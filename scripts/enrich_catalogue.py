"""Apply reviewed, source-linked editorial overlays; never scrape into published rows."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def apply_enrichment(T,uid):
    def source(key,d,title):
        ident=uid('sources/enrichment/'+key)
        T['sources'].append(dict(id=ident,title=title[:240],url=d['url'],publisher=d['publisher'],kind=d.get('kind','manufacturer'),accessed_on='2026-10-25',license_note='Linked source and original editorial paraphrase. Source text, images and trademarks retain their rights.'))
        return ident
    def key(name):return re.sub('[^a-z0-9]+','-',name.lower()).strip('-')
    by_slug={p['slug']:p for p in T['products']};by_ing={i['name'].casefold():i for i in T['ingredients']}
    for d in json.loads((ROOT/'data/enrichment/dossiers.json').read_text()):
        p=by_slug[d['product']];slug=p['slug'];src=source(slug,d['source'],p['name']+' — history and production')
        # Keep the richer existing Monkey founder account; the new process retains its own source.
        if slug!='monkey-47-schwarzwald':p['history']=d['history'];p['history_source_id']=src
        p['description']=d['process'];p['disclosure']='partial'
        existing=next((r for r in T['recipes'] if r['product_id']==p['id']),None)
        if existing:
            existing.update(process=d['process'],notes=d['notes'],source_id=src)
            if d.get('declared_count') is not None:existing['declared_count']=d['declared_count']
            r=existing
        else:
            r=dict(id=uid('recipes/'+slug),product_id=p['id'],version='Public disclosure · 2026-10-25',declared_count=d.get('declared_count'),process=d['process'],notes=d['notes'],source_id=src);T['recipes'].append(r)
        inputsrc=source(slug+'-inputs',d['input_source'],p['name']+' — disclosed production inputs') if d.get('input_source') else src
        for name in d['inputs']:
            i=by_ing.get(name.casefold())
            if not i:
                k=key(name);i=dict(id=uid('ingredients/'+k),slug=k,name=name,scientific_name='',family='production input',notes='Named input, not a reconstructed formula or finished-product concentration.',navigation_group='');T['ingredients'].append(i);by_ing[name.casefold()]=i
            if not any(x['recipe_id']==r['id'] and x['ingredient_id']==i['id'] for x in T['recipe_ingredients']):
                T['recipe_ingredients'].append(dict(id=uid('recipe_ingredients/'+slug+'/'+i['slug']),recipe_id=r['id'],ingredient_id=i['id'],source_id=inputsrc,certainty='confirmed' if d.get('input_source',d['source']).get('kind','manufacturer')=='manufacturer' else 'reported',stage='Disclosed production input',amount=None,unit='',notes='Use the linked production account for the stage. No amount or measured transfer to the beverage is inferred.'))
        if d.get('bottling_verified') and d.get('abv') is not None and not any(v['product_id']==p['id'] for v in T['variants']):
            T['variants'].append(dict(id=uid('variants/'+slug+'-reference'),product_id=p['id'],name='Documented reference',market=d['market'],abv=str(d['abv']),volume_ml=d['volume_ml'],source_id=src,barcode=''))
        for n,c in enumerate(d.get('critics',[])):
            cs=source(slug+'-critic-'+str(n),dict(url=c['url'],publisher=c['publisher'],kind='secondary'),p['name']+' — attributed tasting perspective')
            T['critic_reviews'].append(dict(id=uid('critic_reviews/enrichment/'+slug+'/'+str(n)),product_id=p['id'],critic=c['publisher'],source_id=cs,summary=c['summary'],score=str(c['score']) if c.get('score') is not None else None,score_max=c.get('score_max'),published_on=c.get('published_on')))
    # Profile source is a real ingredient assertion. Details are editorially editable from Ingredients.
    recipes={r['id']:r for r in T['recipes']};sources={s['id']:s for s in T['sources']}
    for i in T['ingredients']:
        assertions=[a for a in T['recipe_ingredients'] if a['ingredient_id']==i['id']]
        n=i['name'].lower();part=next((v for token,v in [('peel','Fruit peel'),('leaf','Leaf'),('leaves','Leaves'),('flower','Flowers'),('root','Root / rhizome'),('bark','Bark'),('seed','Seeds'),('berry','Fruit'),('pit oil','Stone-fruit kernel oil'),('kernel oil','Stone-fruit kernel oil')] if token in n),'Part not specified in the source')
        group=next((v for tokens,v in [(['lemon','orange','yuzu','bergamot'],'citrus'),(['rose','lavender','chamomile','flower','jasmine','meadowsweet','heather'],'floral'),(['coriander','cardamom','cinnamon','cassia','pepper','cubeb','nutmeg','ginger','fennel'],'spice'),(['root','orris','angelica','liquorice'],'roots'),(['barley','wheat','corn','rye','rice','grain'],'grain'),(['apple','cherry','quince','peach','grape','cranberry','lingonberry'],'fruit'),(['sage','basil','rosemary','tea','mint','verbena','leaf','kelp','bamboo','shiso','kinome','lemongrass'],'herbal')] if any(t in n for t in tokens)),'')
        i['navigation_group']=i.get('navigation_group') or group
        role={'citrus':'Citrus ingredient. Its actual flavour contribution depends on the plant part and the producer’s extraction method.','floral':'Flower-associated ingredient. Floral tasting language alone is not evidence of use; the linked ingredient declaration establishes the connection.','spice':'Spice or seed input. The production account, rather than a tasting note, is the basis for inclusion.','roots':'Root or bark-associated production input. Preparation and extraction should follow the specific producer account.','grain':'Cereal or grain-derived input. Fermentation and distillation transform the raw material; raw-grain composition is not a finished-drink analysis.','fruit':'Fruit or fruit-derived input. Maceration, fermentation, distillation and post-distillation addition are different stages; use the named production account.','herbal':'Herbal, leafy or plant-derived input. The cited recipe establishes use, not active-compound exposure.'}.get(group,'Production material or declared blend component. It must not be interpreted as a botanical with a demonstrated neurological effect.')
        i['plant_part']=part;i['sensory_role']=role
        i['preparation']=' / '.join(dict.fromkeys(recipes[a['recipe_id']]['process'] for a in assertions))[:5000] if assertions else 'No product-specific preparation has been established.'
        i['technical_notes']='The displayed product connections are source-linked ingredient assertions. Amounts and finished-drink concentrations are unknown unless a separate measurement is present. A plant or extract study does not establish the effect of a distilled beverage.'
        i['profile_source_id']=assertions[0]['source_id'] if assertions else None
