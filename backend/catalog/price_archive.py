"""Bounded Wayback price research. Only an explicit product-price node is parsed."""
import json,re,html,time,hashlib,urllib.request,urllib.parse
from datetime import datetime,timezone
from pathlib import Path
AGENT='Alcooltest/1.0 (https://github.com/nabz0r/AlcooholTest; archival price research)'
HOST='web.archive.org'
def fetch(url,cache):
    if urllib.parse.urlparse(url).hostname!=HOST:raise ValueError('Archive host rejected')
    cache=Path(cache);cache.parent.mkdir(parents=True,exist_ok=True)
    if cache.exists():return cache.read_bytes()
    req=urllib.request.Request(url,headers={'User-Agent':AGENT,'Accept':'application/json,text/html'})
    with urllib.request.urlopen(req,timeout=35) as response:
        final=urllib.parse.urlparse(response.url)
        if final.hostname!=HOST:raise ValueError('Archive redirected outside archive')
        if '/web/' in url and '/web/'+url.split('/web/')[1].split('/')[0][:14] not in response.url:raise ValueError('Capture timestamp changed')
        raw=response.read(4*1024*1024+1)
        if len(raw)>4*1024*1024:raise ValueError('Archive response too large')
    tmp=cache.with_suffix(cache.suffix+'.tmp');tmp.write_bytes(raw);tmp.replace(cache);return raw

def parse_capture(raw,target,timestamp,original):
    text=raw.decode('utf-8',errors='replace');plain=lambda s:html.unescape(re.sub('<[^>]+>',' ',s)).strip()
    heading=re.search(r'<h1\b[^>]*>(.*?)</h1>',text,re.S|re.I)
    title=plain(heading.group(1)) if heading else ''
    if not title or any(token.lower() not in title.lower() for token in target['tokens']):raise ValueError('Product heading does not match reviewed target')
    # The old taxed-price node excludes ex-VAT and recommendation prices.
    price=re.search(r'<span[^>]+id=["\'][^"\']*LblPriceTaxed["\'][^>]*>(.*?)</span>',text,re.S|re.I)
    if not price:
        candidates=list(re.finditer(r'<span[^>]+itemprop=[\"\']price[\"\'][^>]*>(.*?)</span>',text,re.S|re.I))
        if len(candidates)==1:price=candidates[0]
    if not price:
        basket=re.search(r'<div[^>]+id=[\"\']basket[\"\'][^>]*>(.*?)<!-- End: Offer, Price and Basket -->',text,re.S|re.I)
        if basket:price=re.search(r'<div[^>]+class=[\"\']price[\"\'][^>]*>(.*?)</div>',basket.group(1),re.S|re.I)
    if not price:raise ValueError('No supported product-specific taxed price node; review required')
    amount=re.search(r'£\s*([\d,]+\.\d{2})',plain(price.group(1)))
    if not amount:raise ValueError('No unambiguous GBP amount in taxed price')
    # Require adjacent detail-table cells, not arbitrary mentions elsewhere in the page.
    cells=[plain(v) for v in re.findall(r'<td[^>]*class=["\']detailBox02["\'][^>]*>(.*?)</td>',text,re.S|re.I)]
    volume=next((re.fullmatch(r'(\d+(?:\.\d+)?)\s*cl',v,re.I) for v in cells if re.fullmatch(r'(\d+(?:\.\d+)?)\s*cl',v,re.I)),None)
    abv=next((re.fullmatch(r'(\d+(?:\.\d+)?)\s*%',v) for v in cells if re.fullmatch(r'(\d+(?:\.\d+)?)\s*%',v)),None)
    if not volume or not abv:
        formats=re.findall(r'<(?:div|span)[^>]+class=[\"\'](?:size|strength)[\"\'][^>]*>(.*?)</(?:div|span)>',text,re.S|re.I)
        matches=[re.fullmatch(r'(\d+(?:\.\d+)?)\s*cl\s*/\s*(\d+(?:\.\d+)?)\s*%',plain(f),re.I) for f in formats]
        matches=[m for m in matches if m]
        if len(matches)==1:
            volume=re.match(r'(.*)',matches[0].group(1));abv=re.match(r'(.*)',matches[0].group(2))
    if not volume or not abv:raise ValueError('Bottling volume or ABV is not explicit in the capture')
    return {'product':target['product'],'retailer_id':target['retailer_id'],'title':title,'observed_on':datetime.strptime(timestamp,'%Y%m%d%H%M%S').date().isoformat(),'timestamp':timestamp,'amount':amount.group(1).replace(',',''),'currency':'GBP','country':'United Kingdom','retailer':'The Whisky Exchange','volume_ml':round(float(volume.group(1))*10),'abv':abv.group(1),'tax_included':True,'basis':'archive_capture','source_url':'https://web.archive.org/web/'+timestamp+'/'+original,'original_url':original,'content_sha256':hashlib.sha256(raw).hexdigest(),'retrieved_at':datetime.now(timezone.utc).isoformat(),'date_scope':'Archive capture date; not a transaction or guaranteed start of the offer.'}

def collect(targets,root,max_captures=8,notify=None):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);points=[];errors=[];indexes=[]
    for target in targets:
        ident=int(target['retailer_id'])
        if not 1<=ident<=999999:raise ValueError('Invalid reviewed retailer identifier')
        query={'url':f'thewhiskyexchange.com/P-{ident}.aspx','output':'json','filter':['statuscode:200','mimetype:text/html'],'collapse':'timestamp:4','from':'1999','to':'2026','limit':'40'}
        url='https://web.archive.org/cdx/search/cdx?'+urllib.parse.urlencode(query,doseq=True)
        try:
            index=json.loads(fetch(url,root/f'{ident}-index.json'));indexes.append({'product':target['product'],'url':url,'captures':len(index)-1})
            for row in index[1:max_captures+1]:
                stamp,original=row[1],row[2]
                if not re.fullmatch(r'\d{14}',stamp) or urllib.parse.urlparse(original).hostname not in ['www.thewhiskyexchange.com','thewhiskyexchange.com']:raise ValueError('Invalid indexed capture')
                try:
                    raw=fetch('https://web.archive.org/web/'+stamp+'id_/'+original,root/f'{ident}-{stamp}.html');point=parse_capture(raw,target,stamp,original);points.append(point)
                    if notify:notify(point)
                except Exception as exc:errors.append({'product':target['product'],'timestamp':stamp,'error':str(exc)[:180]})
                time.sleep(1)
        except Exception as exc:errors.append({'product':target['product'],'error':str(exc)[:180]})
    return {'scope':'Bounded annual captures of reviewed retailer product IDs. Missing years are not interpolated. Raw page text is not redistributed. Parsed facts require editorial review.','indexes':indexes,'points':points,'errors':errors}

def stage_price(point):
    from . import models as m
    product=m.Product.objects.filter(slug=point['product'],merged_into__isnull=True).first()
    candidate,_=m.DiscoveryCandidate.objects.get_or_create(provider='wayback',external_id=f"{point['retailer_id']}:{point['timestamp']}",defaults={'label':point['title'][:240],'category':product.category if product else 'Whisky','source_url':point['source_url'],'payload':point,'resolved_product':product})
    return candidate

def price_archive_to_file(path):
    from django.conf import settings
    from .models import DiscoveryCursor
    targets=json.loads((settings.SEED_FILE.parent.parent/'prices/targets.json').read_text())
    cursor,_=DiscoveryCursor.objects.get_or_create(key='price-archive:targets')
    index=int(cursor.cursor or '0')%len(targets)
    report=collect([targets[index]],settings.EXPORT_ROOT/'price-archive-cache',max_captures=20,notify=stage_price)
    cursor.cursor=str((index+1)%len(targets));cursor.save()
    with path.open('w') as stream:
        stream.write(json.dumps({'type':'manifest','scope':report['scope'],'target':targets[index],'requires_editorial_acceptance':True})+'\n')
        for row in report['points']:stream.write(json.dumps({'type':'price_candidate',**row})+'\n')
        stream.write(json.dumps({'type':'summary','parsed':len(report['points']),'errors':report['errors']})+'\n')
