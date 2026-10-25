"""Reproduce reviewed price facts; preserve date, bottling, market, tax and source scope."""
import hashlib,json,sys
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from catalog.price_dates import price_bounds,price_label

def apply_prices(T,uid):
    reports=[json.loads((ROOT/'data/prices/archive-research.json').read_text())]
    current=ROOT/'data/prices/current-source-research.json'
    if current.exists():reports.append(json.loads(current.read_text()))
    documents=ROOT/'data/prices/document-research.json'
    if documents.exists():reports.append(json.loads(documents.read_text()))
    launch=ROOT/'data/prices/launch-research.json'
    if launch.exists():reports.append(json.loads(launch.read_text()))
    remaining=ROOT/'data/prices/remaining-gap-research.json'
    if remaining.exists():reports.append(json.loads(remaining.read_text()))
    products={p['slug']:p for p in T['products']};variants={};seen={}
    release_path=ROOT/'data/prices/coverage-research.json'
    releases={r['product']:r.get('first_release_year') or r.get('release_not_before_year') for r in json.loads(release_path.read_text())} if release_path.exists() else {}
    for report in reports:
        for d in report['points']:
            p=products[d['product']];archival=d.get('basis','archive_capture')=='archive_capture';basis='archive_capture' if archival else 'launch_msrp' if d.get('basis')=='launch_msrp' else 'historical_ad' if d.get('basis') in ['archive_document','historical_ad'] else 'wholesale_list' if d.get('basis')=='wholesale_list' else 'retail_offer'
            precision='month' if d.get('date_precision')=='month' else 'day'
            temporal={'observed_on':d.get('observed_on'),'observed_period':d.get('observed_period',''),'date_precision':precision}
            bounds=price_bounds(temporal);date_key=price_label(temporal)
            if archival and precision!='day':raise ValueError('An archive capture requires its actual capture day')
            if releases.get(d['product']) and bounds[0].year<releases[d['product']]:raise ValueError('Price predates the documented expression launch or earliest possible year: '+d['product'])
            abv=format(Decimal(str(d['abv'])).normalize(),'f');volume=int(d['volume_ml'])
            if not 0<Decimal(d['amount'])<1000000 or not 0<Decimal(abv)<=100 or not 1<=volume<=30000:raise ValueError('Invalid reviewed price or format')
            k=d['product']+'/'+str(volume)+'/'+abv
            if d['country']!='United Kingdom':k+='/'+d['country']
            key=(k,date_key,d['retailer'],d['currency'],d['country'])
            if key in seen:
                if Decimal(seen[key]['amount'])!=Decimal(d['amount']) or seen[key].get('tax_included')!=d.get('tax_included'):raise ValueError('Conflicting same-day observation: '+str(key))
                continue
            seen[key]=d
            src_key='sources/archive/'+str(d['retailer_id'])+'/'+d['timestamp'] if archival else 'sources/retail/'+hashlib.sha256(d['source_url'].encode()).hexdigest()[:24]+'/'+date_key+'/'+d['product']
            if archival and d.get('parser')=='drinkshop_primary_price_table':src_key='sources/archive/drinkshop/'+str(d['source_retailer_id'])+'/'+d['timestamp']
            srcid=uid(src_key)
            source_suffix={'archive_capture':'archived retail price','retail_offer':'observed retail offer','launch_msrp':'announced launch recommendation','historical_ad':'published historical price','wholesale_list':'published wholesale price'}[basis]
            prefix={'archive_capture':'Archived retail offer; capture date is not a transaction date. ','retail_offer':'Retail source viewed on retrieval date; availability and price may change. ','launch_msrp':'Manufacturer recommendation documented on the stated source date; not a retail transaction or retrieval-date offer. ','historical_ad':'Price printed in a dated retailer document; not a transaction or retrieval-date offer. ','wholesale_list':'Published wholesale list; a trade price, not a consumer retail offer or transaction. '}[basis]
            T['sources'].append(dict(id=srcid,title=(d['title']+' — '+source_suffix)[:240],url=d['source_url'],publisher=d.get('source_publisher',d['retailer']+(' / Internet Archive' if archival else '')),kind=d.get('source_kind','manufacturer' if basis=='launch_msrp' else 'secondary'),accessed_on=d.get('retrieved_at','2026-10-25')[:10],license_note='Parsed price and bottling facts. Source text and images retain their rights. '+d.get('hash_scope','Source response bytes')+' SHA-256 '+d['content_sha256']+(' '+d['source_crawl_label'] if d.get('source_crawl_label') else '')))
            variant=variants.get(k)
            if not variant:
                variant=dict(id=uid('variants/archive/'+k),product_id=p['id'],name=f"{'Archive' if archival else 'Launch' if basis=='launch_msrp' else 'Wholesale' if basis=='wholesale_list' else 'Retail'} reference · {volume} ml / {abv}%",market='United Kingdom archive' if archival else d['country']+(' launch recommendation' if basis=='launch_msrp' else ' historical advertisement' if basis=='historical_ad' else ' wholesale reference' if basis=='wholesale_list' else ' retail reference'),volume_ml=volume,abv=abv,source_id=srcid,barcode='');T['variants'].append(variant);variants[k]=variant
            price_key='prices/archive/'+k+'/'+date_key
            # Preserve the existing archival identifiers. New current observations include seller/currency identity.
            if not archival or d.get('parser')=='drinkshop_primary_price_table':price_key+='/'+d['retailer']+'/'+d['currency']
            T['price_observations'].append(dict(id=uid(price_key),variant_id=variant['id'],basis=basis,**temporal,amount=d['amount'],currency=d['currency'],country=d['country'],retailer=d['retailer'],source_id=srcid,tax_included=d.get('tax_included'),promotion=d.get('promotion'),notes=prefix+d['date_scope']+' '+d.get('notes','')+(' Manufacturer recommendation; dated '+d.get('date_type','announcement or scheduled release')+'.' if basis=='launch_msrp' else '')+' '+d.get('hash_scope','Source response bytes')+' SHA-256 '+d['content_sha256']))
