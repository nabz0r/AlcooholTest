"""HTTP read benchmark. Never creates catalogue records; reports actual live cardinality."""
import argparse,json,time,statistics,urllib.request,concurrent.futures
p=argparse.ArgumentParser();p.add_argument('--base',default='http://localhost:8088');p.add_argument('--requests',type=int,default=100);p.add_argument('--concurrency',type=int,default=8);p.add_argument('--output');a=p.parse_args()
def get(path):
    started=time.perf_counter()
    with urllib.request.urlopen(a.base+path,timeout=30) as r: data=json.load(r)
    return (time.perf_counter()-started)*1000,data
stats=get('/api/v1/stats')[1]
results=[];errors=0
with concurrent.futures.ThreadPoolExecutor(max_workers=a.concurrency) as pool:
    jobs=[pool.submit(get,'/api/v1/products?q=juniper&limit=24' if i%2 else '/api/v1/products?limit=24') for i in range(a.requests)]
    for job in concurrent.futures.as_completed(jobs):
        try: results.append(job.result()[0])
        except Exception: errors+=1
results.sort()
report={'requests':a.requests,'concurrency':a.concurrency,'successes':len(results),'errors':errors,'dataset':{k:stats[k] for k in ['products','brands','ingredients','sources']},'latency_ms':{'median':round(statistics.median(results),2) if results else None,'p95':round(results[min(len(results)-1,int(len(results)*.95))],2) if results else None},'scope':'Mixed catalogue and ingredient-search GETs on the live dataset; not proof of performance at larger cardinalities.'}
text=json.dumps(report,indent=2);print(text)
if a.output: open(a.output,'w').write(text+'\n')
