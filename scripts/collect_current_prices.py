#!/usr/bin/env python3
"""Observe reviewed retailer pages now. These are current offers, never historical reconstructions."""
import sys,json,hashlib,urllib.request,urllib.parse,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from catalog.price_archive import parse_capture,AGENT

def observe(target):
    now=datetime.now(timezone.utc);ident=target['retailer_id'];url=target.get('modern_url') or target.get('source_url') or target.get('verified_url')
    if not url:raise ValueError('No reviewed current page URL')
    def valid(value):
        parsed=urllib.parse.urlparse(value)
        return parsed.scheme=='https' and parsed.hostname in ['www.thewhiskyexchange.com','thewhiskyexchange.com'] and parsed.path.lower().startswith(f'/p/{ident}/')
    if not valid(url):raise ValueError('Current page does not match reviewed retailer ID')
    cache=ROOT/'work/current-prices';cache.mkdir(parents=True,exist_ok=True)
    rawpath=cache/f'{ident}-{now.date().isoformat()}.html'
    if rawpath.exists():raw=rawpath.read_bytes()
    else:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':AGENT}),timeout=25) as response:
            if not valid(response.url):raise ValueError('Current page redirected to another retailer or product')
            raw=response.read(4*1024*1024+1)
            if len(raw)>4*1024*1024:raise ValueError('Response too large')
        rawpath.write_bytes(raw)
    point=parse_capture(raw,target,now.strftime('%Y%m%d%H%M%S'),url)
    point.update(basis='current_offer',source_url=url,retrieved_at=now.isoformat(),date_scope='Price displayed on the retrieval date. Not a purchase, earlier price, or guarantee of availability.')
    return point
if __name__=='__main__':
    targets=json.loads((ROOT/'data/prices/targets.json').read_text());points=[];errors=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures={pool.submit(observe,t):t for t in targets}
        for future in as_completed(futures):
            t=futures[future]
            try:p=future.result();points.append(p);print(p['product'],p['amount'],flush=True)
            except Exception as exc:errors.append({'product':t['product'],'retailer_id':t['retailer_id'],'error':str(exc)[:200]});print('unavailable',t['product'],type(exc).__name__,flush=True)
            report={'scope':'Current retailer offers on retrieval date, not twenty-year historical coverage. Exact heading, volume and strength required. Raw copyrighted HTML stays local.','points':sorted(points,key=lambda p:(p['product'],p['observed_on'])),'errors':errors}
            (ROOT/'data/prices/current-research.json').write_text(json.dumps(report,indent=2)+'\n')
