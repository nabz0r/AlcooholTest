"""Content-addressed public fact capsules; never a copyrighted-page mirror.

The pure builders also serve the offline CLI. Django and database access are lazy.
Only explicit public fields are copied; accounts and editorial queues are absent.
"""
import hashlib
import http.client
import json
import os
import re
import tempfile
import zipfile
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

SCHEMA_VERSION = '1.0'
PUBLICATION_POLICY_REVISION = 'public-fk-v2'
MAX_ASSET_BYTES = 8 * 1024 * 1024
MAX_CAPSULE_BYTES = 8 * 1024 * 1024
MAX_RESEARCH_BYTES = 32 * 1024 * 1024
MAX_BUNDLE_BYTES = 256 * 1024 * 1024
ASSET_PATH = re.compile(r'^/bottles/[-a-z0-9]+\.(?:jpg|png|webp)$')
DIGEST = re.compile(r'^[a-f0-9]{64}$')
PUBLIC_FIELDS = {
    'sources': 'id title url publisher kind accessed_on license_note',
    'places': 'id slug name region country source_id notes',
    'brands': 'id slug name country website',
    'ingredients': 'id slug name scientific_name family notes plant_part sensory_role preparation technical_notes navigation_group profile_source_id',
    'compounds': 'id slug name cas notes',
    'ingredient_compounds': 'id ingredient_id compound_id source_id notes',
    'products': 'id slug brand_id place_id name category description disclosure status color shape history history_source_id edition_of_id merged_into_id photo_credit photo_license',
    'bottle_assets': 'id product_id local_path source_page author license license_url sha256 edition_note view pair_key barcode',
    'external_photo_references': 'id product_id view source_page image_url publisher credit rights_note edition_note verified_on verified',
    'variants': 'id product_id name market abv volume_ml source_id barcode',
    'recipes': 'id product_id version declared_count process source_id notes',
    'recipe_ingredients': 'id recipe_id ingredient_id source_id certainty stage amount unit notes',
    'studies': 'id title compound_id source_id design population finding limitation beverage_evidence',
    'measurements': 'id variant_id compound_id value unit method batch source_id sampled_on',
    'mechanisms': 'id compound_id target action evidence_context source_id limitation',
    'critic_reviews': 'id product_id critic source_id summary score score_max published_on',
    'price_observations': 'id variant_id observed_on observed_period date_precision amount currency country retailer source_id notes basis promotion tax_included',
    'market_price_indexes': 'id slug product_id source_id title currency territory statistic unit_scope method notes method_source_url fact_sha256 verified',
    'market_price_index_points': 'id index_id period value',
    'product_research': 'id product_id first_release_year release_not_before_year release_source_url notes',
    'approved_photographs': 'id product_id view image_url credit license source_url caption pair_key barcode',
}
URL_FIELDS = {'website', 'source_page', 'image_url', 'release_source_url', 'method_source_url', 'source_url'}
RESEARCH_FILES = [
    'prices/archive-research.json', 'prices/current-source-research.json',
    'prices/launch-research.json', 'prices/document-research.json', 'prices/appleton-predecessor-research.json',
    'prices/additional-launch-research.json', 'prices/coverage-research.json', 'prices/remaining-gap-research.json',
    'prices/market-indexes/kakubin.json', 'assets.json',
    'photography/external-references.json',
]
NOTICE = ('A Memento preserves the public catalogue facts, editorial summaries and provenance known at capture time. '
          'It does not copy complete source articles or prove their contents independently. Original pages and external '
          'photographs retain their rights. Raw research caches, accounts, private collections and moderation queues are excluded.')


def _encode(value):
    if isinstance(value, (date, datetime, Decimal, UUID)):
        return str(value) if isinstance(value, (Decimal, UUID)) else value.isoformat()
    raise TypeError(type(value).__name__)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=_encode).encode('utf-8')


def sha256(value):
    return hashlib.sha256(value).hexdigest()


def public_url(value):
    """URLs are stored as references only. None becomes a network destination."""
    if not isinstance(value, str) or len(value) > 2000 or any(ord(c) < 32 for c in value):
        return None
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password:
            return None
        return value
    except ValueError:
        return None


def public_document(document):
    tables = document.get('tables', {})
    clean = {key: [{f: row[f] for f in fields.split() if f in row} for row in tables.get(key, [])]
             for key, fields in PUBLIC_FIELDS.items()}
    products = {str(r['id']) for r in clean['products'] if r.get('status') == 'published'}
    clean['products'] = [r for r in clean['products'] if str(r['id']) in products]
    for key in ('variants', 'recipes', 'bottle_assets', 'critic_reviews', 'product_research', 'approved_photographs'):
        clean[key] = [r for r in clean[key] if str(r.get('product_id')) in products]
    clean['external_photo_references'] = [r for r in clean['external_photo_references'] if str(r.get('product_id')) in products and r.get('verified')]
    clean['market_price_indexes'] = [r for r in clean['market_price_indexes'] if str(r.get('product_id')) in products and r.get('verified')]
    variants = {str(r['id']) for r in clean['variants']}
    recipes = {str(r['id']) for r in clean['recipes']}
    indexes = {str(r['id']) for r in clean['market_price_indexes']}
    for key in ('price_observations', 'measurements'):
        clean[key] = [r for r in clean[key] if str(r.get('variant_id')) in variants]
    clean['recipe_ingredients'] = [r for r in clean['recipe_ingredients'] if str(r.get('recipe_id')) in recipes]
    clean['market_price_index_points'] = [r for r in clean['market_price_index_points'] if str(r.get('index_id')) in indexes]
    brand_ids = {str(r.get('brand_id')) for r in clean['products']}
    place_ids = {str(r.get('place_id')) for r in clean['products']}
    clean['brands'] = [r for r in clean['brands'] if str(r['id']) in brand_ids]
    clean['places'] = [r for r in clean['places'] if str(r['id']) in place_ids]
    source_ids = {str(row[field]) for key, rows in clean.items() if key != 'sources'
                  for row in rows for field in ('source_id', 'history_source_id', 'profile_source_id') if row.get(field)}
    # URL equality is not publication authority for a Source row's metadata.
    # Public URL-only references get their own capsule without adopting an orphan Source.
    clean['sources'] = [r for r in clean['sources'] if str(r['id']) in source_ids]
    return json.loads(canonical({'tables': clean}))


def catalog_document():
    from . import models as m
    from .interchange import TABLES, rows_for
    tables = {key: list(rows_for(key, model)) for key, model in TABLES.items() if key in PUBLIC_FIELDS}
    tables['product_research'] = list(m.ProductResearch.objects.filter(product__status='published').values(*PUBLIC_FIELDS['product_research'].split()))
    tables['approved_photographs'] = [
        {'id': str(photo.pk), 'product_id': str(photo.product_id), 'view': photo.view,
         'image_url': photo.photo.url, 'credit': photo.credit, 'license': photo.license,
         'source_url': photo.source_url, 'caption': photo.caption, 'pair_key': photo.pair_key, 'barcode': photo.barcode}
        for photo in m.BottlePhoto.objects.filter(approved=True, product__status='published')]
    return {'tables': tables}


def load_research_documents(root):
    """Read only fixed public fact-report paths. Never inspect private page caches."""
    root = Path(root).resolve()
    found = []
    for relative in RESEARCH_FILES:
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size > MAX_RESEARCH_BYTES:
            continue
        data = json.loads(path.read_text())
        found.append((relative, data))
    return found


def _proofs(research_documents, public_products):
    proofs = defaultdict(list)
    for name, document in research_documents:
        rows = document if isinstance(document, list) else document.get('points', []) + document.get('indexes', []) + (document.get('products', []) if name == 'prices/additional-launch-research.json' else [])
        for row in rows:
            if not isinstance(row, dict):
                continue
            product_slug = row.get('product') or row.get('product_slug')
            if product_slug and product_slug not in public_products:
                continue
            url = public_url(row.get('source_url') or row.get('source_page'))
            if not url:
                continue
            retrieval = row.get('source_retrieval') if isinstance(row.get('source_retrieval'), dict) else {}
            digest = row.get('content_sha256') or retrieval.get('sha256')
            scope = row.get('hash_scope') or retrieval.get('hash_scope')
            raw_capture = name in ('prices/archive-research.json', 'prices/appleton-predecessor-research.json') and DIGEST.fullmatch(str(digest or ''))
            raw_document = (name in ('prices/document-research.json', 'prices/remaining-gap-research.json')
                            and str(scope or '').startswith('Complete original') and 'PDF' in str(scope)
                            and 'bytes' in str(scope) and DIGEST.fullmatch(str(digest or '')))
            if raw_capture:
                scope = 'SHA-256 of decoded and decompressed raw archived HTML capture bytes; bytes retained privately, not copied into this capsule.'
            raw_verified_research = (name == 'prices/additional-launch-research.json' and retrieval.get('http_status') == 200
                                     and str(scope or '').startswith('Downloaded raw') and DIGEST.fullmatch(str(digest or '')))
            proof = {key: row[key] for key in ('original_url', 'retrieved_at', 'retrieved_on', 'observed_on', 'date_scope', 'date_precision', 'evidence_facts') if key in row}
            proof.update({'report': name, 'content_sha256': digest if DIGEST.fullmatch(str(digest or '')) else None,
                          'hash_scope': scope or 'No original-content hash scope established by this report.',
                          'original_content_sha256': digest if raw_capture or raw_document or raw_verified_research else None,
                          'original_content_copied': False})
            if retrieval.get('checked_on'):
                proof['retrieved_on'] = retrieval['checked_on']
            # A local asset hash identifies hosted image bytes, never its full-resolution source page.
            if name == 'assets.json':
                proof.update({'local_asset_sha256': row.get('sha256'), 'local_path': row.get('file'),
                              'hash_scope': 'SHA-256 of the locally hosted licensed image file; not the source page or an unavailable full-resolution original.'})
            if proof not in proofs[url]:
                proofs[url].append(proof)
    return proofs


def build_capsules(document, research_documents=()):
    tables = public_document(document)['tables']
    products = {str(r['id']): r for r in tables['products']}
    context = defaultdict(set)
    for ident, row in products.items():
        context[('products', ident)].add(row['slug'])
        for key, field in [('brands', 'brand_id'), ('places', 'place_id')]:
            if row.get(field):
                context[(key, str(row[field]))].add(row['slug'])
    for key in ('variants', 'recipes', 'bottle_assets', 'external_photo_references', 'critic_reviews', 'market_price_indexes', 'product_research', 'approved_photographs'):
        for row in tables[key]:
            product = products.get(str(row.get('product_id')))
            if product:
                context[(key, str(row['id']))].add(product['slug'])
    for key, foreign_key, parent in [('price_observations', 'variant_id', 'variants'), ('measurements', 'variant_id', 'variants'),
                                     ('recipe_ingredients', 'recipe_id', 'recipes'), ('market_price_index_points', 'index_id', 'market_price_indexes')]:
        for row in tables[key]:
            context[(key, str(row['id']))] |= context[(parent, str(row.get(foreign_key)))]
            if key == 'recipe_ingredients':
                context[('ingredients', str(row.get('ingredient_id')))] |= context[(key, str(row['id']))]
    for row in tables['ingredient_compounds']:
        context[('ingredient_compounds', str(row['id']))] |= context[('ingredients', str(row.get('ingredient_id')))]
        context[('compounds', str(row.get('compound_id')))] |= context[('ingredient_compounds', str(row['id']))]
    for key in ('studies', 'mechanisms'):
        for row in tables[key]:
            context[(key, str(row['id']))] |= context[('compounds', str(row.get('compound_id')))]
    source_proofs = _proofs(research_documents, {p['slug'] for p in products.values()})
    capsules = {}
    by_url = {}
    for source in sorted(tables['sources'], key=lambda r: str(r['id'])):
        key = 'source:' + str(source['id'])
        url = public_url(source.get('url'))
        metadata = {field: source.get(field) for field in ('id', 'title', 'publisher', 'kind', 'accessed_on', 'license_note')}
        metadata['original_url'] = url
        capsules[key] = {'source_key': key, 'kind': 'source', 'status': 'fact_extract_only', 'source': metadata, 'records': [], 'products': set()}
        if url:
            by_url.setdefault(url, key)

    def reference(url, title, kind='reference', accessed_on=None):
        url = public_url(url)
        if not url:
            return None
        if url in by_url:
            return by_url[url]
        key = 'reference:' + sha256(url.encode())
        by_url[url] = key
        capsules[key] = {'source_key': key, 'kind': kind, 'status': 'external_link_only',
                         'source': {'original_url': url, 'title': title, 'publisher': urlsplit(url).hostname,
                                    'accessed_on': accessed_on, 'license_note': 'External reference only; original content not copied.'},
                         'records': [], 'products': set()}
        return key

    for table, rows in tables.items():
        if table == 'sources':
            continue
        for row in sorted(rows, key=lambda r: str(r['id'])):
            record_products = sorted(context[(table, str(row['id']))])
            fact = {'table': table, 'record_id': str(row['id']), 'fields': row,
                    'context': {'products': record_products, 'record_scope': 'Public catalogue editorial record; not a verbatim original-page copy.'}}
            keys = set()
            for field in ('source_id', 'history_source_id', 'profile_source_id'):
                key = 'source:' + str(row.get(field))
                if row.get(field) and key in capsules:
                    keys.add(key)
            for field in URL_FIELDS:
                if row.get(field):
                    key = reference(row[field], row.get('title') or row.get('name') or table.replace('_', ' ').title(),
                                    accessed_on=row.get('verified_on'))
                    if key:
                        keys.add(key)
            if table == 'bottle_assets':
                key = 'asset:' + str(row['id'])
                asset_product = products.get(str(row.get('product_id')), {})
                asset_brand = next((b.get('name', '') for b in tables['brands'] if str(b['id']) == str(asset_product.get('brand_id'))), '')
                asset_view = {'front':'Front photograph','back':'Rear label photograph','detail':'Detail photograph'}.get(row.get('view'), 'Reference photograph')
                asset_title = ' · '.join(value for value in (asset_brand, asset_product.get('name', 'Bottle'), asset_view) if value)
                capsules[key] = {'source_key': key, 'kind': 'licensed_asset', 'status': 'licensed_local_asset',
                                 'source': {'original_url': public_url(row.get('source_page')),
                                            'title': asset_title,
                                            'publisher': row.get('author'), 'accessed_on': None,
                                            'license_note': row.get('license'), 'license_url': public_url(row.get('license_url'))},
                                 'local_asset': {'path': row.get('local_path'), 'sha256': row.get('sha256'),
                                                 'hash_scope': 'Locally hosted image bytes; not the source page.', 'license': row.get('license'),
                                                 'license_url': row.get('license_url'), 'credit': row.get('author'),
                                                 'source_url': row.get('source_page'), 'modification_note': row.get('edition_note')},
                                 'records': [], 'products': set()}
                keys.add(key)
            if table == 'external_photo_references':
                key = 'photo-reference:' + str(row['id'])
                capsules[key] = {'source_key': key, 'kind': 'external_photo_reference', 'status': 'external_link_only',
                                 'source': {'original_url': public_url(row.get('source_page')), 'image_url': public_url(row.get('image_url')),
                                            'title': row.get('edition_note'), 'publisher': row.get('publisher'),
                                            'accessed_on': row.get('verified_on'), 'license_note': row.get('rights_note')},
                                 'records': [], 'products': set()}
                keys.add(key)
            if not keys:
                # Retain unsourced public editorial data without inventing a source URL.
                key = 'catalogue:' + table
                capsules.setdefault(key, {'source_key': key, 'kind': 'catalogue_context', 'status': 'fact_extract_only',
                                           'source': {'original_url': None, 'title': table.replace('_', ' ').title(),
                                                      'publisher': 'AlcoolTest catalogue', 'accessed_on': None,
                                                      'license_note': 'Project editorial data; no original source assigned to this record.'},
                                           'records': [], 'products': set()})
                keys.add(key)
            for key in sorted(keys):
                capsules[key]['records'].append(fact)
                capsules[key]['products'].update(record_products)
    # Explicit public research reports add source-linked limits and identity facts that
    # may not have a Source foreign key yet. Never sweep arbitrary files or raw caches.
    canonical_products = {p['slug']: p for p in products.values() if not p.get('edition_of_id') and not p.get('merged_into_id')}
    chronology_fields = set(('product first_release_year release_not_before_year release_period release_source_url source_url publisher source_kind exact_claim_scope notes reviewed_on published_on pdf_page printed_page name_introduced_year name_introduced_period historical_alias alias_same_liquid_explicit_owner_confirmation twenty_year_eligibility_as_of_2026_10_25').split())
    reference_fields = set(('source_url publisher source_kind published_on claim_scope notes').split())
    for report_name, report in research_documents:
        rows = []
        if report_name == 'prices/additional-launch-research.json':
            rows = [('research_chronology', row) for row in report.get('products', [])]
            rows += [('research_price_lead', row) for row in report.get('price_leads', [])]
        elif report_name == 'prices/coverage-research.json':
            rows = [('research_chronology', row) for row in report if isinstance(row, dict)]
        elif report_name == 'prices/appleton-predecessor-research.json' and report.get('mapping'):
            rows = [('research_expression_identity', report['mapping'])]
        elif report_name == 'prices/remaining-gap-research.json':
            rows = [('research_price_document', row) for row in report.get('points', [])]
            rows += [('research_gap_check', row) for row in report.get('gaps', [])]
        for table, row in rows:
            slug = row.get('product')
            if slug not in canonical_products:
                continue
            fields = {k: row[k] for k in chronology_fields if k in row}
            if table == 'research_price_lead':
                fields.update({k: row[k] for k in ('amount','currency','volume_ml','abv_as_published','country','basis','price_label','tax_included','promotion','status','claim_scope') if k in row})
            if table == 'research_price_document':
                fields.update({k:row[k] for k in ('observed_on','observed_period','date_precision','amount','currency','country','retailer','volume_ml','abv','printed_us_proof','price_label','basis','tax_included','date_scope','proof_conversion_source') if k in row})
            if table == 'research_gap_check':
                fields.update({k:row[k] for k in ('status','older_retail_gap_resolved','summary') if k in row})
            if table == 'research_expression_identity':
                fields.update({k: row[k] for k in ('historical_alias','verification','verified_on','identity_sources') if k in row})
            primary_url = row.get('source_url') or row.get('release_source_url')
            references = [(primary_url, fields, row.get('publisher'), row.get('reviewed_on'))] if public_url(primary_url) else []
            for extra in row.get('additional_sources', []):
                if isinstance(extra, dict) and public_url(extra.get('source_url')):
                    references.append((extra['source_url'], {k:extra[k] for k in reference_fields if k in extra}, extra.get('publisher'), None))
            for checked in row.get('checked_sources', []):
                if public_url(checked.get('source_url')):
                    references.append((checked['source_url'], {**fields,'source_url':checked['source_url'],'checked_result':checked.get('result'),'acceptance_scope':'Research check only; not an accepted price observation.'}, None, None))
            if public_url(row.get('proof_conversion_source')):
                references.append((row['proof_conversion_source'], {'product':slug,'claim_scope':'U.S. proof to ABV conversion reference for the cited price document; not a beverage-specific study.','primary_document_url':primary_url}, 'U.S. Alcohol and Tobacco Tax and Trade Bureau', None))
            for identity_url in row.get('identity_sources', []):
                if public_url(identity_url):
                    references.append((identity_url, fields, None, row.get('verified_on')))
            if not references:
                references = [(None, fields, 'AlcoolTest research notebook', None)]
            for url, source_fields, publisher, accessed_on in references:
                key = reference(url, canonical_products[slug]['name'] + ' · research reference', 'research_reference', accessed_on)
                if not key:
                    key = 'catalogue:research_chronology'
                    capsules.setdefault(key, {'source_key': key, 'kind': 'catalogue_context', 'status': 'fact_extract_only',
                                              'source': {'original_url': None, 'title': 'Research chronology and documented gaps',
                                                         'publisher': 'AlcoolTest research notebook', 'accessed_on': None,
                                                         'license_note': 'Original editorial research scope; no original page assigned.'},
                                              'records': [], 'products': set()})
                if publisher and capsules[key]['kind'] == 'research_reference':
                    capsules[key]['source']['publisher'] = publisher
                fact_fields = {**source_fields, 'product': slug, 'report': report_name}
                record_id = sha256(canonical({'report': report_name, 'table': table, 'product': slug, 'url': url, 'fields': fact_fields}))
                capsules[key]['records'].append({'table': table, 'record_id': record_id, 'fields': fact_fields,
                                                'context': {'products': [slug], 'record_scope': 'Source-linked editorial research facts and limits. A research price lead is not an accepted shop offer or transaction.'}})
                capsules[key]['products'].add(slug)
    output = []
    for key in sorted(capsules):
        capsule = capsules[key]
        url = capsule['source'].get('original_url')
        capsule['schema_version'] = SCHEMA_VERSION
        capsule['original_content_status'] = 'not_copied'
        capsule['source_proofs'] = source_proofs.get(url, [])
        if not capsule['source'].get('accessed_on'):
            known_dates = [str(proof.get('retrieved_on') or proof.get('retrieved_at') or '')[:10]
                           for proof in capsule['source_proofs']]
            known_dates = [value for value in known_dates if re.fullmatch(r'\d{4}-\d{2}-\d{2}', value)]
            if known_dates:
                capsule['source']['accessed_on'] = max(known_dates)
                capsule['source']['access_date_scope'] = 'Recorded report retrieval date, not a new source visit during this local snapshot.'
        capsule['original_content_hashes'] = sorted({proof['original_content_sha256'] for proof in capsule['source_proofs'] if proof.get('original_content_sha256')})
        capsule['products'] = sorted(capsule['products'])
        capsule['records'].sort(key=lambda r: (r['table'], r['record_id']))
        capsule['record_count'] = len(capsule['records'])
        capsule['notice'] = NOTICE
        capsule['snapshot_sha256'] = sha256(canonical(capsule))
        output.append(capsule)
    return output


def verify_capsule(capsule):
    payload = dict(capsule)
    digest = payload.pop('snapshot_sha256', '')
    return bool(DIGEST.fullmatch(str(digest))) and sha256(canonical(payload)) == digest


def _immutable_file(path, data):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.capsule-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
        try:
            os.link(temporary, path)  # Atomic publication without replacement, even across workers.
        except FileExistsError:
            if path.read_bytes() != data:
                raise ValueError('Existing immutable Memento file differs from its content address.')
    finally:
        Path(temporary).unlink(missing_ok=True)


def persist_snapshot(capsules, root, captured_at=None, publication_state_sha256=None):
    root = Path(root)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    captured_at = captured_at or datetime.now(timezone.utc).isoformat()
    entries = []
    for capsule in capsules:
        if not verify_capsule(capsule):
            raise ValueError('Invalid fact-capsule SHA-256.')
        digest = capsule['snapshot_sha256']
        data = canonical(capsule) + b'\n'
        if len(data) > MAX_CAPSULE_BYTES:
            raise ValueError('A Memento capsule exceeds the bounded artifact size.')
        _immutable_file(root / 'capsules' / (digest + '.json'), data)
        source = capsule['source']
        entries.append({'sha256': digest, 'source_key': capsule['source_key'], 'kind': capsule['kind'],
                        'status': capsule['status'], 'title': source.get('title') or 'Untitled source',
                        'publisher': source.get('publisher') or '', 'original_url': source.get('original_url'),
                        'accessed_on': source.get('accessed_on'), 'record_count': capsule['record_count'],
                        'products': capsule['products'], 'source_content_hash_known': bool(capsule['original_content_hashes']),
                        'local_asset': capsule.get('local_asset'), 'url': '/api/v1/memento/capsules/' + digest})
    counts = defaultdict(int)
    for entry in entries:
        counts[entry['kind']] += 1
    manifest = {'schema_version': SCHEMA_VERSION, 'captured_at': captured_at, 'notice': NOTICE,
                'original_pages_copied': 0, 'counts': dict(counts), 'capsules': len(entries), 'items': entries,
                'publication_state_sha256': publication_state_sha256}
    digest = sha256(canonical(manifest))
    manifest['snapshot_sha256'] = digest
    data = canonical(manifest) + b'\n'
    _immutable_file(root / 'snapshots' / (digest + '.json'), data)
    descriptor, name = tempfile.mkstemp(prefix='.memento-', dir=root)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
        os.replace(name, root / 'index.json')
    finally:
        Path(name).unlink(missing_ok=True)
    return manifest


def snapshot_root():
    from django.conf import settings
    return Path(getattr(settings, 'MEMENTO_ROOT', settings.EXPORT_ROOT / 'memento'))


def _publication_fingerprint(membership):
    # Publication policy changes must invalidate artifacts from older app versions,
    # even when every public object ID remains unchanged.
    return sha256(canonical({'policy_revision': PUBLICATION_POLICY_REVISION, 'membership': membership}))


def document_publication_state(document):
    tables = public_document(document)['tables']
    return _publication_fingerprint({key: sorted(str(r['id']) for r in tables[key]) for key in
                                     ('products', 'bottle_assets', 'approved_photographs', 'external_photo_references', 'market_price_indexes')})


def current_publication_state():
    from . import models as m
    queries = {'products': m.Product.objects.filter(status='published'),
               'bottle_assets': m.BottleAsset.objects.filter(product__status='published'),
               'approved_photographs': m.BottlePhoto.objects.filter(approved=True, product__status='published'),
               'external_photo_references': m.ExternalPhotoReference.objects.filter(verified=True, product__status='published'),
               'market_price_indexes': m.MarketPriceIndex.objects.filter(verified=True, product__status='published')}
    return _publication_fingerprint({key: sorted(str(pk) for pk in qs.values_list('pk', flat=True)) for key, qs in queries.items()})


def refresh_snapshot():
    from django.conf import settings
    reports = load_research_documents(Path(settings.SEED_FILE).parent.parent)
    document = catalog_document()
    return persist_snapshot(build_capsules(document, reports), snapshot_root(),
                            publication_state_sha256=document_publication_state(document))


def latest_snapshot():
    path = snapshot_root() / 'index.json'
    manifest = json.loads(path.read_text()) if path.is_file() else None
    # A withdrawn product, image approval or verified series cannot remain public through a stale artifact.
    if manifest is None or manifest.get('publication_state_sha256') != current_publication_state():
        manifest = refresh_snapshot()
    return manifest


def licensed_asset(asset):
    path, digest = asset.get('path', ''), asset.get('sha256', '')
    if not ASSET_PATH.fullmatch(path) or not DIGEST.fullmatch(digest):
        return False
    license_name = asset.get('license', '').strip()
    parsed = urlsplit(asset.get('license_url', ''))
    cc = parsed.hostname in ('creativecommons.org', 'www.creativecommons.org') and (
        parsed.path.startswith('/licenses/by/') or parsed.path.startswith('/licenses/by-sa/') or parsed.path.startswith('/publicdomain/zero/'))
    public_domain = license_name == 'Public domain' and parsed.hostname == 'commons.wikimedia.org' and parsed.path.startswith('/wiki/File:')
    return bool((cc and (license_name.startswith('CC BY') or license_name == 'CC0')) or public_domain)


def local_asset_bytes(asset, assets_root=None):
    if not licensed_asset(asset):
        raise ValueError('Only a reviewed, licensed local bottle file can enter the bundle.')
    path = asset['path']
    if assets_root is not None:
        root = Path(assets_root).resolve()
        file = (root / path.lstrip('/')).resolve()
        if not file.is_relative_to(root) or not file.is_file() or file.stat().st_size > MAX_ASSET_BYTES:
            raise ValueError('Licensed asset missing, outside the fixed root, or too large.')
        data = file.read_bytes()
    else:
        # Fixed service and port; no Source URL, redirect, header or hostname is accepted.
        connection = http.client.HTTPConnection('web', 8080, timeout=8)
        try:
            connection.request('GET', path, headers={'Accept': 'image/jpeg,image/png,image/webp'})
            response = connection.getresponse()
            if response.status != 200:
                raise ValueError('The fixed local media service did not return the licensed file.')
            length = response.getheader('Content-Length')
            if length and int(length) > MAX_ASSET_BYTES:
                raise ValueError('Licensed local media exceeds 8 MiB.')
            data = response.read(MAX_ASSET_BYTES + 1)
        finally:
            connection.close()
    if len(data) > MAX_ASSET_BYTES or sha256(data) != asset['sha256']:
        raise ValueError('Licensed local media failed its expected SHA-256 or size check.')
    return data


def write_bundle(path, manifest, root, assets_root=None, include_assets=True):
    """Fail the bundle on missing/hash-mismatched required media; never publish a partial ZIP."""
    root = Path(root)
    entries = manifest['items']
    media, size = {}, 0
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr('index.json', canonical(manifest) + b'\n')
        archive.writestr('README.txt', NOTICE + '\n\nVerify each capsule by removing snapshot_sha256, encoding canonical UTF-8 JSON with sorted keys and compact separators, and comparing SHA-256. Source hashes have their own explicit scope.\n\nLocal licensed media is included only when the bundle manifest says so. External references remain links. No complete source articles or private raw HTML caches are included.\n')
        for item in entries:
            digest = item['sha256']
            if not DIGEST.fullmatch(digest):
                raise ValueError('Invalid capsule identity.')
            data = (root / 'capsules' / (digest + '.json')).read_bytes()
            capsule = json.loads(data)
            if not verify_capsule(capsule):
                raise ValueError('Stored fact capsule failed integrity validation.')
            archive.writestr('capsules/' + digest + '.json', data)
            asset = item.get('local_asset')
            if include_assets and asset and asset['path'] not in media:
                data = local_asset_bytes(asset, assets_root)
                size += len(data)
                if size > MAX_BUNDLE_BYTES:
                    raise ValueError('Licensed media bundle exceeds 256 MiB.')
                media[asset['path']] = {'sha256': sha256(data), 'bytes': len(data), **asset}
                archive.writestr('media/' + asset['path'].lstrip('/'), data)
        bundle = {'schema_version': SCHEMA_VERSION, 'snapshot_sha256': manifest['snapshot_sha256'],
                  'media_included': include_assets, 'licensed_media_files': len(media), 'licensed_media_bytes': size,
                  'original_source_pages_copied': 0, 'external_reference_files_copied': 0,
                  'files': list(media.values()), 'notice': NOTICE}
        archive.writestr('licenses/media-manifest.json', canonical(bundle) + b'\n')
    return bundle


def memento_to_file(path):
    manifest = refresh_snapshot()
    return write_bundle(path, manifest, snapshot_root())


def _json(data, status=200):
    from django.http import JsonResponse
    return JsonResponse(data, status=status, json_dumps_params={'default': _encode})


def memento_index(request):
    if request.method != 'GET':
        return _json({'error': 'GET required.'}, 405)
    try:
        limit = max(1, min(60, int(request.GET.get('limit', '24'))))
        offset = max(0, min(100000, int(request.GET.get('offset', '0'))))
    except ValueError:
        return _json({'error': 'Use integer pagination values.'}, 400)
    q = request.GET.get('q', '').strip().casefold()[:120]
    product = request.GET.get('product', '')[:100]
    kind = request.GET.get('kind', '')[:40]
    manifest = latest_snapshot()
    items = [item for item in manifest['items'] if (not product or product in item['products']) and (not kind or item['kind'] == kind)
             and (not q or q in ' '.join(str(item.get(k) or '') for k in ('title', 'publisher', 'original_url', 'source_key')).casefold())]
    return _json({key: manifest[key] for key in ('schema_version', 'captured_at', 'notice', 'original_pages_copied', 'counts', 'capsules', 'snapshot_sha256')}
                 | {'total': len(items), 'items': items[offset:offset + limit], 'next': offset + limit if len(items) > offset + limit else None})


def memento_capsule(request, digest):
    from django.http import Http404, HttpResponse, HttpResponseNotModified
    if request.method != 'GET':
        return _json({'error': 'GET required.'}, 405)
    if not DIGEST.fullmatch(str(digest)) or not any(item['sha256'] == digest for item in latest_snapshot()['items']):
        raise Http404
    data = (snapshot_root() / 'capsules' / (digest + '.json')).read_bytes()
    if len(data) > MAX_CAPSULE_BYTES or not verify_capsule(json.loads(data)):
        return _json({'error': 'Capsule integrity check failed.'}, 503)
    etag = '"' + digest + '"'
    if request.headers.get('If-None-Match') == etag:
        return HttpResponseNotModified(headers={'ETag': etag})
    response = HttpResponse(data, content_type='application/json; charset=utf-8')
    response['ETag'] = etag
    response['Content-Disposition'] = 'attachment; filename="memento-' + digest[:16] + '.json"'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


def staff_memento(request, source_id=None):
    from django.views.decorators.csrf import csrf_protect
    return csrf_protect(_staff_memento)(request, source_id)


def _staff_memento(request, source_id=None):
    from django.contrib import admin, messages
    from django.core.exceptions import PermissionDenied
    from django.db import transaction
    from django.shortcuts import redirect
    from django.template.response import TemplateResponse
    from . import models as m
    if not request.user.is_active or not request.user.is_staff or not request.user.has_perm('catalog.view_source'):
        raise PermissionDenied
    if request.method == 'POST':
        if not request.user.has_perm('catalog.add_job'):
            raise PermissionDenied
        if request.POST.get('action') != 'regenerate':
            return _json({'error': 'Unknown Memento action.'}, 400)
        with transaction.atomic():
            job = m.Job.objects.filter(kind='memento', status__in=['queued', 'running']).first()
            if not job:
                job = m.Job.objects.create(kind='memento', created_by=request.user)
                m.Audit.objects.create(actor=request.user, action='memento.queued', target=str(job.pk), detail={'scope': 'public facts and licensed hosted media'})
        messages.success(request, 'Memento bundle queued. Public facts are captured; licensed files must pass their SHA-256 before the ZIP can finish.')
        return redirect(request.path)
    if request.method != 'GET':
        return _json({'error': 'GET or POST required.'}, 405)
    manifest = latest_snapshot()
    selected = [item for item in manifest['items'] if not source_id or item['source_key'] == 'source:' + str(source_id)]
    q = request.GET.get('q', '').strip()[:120]
    if q:
        selected = [item for item in selected if q.casefold() in (item['title'] + ' ' + item['publisher'] + ' ' + str(item['original_url'] or '')).casefold()]
    return TemplateResponse(request, 'admin/source_memento.html', {
        **admin.site.each_context(request), 'title': 'Source Memento', 'manifest': manifest,
        'items': selected[:60], 'matched': len(selected), 'query': q,
        'can_queue': request.user.has_perm('catalog.add_job'),
        'jobs': m.Job.objects.filter(kind='memento').order_by('-created_at')[:8],
    })
