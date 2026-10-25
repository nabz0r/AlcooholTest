#!/usr/bin/env python3
"""Accept explicitly reviewed candidate facts without overwriting conflicting historical records."""
import argparse,json,hashlib
from datetime import date
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--accept-reviewed',action='store_true',help='Write the reviewed archival distribution after provenance/conflict checks.');args=p.parse_args()
base=ROOT/'data/prices/archive-research.json';old=json.loads(base.read_text());incoming=json.loads((ROOT/'data/prices/archive-expansion.json').read_text())
releases={r['product']:r.get('first_release_year') or r.get('release_not_before_year') for r in json.loads((ROOT/'data/prices/coverage-research.json').read_text())}
accepted={};held=list(incoming.get('review_candidates',[]));duplicates=0
held_sources={(r['product'],r['source_url']) for r in held if r.get('product') and r.get('source_url')}
for point in old['points']+incoming['points']+json.loads((ROOT/'data/prices/appleton-predecessor-research.json').read_text())['points']:
    if (point['product'],point['source_url']) in held_sources:continue
    if point['product'] not in releases:raise ValueError('Unknown canonical product')
    if releases[point['product']] and int(point['observed_on'][:4])<releases[point['product']]:held.append({'reason':'Before sourced expression launch or earliest possible year','point':point});continue
    if point.get('editorial_status') in ['needs_review','review_required'] or point.get('review_required'):held.append({'reason':'Flagged source anomaly','point':point});continue
    if not point['source_url'].startswith('https://web.archive.org/web/') or len(point['content_sha256'])!=64:raise ValueError('Unrecognized archive provenance')
    date.fromisoformat(point['observed_on'])
    key=(point['product'],point['observed_on'],int(point['volume_ml']),str(Decimal(str(point['abv'])).normalize()),point['currency'],point['country'],point['retailer'])
    if key in accepted:
        prior=accepted[key]
        if Decimal(prior['amount'])!=Decimal(point['amount']) or prior.get('tax_included')!=point.get('tax_included'):
            held.append({'reason':'Conflicting observation on the same source day; existing reviewed fact retained','point':point,'retained_source':prior['source_url']})
        else:duplicates+=1
        continue
    accepted[key]=point
points=sorted(accepted.values(),key=lambda d:(d['product'],d['observed_on'],d['retailer'],d['volume_ml'],d['abv']))
report={'scope':'Reviewed annual retailer captures across legacy and modern URL layouts. Exact primary product/row, volume, strength and price are required. Missing years and failed requests are not reconstructed.','points':points,'indexes':incoming.get('indexes',[]),'errors':incoming.get('errors',[]),'unaccepted_candidates':held,'review':{'reviewed_on':'2026-10-25','old_points':len(old['points']),'candidate_points':len(incoming['points']),'accepted_points':len(points),'duplicates_ignored':duplicates,'held_for_review':len(held),'candidate_report_sha256':hashlib.sha256((ROOT/'data/prices/archive-expansion.json').read_bytes()).hexdigest()}}
if args.accept_reviewed:base.write_text(json.dumps(report,indent=2)+'\n')
print({**report['review'],'write':args.accept_reviewed,'canonical_products':len({p['product'] for p in points})})
