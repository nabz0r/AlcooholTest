"""Normalize reviewed monthly survey series without creating bottlings or offers."""
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def apply_market_indexes(tables,uid,directory=None):
    directory=Path(directory) if directory else ROOT/'data/prices/market-indexes'
    tables.setdefault('market_price_indexes',[])
    tables.setdefault('market_price_index_points',[])
    products={row['slug']:row for row in tables['products']}
    seen=set()
    for path in sorted(directory.glob('*.json')):
        document=json.loads(path.read_text())
        for series in document['indexes']:
            key=series['series_key']
            if key in seen:raise ValueError('Duplicate market index series: '+key)
            seen.add(key)
            product=products[series['product']]
            points=series['points']
            facts=[{'period':row['period'],'value':row['value']} for row in points]
            if facts!=series['evidence_facts']:raise ValueError('Index points differ from the reviewed source fact extraction')
            digest=hashlib.sha256(json.dumps(facts,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
            if digest!=series['content_sha256']:raise ValueError('Market index extraction hash mismatch')
            periods=set()
            for row in points:
                if not re.fullmatch(r'[12]\d{3}-(0[1-9]|1[0-2])',row['period']):raise ValueError('Invalid monthly index period')
                if row['period'] in periods:raise ValueError('Duplicate monthly index period')
                periods.add(row['period'])
                number=Decimal(row['value'])
                if not number.is_finite() or not 0<number<1000000000:raise ValueError('Invalid monthly index value')
            if len(points)!=series['point_count']:raise ValueError('Market index point count differs from reviewed manifest')
            source_id=uid('sources/market-index/'+key)
            tables['sources'].append(dict(id=source_id,title=series['title']+' — monthly survey statistic',url=series['source_url'],publisher=series['publisher'],kind='secondary',accessed_on=series['retrieved_at'][:10],license_note=series['license_note']+' '+series['attribution']+' '+series['hash_scope']+' SHA-256 '+digest))
            specification_notes=[]
            for spec in series.get('specifications',[]):
                specification_notes.append(f"{spec['from_period']}–{spec['to_period']}: {spec['survey_brand']}, {spec['volume_ml']} ml, {spec['abv_min_inclusive']}% ≤ ABV < {spec['abv_max_exclusive']}%.")
            index_id=uid('market_price_indexes/'+key)
            slug=re.sub(r'[^a-z0-9]+','-',key.lower()).strip('-')
            tax='tax included' if series.get('tax_included') is True else 'tax excluded' if series.get('tax_included') is False else 'tax treatment unspecified'
            tables['market_price_indexes'].append(dict(id=index_id,slug=slug,product_id=product['id'],source_id=source_id,title=series['title'],currency=series['currency'],territory={'JP':'Japan'}.get(series['country'],series['country']),statistic=series['statistic'].replace('_',' '),unit_scope=series['unit']+'; '+tax+'; survey specification changes documented below',method=series['method']+' '+series['extraction_details']+' Survey specifications: '+' '.join(specification_notes),notes=series['notes']+' '+series['attribution'],method_source_url=series['dataset_url'],fact_sha256=digest,verified=series.get('verified') is True))
            for row in sorted(points,key=lambda row:row['period']):
                tables['market_price_index_points'].append(dict(id=uid('market_price_index_points/'+key+'/'+row['period']),index_id=index_id,period=row['period'],value=row['value']))

