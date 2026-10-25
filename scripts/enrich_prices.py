"""Reproduce reviewed archival observations from explicit parsed price facts."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def apply_prices(T,uid):
    report=json.loads((ROOT/'data/prices/archive-research.json').read_text())
    products={p['slug']:p for p in T['products']};variants={}
    for d in report['points']:
        p=products[d['product']];srcid=uid('sources/archive/'+str(d['retailer_id'])+'/'+d['timestamp'])
        T['sources'].append(dict(id=srcid,title=(d['title']+' — archived retail price')[:240],url=d['source_url'],publisher='The Whisky Exchange / Internet Archive',kind='secondary',accessed_on='2026-10-25',license_note='Parsed price and bottling facts. Source text and images retain their rights. Content SHA-256 '+d['content_sha256']))
        k=d['product']+'/'+str(d['volume_ml'])+'/'+d['abv'];variant=variants.get(k)
        if not variant:
            variant=dict(id=uid('variants/archive/'+k),product_id=p['id'],name=f"Archive reference · {d['volume_ml']} ml / {d['abv']}%",market='United Kingdom archive',volume_ml=d['volume_ml'],abv=d['abv'],source_id=srcid,barcode='');T['variants'].append(variant);variants[k]=variant
        T['price_observations'].append(dict(id=uid('prices/archive/'+k+'/'+d['observed_on']),variant_id=variant['id'],observed_on=d['observed_on'],amount=d['amount'],currency=d['currency'],country=d['country'],retailer=d['retailer'],source_id=srcid,tax_included=True,promotion=False,notes='Archived retail offer; capture date is not a transaction date. Packaging and liquid may change across years. '+d['date_scope']+' Content SHA-256 '+d['content_sha256']))
