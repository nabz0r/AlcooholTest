"""Fixed-provider, checkpointed discovery. Never treat a public claim as a verified formula."""
import json,time,urllib.request,urllib.parse,hashlib,re,html,logging
from pathlib import Path
from datetime import date
from io import BytesIO
from PIL import Image
from django.conf import settings
from .models import DiscoveryCursor,DiscoveryCandidate
AGENT='Alcooltest/1.0 (https://github.com/nabz0r/AlcooholTest; open-source research catalogue)'
CATEGORIES={'Gin':'Q959362','Rum':'Q83376','Whisky':'Q281','Vodka':'Q374','Liqueur':'Q178780','Amaretto':'Q455045'}

def request_json(url):
    allowed={'query.wikidata.org','www.wikidata.org','commons.wikimedia.org','eutils.ncbi.nlm.nih.gov'}
    if urllib.parse.urlparse(url).hostname not in allowed: raise ValueError('Provider not allowed.')
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':AGENT,'Accept':'application/json'})
            with urllib.request.urlopen(req,timeout=40) as response:
                if urllib.parse.urlparse(response.url).hostname not in allowed:raise ValueError('Unexpected provider redirect.')
                data=response.read(8*1024*1024+1)
                if len(data)>8*1024*1024:raise ValueError('Provider response too large.')
                return json.loads(data)
        except Exception:
            if attempt==2:raise
            time.sleep(1+attempt*2)

def wiki_api(host,params):return request_json(f'https://{host}/w/api.php?'+urllib.parse.urlencode({**params,'format':'json'}))
def image_for(title,candidate):
    # Commons attribution is required before downloading; raw source URLs are never arbitrary inputs.
    if not title or len(title)>250:return
    d=wiki_api('commons.wikimedia.org',{'action':'query','titles':'File:'+title,'prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':600})
    infos=next(iter(d.get('query',{}).get('pages',{}).values()),{}).get('imageinfo',[])
    if not infos:return
    info=infos[0];meta=info.get('extmetadata',{});license=meta.get('LicenseShortName',{}).get('value','')
    if not any(x in license for x in ['CC BY','CC0','Public domain']):return
    url=info.get('thumburl',info.get('url',''));host=urllib.parse.urlparse(url).hostname
    if host not in {'upload.wikimedia.org','thumb.wikimedia.org'}:return
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':AGENT}),timeout=30) as r:
        if urllib.parse.urlparse(r.url).hostname not in {'upload.wikimedia.org','thumb.wikimedia.org'}:raise ValueError('Unexpected media redirect')
        data=r.read(5*1024*1024+1)
    if len(data)>5*1024*1024:return
    im=Image.open(BytesIO(data))
    if im.format not in ['JPEG','PNG','WEBP'] or im.width*im.height>16000000:return
    im.load();im.thumbnail((1000,1000));out=BytesIO();im.convert('RGB').save(out,format='JPEG',quality=88)
    root=settings.MEDIA_ROOT/'discovery';root.mkdir(parents=True,exist_ok=True);path=root/f'{candidate.id}.jpg';path.write_bytes(out.getvalue())
    plain=lambda s:html.unescape(re.sub('<[^>]+>','',s)).strip()
    candidate.image_path='discovery/'+path.name
    candidate.image_metadata={'source_page':info.get('descriptionurl'),'author':plain(meta.get('Artist',{}).get('value','See source page')),'license':license,'license_url':meta.get('LicenseUrl',{}).get('value',''),'download_url':url,'sha256':hashlib.sha256(out.getvalue()).hexdigest(),'modifications':'Thumbnail converted to JPEG and limited to 1000px.','caution':'Discovery image may show a distillery, a collection, another edition or non-bottle subject. Editor verification required.'}
    candidate.save(update_fields=['image_path','image_metadata','updated_at'])

def discover_to_file(path):
    summary={'provider':'Wikidata','license':'CC0-1.0 structured metadata; image licenses recorded individually','candidates':0,'images':0,'categories':{},'errors':[],'complete_internet_coverage':False}
    with path.open('w') as stream:
        stream.write(json.dumps({'type':'manifest','schema_version':'discovery-1.0','retrieved_on':date.today().isoformat(),'scope':'One checkpointed page of up to 25 Wikidata-classified entries per category. Not every public bottle; staged for review.','license':summary['license']})+'\n')
        for category,qid in CATEGORIES.items():
            cursor,_=DiscoveryCursor.objects.get_or_create(key='wikidata:'+qid)
            if cursor.exhausted:summary['categories'][category]={'exhausted':True,'fetched':0};continue
            try:
                last=cursor.cursor
                if last and not re.fullmatch(r'Q\d+',last):raise ValueError('Invalid checkpoint.')
                after=f'FILTER(STR(?item)>"http://www.wikidata.org/entity/{last}")' if last else ''
                query=f'SELECT DISTINCT ?item WHERE {{ ?item wdt:P31/wdt:P279* wd:{qid} . {after} }} ORDER BY ?item LIMIT 25'
                result=request_json('https://query.wikidata.org/sparql?'+urllib.parse.urlencode({'query':query,'format':'json'}))
                ids=[b['item']['value'].rsplit('/',1)[-1] for b in result['results']['bindings']]
                if not ids:cursor.exhausted=True;cursor.save();summary['categories'][category]={'exhausted':True,'fetched':0};continue
                entities=wiki_api('www.wikidata.org',{'action':'wbgetentities','ids':'|'.join(ids),'props':'labels|descriptions|claims','languages':'en'})['entities']
                image_count=0
                for external,entity in entities.items():
                    label=entity.get('labels',{}).get('en',{}).get('value',external)
                    candidate,_=DiscoveryCandidate.objects.update_or_create(provider='wikidata',external_id=external,defaults={'label':label[:240],'category':category,'source_url':'https://www.wikidata.org/wiki/'+external,'payload':entity})
                    claims=entity.get('claims',{});images=claims.get('P18',[])
                    if images and not candidate.image_path and image_count<3:
                        image_count+=1
                        try:
                            image_for(images[0]['mainsnak']['datavalue']['value'],candidate)
                            if candidate.image_path:summary['images']+=1
                        except Exception as exc:logging.getLogger(__name__).warning('Image %s skipped: %s',external,type(exc).__name__)
                    stream.write(json.dumps({'type':'candidate','provider':'wikidata','external_id':external,'category':category,'source_url':candidate.source_url,'retrieved_on':date.today().isoformat(),'license':'CC0-1.0','payload':entity,'image_path':candidate.image_path,'image_metadata':candidate.image_metadata},ensure_ascii=False)+'\n');stream.flush();summary['candidates']+=1
                cursor.cursor=ids[-1];cursor.exhausted=len(ids)<25;cursor.save();summary['categories'][category]={'fetched':len(ids),'cursor':cursor.cursor,'exhausted':cursor.exhausted}
            except Exception as exc:summary['errors'].append({'category':category,'error':type(exc).__name__});logging.getLogger(__name__).exception('Discovery category failed: %s',category)
        stream.write(json.dumps({'type':'summary',**summary})+'\n')
    if not summary['candidates'] and summary['errors']:raise ValueError('No provider page succeeded.')
    return summary

RESEARCH_QUERIES={'linalool':'linalool AND (anxiety OR neurological)','myristicin':'myristicin AND (toxicology OR intoxication)','thujone':'thujone AND (alcohol OR GABA)','ethanol':'ethanol AND NMDA','chamomile':'chamomile AND randomized AND anxiety'}
def research_to_file(path):
    summary={'provider':'NCBI PubMed','records':0,'queries':{},'scope':'Bibliographic metadata only; no full-paper copying and no automatic clinical-effect extraction.'}
    with path.open('w') as out:
        out.write(json.dumps({'type':'manifest','schema_version':'research-discovery-1.0','retrieved_on':date.today().isoformat(),'scope':summary['scope']})+'\n')
        seen=set()
        for key,query in RESEARCH_QUERIES.items():
            base='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
            result=request_json(base+'esearch.fcgi?'+urllib.parse.urlencode({'db':'pubmed','term':query,'retmax':20,'retmode':'json','sort':'pub date','tool':'alcooltest'}))
            ids=result['esearchresult']['idlist'];time.sleep(.4)
            summary['queries'][key]={'query':query,'total_matches':result['esearchresult']['count'],'fetched':len(ids)}
            if not ids:continue
            records=request_json(base+'esummary.fcgi?'+urllib.parse.urlencode({'db':'pubmed','id':','.join(ids),'retmode':'json','tool':'alcooltest'}))['result'];time.sleep(.4)
            for pmid in records.get('uids',[]):
                if pmid in seen:continue
                seen.add(pmid);payload=records[pmid]
                DiscoveryCandidate.objects.update_or_create(provider='pubmed',external_id=pmid,defaults={'label':payload.get('title',pmid)[:240],'category':'Research','source_url':f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/','payload':payload})
                out.write(json.dumps({'type':'publication','pmid':pmid,'source_url':f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/','query':query,'payload':payload})+'\n');summary['records']+=1
        out.write(json.dumps({'type':'summary',**summary})+'\n')
    return summary
