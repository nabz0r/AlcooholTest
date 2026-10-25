#!/usr/bin/env python3
"""Rebuild per-product coverage from accepted facts, keeping local photos and links distinct."""
import json,sys
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from catalog.price_dates import price_bounds,price_label,conservative_span,comparable_basis
T=json.loads((ROOT/'data/catalog/seed.json').read_text())['tables']
products=[p for p in T['products'] if not p.get('edition_of_id') and not p.get('merged_into_id') and p['status']=='published']
launches={r['product']:r for r in json.loads((ROOT/'data/prices/coverage-research.json').read_text())}
assets=defaultdict(list);external=defaultdict(list);variants=defaultdict(list);recipes=defaultdict(list);inputs=defaultdict(list);critics=Counter();prices=defaultdict(list)
for a in T['bottle_assets']:assets[a['product_id']].append(a)
for a in T.get('external_photo_references',[]):
 if a['verified']:external[a['product_id']].append(a)
for v in T['variants']:variants[v['product_id']].append(v)
variant_ids={v['id']:v for v in T['variants']}
for r in T['recipes']:recipes[r['product_id']].append(r)
for r in T['recipe_ingredients']:inputs[r['recipe_id']].append(r)
for r in T['critic_reviews']:critics[r['product_id']]+=bool(r['summary'].strip() and r['source_id'])
for r in T['price_observations']:prices[variant_ids[r['variant_id']]['product_id']].append(r)
rows=[];coverage=[];totals=Counter()
for p in products:
 pid=p['id'];local=assets[pid];refs=external[pid];dated=sorted(prices[pid],key=price_bounds);launch=launches[p['slug']].get('first_release_year') or launches[p['slug']].get('release_not_before_year')
 valid=[r for r in dated if not launch or price_bounds(r)[0].year>=launch]
 checks={'history':bool(p['history'].strip() and p['history_source_id']),'bottling':bool(variants[pid]),'production':any(r['process'].strip() and r['source_id'] for r in recipes[pid]),'ingredients':any(inputs[r['id']] for r in recipes[pid]),'criticism':bool(critics[pid]),'front':any(a['view']=='front' for a in local),'back':any(a['view']=='back' for a in local),'prices':bool(dated)}
 for k,v in checks.items():totals[k]+=v
 available={view:checks[view] or any(r['view']==view for r in refs) for view in ['front','back']}
 earliest=dated[0] if dated else None;latest=max(dated,key=lambda row:price_bounds(row)[1]) if dated else None
 row={'slug':p['slug'],'checks':checks,'external_front':any(r['view']=='front' for r in refs),'external_back':any(r['view']=='back' for r in refs),'front_reference_available':available['front'],'rear_reference_available':available['back'],'price_points':len(dated),'price_start':price_label(earliest) if earliest else None,'price_end':price_label(latest) if latest else None,'price_start_precision':earliest.get('date_precision','day') if earliest else None,'price_end_precision':latest.get('date_precision','day') if latest else None,'all_eight':all(checks.values())}
 rows.append(row)
 start=max(2006,launch or 2006);years={price_bounds(r)[0].year for r in valid};span=conservative_span(valid)
 groups=defaultdict(list)
 for r in valid:
  category=comparable_basis(r.get('basis','unspecified'))
  if not category or r['tax_included'] is None:continue
  groups[(r['variant_id'],r['currency'],r['country'],r['retailer'],category,r['tax_included'])].append(r)
 comparable=max((conservative_span(records) for records in groups.values()),default=0)
 coverage.append({'product':p['slug'],'first_release_year':launches[p['slug']].get('first_release_year'),'release_not_before_year':launches[p['slug']].get('release_not_before_year'),'release_source_url':launches[p['slug']].get('release_source_url',''),'observations':len(dated),'start':row['price_start'],'end':row['price_end'],'start_precision':row['price_start_precision'],'end_precision':row['price_end_precision'],'observed_span_years':round(span,2),'twenty_year_evidence':span>=20,'comparable_single_series_span_years':round(comparable,2),'years_with_evidence':sorted(years),'missing_years_in_research_window':[y for y in range(start,2027) if y not in years],'prelaunch_observations':len(dated)-len(valid),'price_bases':dict(Counter(r.get('basis','unspecified') for r in dated))})
audit={'scope':'Field presence does not prove a complete recipe, current packaging or continuous historical prices. Front/back checks count licensed locally hosted images; externally verified source links are separate.','canonical_products':len(products),'totals':dict(totals),'all_eight':sum(r['all_eight'] for r in rows),'front_references_available':sum(r['front_reference_available'] for r in rows),'rear_references_available':sum(r['rear_reference_available'] for r in rows),'records':rows}
(ROOT/'data/catalog/dossier-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
report={'scope':'Accepted sourced price records. Overall spans may cross formats, retailers, markets and price bases; they are not a comparable return series. Comparable single-series spans retain variant, seller, currency, country, retail-versus-wholesale level and known tax basis and exclude MSRP or unknown basis. Month-only dates remain YYYY-MM. Elapsed spans use conservative month bounds: earliest possible evidence may occur at month end and latest at month start; those internal bounds are never stored as source observation days. Missing years are not interpolated. Document/launch dates keep their stated scope in source notes.','canonical_products':len(products),'products_with_prices':sum(bool(prices[p['id']]) for p in products),'products_with_twenty_year_evidence':sum(r['twenty_year_evidence'] for r in coverage),'products_launched_after_2006':sum((r['first_release_year'] or 0)>2006 for r in coverage),'products_with_post_2006_brand_bound':sum(not r['first_release_year'] and (r['release_not_before_year'] or 0)>2006 for r in coverage),'products_too_young_for_twenty_year_history':sum((r['first_release_year'] or r['release_not_before_year'] or 0)>2006 for r in coverage),'records':coverage}
(ROOT/'data/prices/coverage.json').write_text(json.dumps(report,indent=2)+'\n')
print({'photographs':len(T['bottle_assets']),'external_references':len(T.get('external_photo_references',[])),'local_fronts':totals['front'],'local_rears':totals['back'],'front_references':audit['front_references_available'],'rear_references':audit['rear_references_available'],'all_eight':audit['all_eight'],'prices':len(T['price_observations']),'twenty_year_spans':report['products_with_twenty_year_evidence']})
