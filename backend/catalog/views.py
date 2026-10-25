from .discovery import with_coverage,coverage as coverage_data,find,ingredients as indexed_ingredients,related
import json, secrets
from functools import wraps
from uuid import UUID
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Count, Avg
from django.conf import settings
from django.shortcuts import get_object_or_404
from . import models as m
from .interchange import validate_document, encode
from .cache import public_cache


def reply(data,status=200): return JsonResponse(data,safe=not isinstance(data,list),status=status,json_dumps_params={'default':encode})
def body(request):
    if request.content_type!='application/json': raise ValueError('Send application/json.')
    data=json.loads(request.body)
    if not isinstance(data,dict): raise ValueError('Expected a JSON object.')
    return data

def api(fn):
    @wraps(fn)
    def inner(request,*args,**kwargs):
        try: return fn(request,*args,**kwargs)
        except (ValueError,TypeError,KeyError,ValidationError) as exc:
            return reply({'error':'; '.join(exc.messages) if isinstance(exc,ValidationError) else str(exc)},400)
    return inner

def auth(staff=False):
    def decorate(fn):
        @wraps(fn)
        def inner(request,*args,**kwargs):
            if not request.user.is_authenticated: return reply({'error':'Sign in to continue.'},401)
            if staff and not (request.user.is_staff and request.user.has_perm('catalog.add_job')): return reply({'error':'Staff access required.'},403)
            return fn(request,*args,**kwargs)
        return inner
    return decorate

def audit(request,action,target,detail=None): m.Audit.objects.create(actor=request.user if request.user.is_authenticated else None,action=action,target=str(target),detail=detail or {})

def source_data(s): return {'id':s.id,'title':s.title,'url':s.url,'publisher':s.publisher,'kind':s.kind,'accessed_on':s.accessed_on}

def card(p):
    asset=next((a for a in p.assets.all() if a.view=='front'),None)
    member=next(iter(getattr(p,'approved_fronts',[])),None)
    image=p.photo.url if p.photo else asset.local_path if asset else member.photo.url if member else None
    credit=p.photo_credit if p.photo else asset.author if asset else member.credit if member else ''
    license=p.photo_license if p.photo else asset.license if asset else member.license if member else ''
    image_source=asset.source_page if asset and not p.photo else member.source_url if member and not p.photo else None
    note=asset.edition_note if asset and not p.photo else member.caption if member and not p.photo else ''
    return {
      'coverage':coverage_data(p) if hasattr(p,'documented_areas') else None,
      'history':p.history,'history_source':source_data(p.history_source) if p.history_source_id else None,
      'merged_into':p.merged_into.slug if p.merged_into_id else None,'edition_of':p.edition_of.slug if p.edition_of_id else None,
      'editions':[{'slug':e.slug,'name':e.name} for e in p.editions.all() if e.status=='published'],
      'id':p.id,'slug':p.slug,'name':p.name,'brand':p.brand.name,'country':p.brand.country,'category':p.category,
      'description':p.description,'disclosure':p.disclosure,'color':p.color,'shape':p.shape,
      'photo':p.photo.url if p.photo else None,'photo_credit':p.photo_credit,'photo_license':p.photo_license,
      'image':image,'image_credit':credit,'image_license':license,'image_source':image_source,'image_note':note,
      'locality':p.place.name if p.place else '','region':p.place.region if p.place else '',
      'origin_source':source_data(p.place.source) if p.place else None,
      'variants':[{'id':v.id,'name':v.name,'market':v.market,'abv':v.abv,'volume_ml':v.volume_ml,'source':source_data(v.source)} for v in p.variants.all()]
    }

@require_GET
@api
def health(request):
    from django.db import connection
    with connection.cursor() as cur: cur.execute('SELECT 1')
    return reply({'status':'ok','version':'1.0.0'})

@require_GET
@ensure_csrf_cookie
def session(request):
    return reply({'user':{'username':request.user.username,'staff':request.user.is_staff} if request.user.is_authenticated else None,'setup_required':not m.Installation.objects.filter(pk=1,completed=True).exists(),'registration_open':settings.REGISTRATION_OPEN})

@require_POST
@api
def setup(request):
    data=body(request)
    if not settings.SETUP_TOKEN or not secrets.compare_digest(str(data.get('token','')),settings.SETUP_TOKEN): return reply({'error':'Invalid setup token.'},403)
    with transaction.atomic():
        m.Installation.objects.get_or_create(pk=1)
        state=m.Installation.objects.select_for_update().get(pk=1)
        if state.completed or get_user_model().objects.filter(is_superuser=True).exists(): return reply({'error':'Setup is already complete.'},409)
        username=str(data['username']).strip(); user=get_user_model()(username=username)
        user.full_clean(exclude=['password']); validate_password(data['password'],user)
        user.set_password(data['password']); user.is_staff=True; user.is_superuser=True; user.save()
        state.completed=True; state.save(); login(request,user); audit(request,'installation.completed',user.pk)
    return reply({'ok':True},201)

@require_POST
@api
def register(request):
    if not settings.REGISTRATION_OPEN: return reply({'error':'Registration is closed.'},403)
    if not m.Installation.objects.filter(pk=1,completed=True).exists(): return reply({'error':'Complete installation first.'},409)
    data=body(request); user=get_user_model()(username=str(data['username']).strip())
    user.full_clean(exclude=['password']); validate_password(data['password'],user)
    user.set_password(data['password']); user.save(); login(request,user)
    return reply({'ok':True},201)

@require_POST
@api
def sign_in(request):
    data=body(request); user=authenticate(request,username=data.get('username',''),password=data.get('password',''))
    if user is None: return reply({'error':'Invalid username or password.'},401)
    login(request,user); return reply({'ok':True})

@require_POST
def sign_out(request): logout(request); return reply({'ok':True})

@require_GET
@api
@public_cache(60)
def products(request):
    q=request.GET.get('q','').strip()[:120]
    qs=m.Product.objects.filter(status='published').select_related('brand','place__source','history_source','edition_of','merged_into').prefetch_related('variants__source','assets','editions').select_related('edition_of')
    qs=with_coverage(qs)
    if request.GET.get('editions')!='all': qs=qs.filter(edition_of__isnull=True)
    if q: qs=qs.filter(Q(name__icontains=q)|Q(brand__name__icontains=q)|Q(recipes__ingredients__ingredient__name__icontains=q)).distinct()
    if request.GET.get('category'): qs=qs.filter(category=request.GET['category'][:40])
    if request.GET.get('country'): qs=qs.filter(brand__country=request.GET['country'][:80])
    if request.GET.get('brand'): qs=qs.filter(brand__slug=request.GET['brand'][:100])
    if request.GET.get('disclosure'): qs=qs.filter(disclosure=request.GET['disclosure'])
    if request.GET.get('ingredient'): qs=qs.filter(recipes__ingredients__ingredient__slug=request.GET['ingredient'][:100]).distinct()
    if request.GET.get('after'): qs=qs.filter(id__gt=UUID(request.GET['after']))
    limit=max(1,min(int(request.GET.get('limit','24')),60)); items=list(qs.order_by('id')[:limit+1])
    return reply({'items':[card(p) for p in items[:limit]],'next':str(items[limit-1].id) if len(items)>limit else None})

@require_GET
@api
@public_cache(60)
def product(request,slug):
    p=get_object_or_404(with_coverage(m.Product.objects.select_related('brand','place__source','history_source','edition_of','merged_into').prefetch_related('editions','assets','variants__source','recipes__source','recipes__ingredients__ingredient','recipes__ingredients__source')),slug=slug)
    if p.merged_into_id:
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect('/api/v1/products/'+p.merged_into.slug)
    if p.status!='published':
        from django.http import Http404
        raise Http404
    result=card(p); recipes=[]
    for r in p.recipes.all():
        recipes.append({'id':r.id,'version':r.version,'declared_count':r.declared_count,'process':r.process,'notes':r.notes,'source':source_data(r.source),'ingredients':[{'id':x.ingredient.id,'slug':x.ingredient.slug,'name':x.ingredient.name,'scientific_name':x.ingredient.scientific_name,'certainty':x.certainty,'stage':x.stage,'amount':x.amount,'unit':x.unit,'notes':x.notes,'source':source_data(x.source)} for x in r.ingredients.all()]})
    result['recipes']=recipes
    result['alternatives']=[{**card(x),'shared_ingredients':shared,'basis':'Shared indexed ingredients' if shared else 'Same category; no ingredient overlap established'} for x,shared in related(p)]
    result['photos']=[{'id':x.id,'view':x.view,'url':x.local_path,'credit':x.author,'license':x.license,'source_url':x.source_page,'caption':x.edition_note} for x in p.assets.all()]+[{'id':x.id,'view':x.view,'url':x.photo.url,'credit':x.credit,'license':x.license,'source_url':x.source_url,'caption':x.caption} for x in p.community_photos.filter(approved=True)]
    result['review_dimensions']=p.reviews.filter(approved=True).aggregate(**{key:Avg(key) for key in ['aroma','taste','finish','value','design']}) | p.reviews.filter(approved=True).aggregate(**{key+'_count':Count(key) for key in ['aroma','taste','finish','value','design']})
    ids=m.RecipeIngredient.objects.filter(recipe__product=p).values_list('ingredient_id',flat=True)
    compounds=m.Compound.objects.filter(ingredientcompound__ingredient_id__in=ids).distinct().prefetch_related('studies__source')
    result['prices']=[{'variant_id':v.variant_id,'date':v.observed_on,'amount':v.amount,'currency':v.currency,'country':v.country,'retailer':v.retailer,'variant':str(v.variant),'volume_ml':v.variant.volume_ml,'abv':v.variant.abv,'promotion':v.promotion,'tax_included':v.tax_included,'source':source_data(v.source)} for v in m.PriceObservation.objects.filter(variant__product=p).select_related('variant__product__brand','source').order_by('observed_on')]
    result['compounds']=[{'id':c.id,'name':c.name,'ingredients':list(c.ingredientcompound_set.filter(ingredient_id__in=ids).values_list('ingredient__name',flat=True)),'notes':c.notes,'mechanisms':[{'target':x.target,'action':x.action,'evidence_context':x.evidence_context,'limitation':x.limitation,'source':source_data(x.source)} for x in c.mechanisms.select_related('source').all()],'studies':[{'title':s.title,'design':s.design,'population':s.population,'finding':s.finding,'limitation':s.limitation,'beverage_evidence':s.beverage_evidence,'source':source_data(s.source)} for s in c.studies.all()]} for c in compounds]
    result['critic_reviews']=[{'critic':x.critic,'summary':x.summary,'score':x.score,'score_max':x.score_max,'source':source_data(x.source)} for x in p.critic_reviews.select_related('source').all()]
    ethanol=m.Compound.objects.filter(slug='ethanol').first()
    result['ethanol_mechanisms']=[{'target':x.target,'action':x.action,'evidence_context':x.evidence_context,'limitation':x.limitation,'source':source_data(x.source)} for x in ethanol.mechanisms.select_related('source').all()] if ethanol else []
    result['measurements']=[{'compound':x.compound.name,'value':x.value,'unit':x.unit,'method':x.method,'batch':x.batch,'source':source_data(x.source)} for x in m.Measurement.objects.filter(variant__product=p).select_related('compound','source')]
    reviews=p.reviews.filter(approved=True).select_related('user')
    result['rating']=reviews.aggregate(average=Avg('rating'),count=Count('id'))
    result['reviews']=[{'username':r.user.username,'rating':r.rating,'text':r.text,'dimensions':{k:getattr(r,k) for k in ['aroma','taste','finish','value','design']},'context':r.context,'tags':r.tags,'buy_again':r.buy_again} for r in reviews.order_by('-updated_at')[:30]]
    return reply(result)

@require_GET
@public_cache(60)
def stats(request):
    return reply({'products':m.Product.objects.filter(status='published',edition_of__isnull=True).count(),'editions':m.Product.objects.filter(status='published',edition_of__isnull=False).count(),'brands':m.Brand.objects.count(),'ingredients':m.Ingredient.objects.count(),'sources':m.Source.objects.count(),'images':m.BottleAsset.objects.count(),'places':m.Place.objects.count(),'studies':m.Study.objects.count(),'measurements':m.Measurement.objects.count(),'categories':list(m.Product.objects.filter(status='published').values_list('category',flat=True).distinct().order_by('category')),'countries':list(m.Brand.objects.values_list('country',flat=True).distinct().order_by('country'))})

@require_GET
@public_cache(60)
def evidence(request):
    return reply({'compounds':[{'id':c.id,'name':c.name,'notes':c.notes,'mechanisms':[{'target':x.target,'action':x.action,'evidence_context':x.evidence_context,'limitation':x.limitation,'source':source_data(x.source)} for x in c.mechanisms.select_related('source').all()],'studies':[{'title':s.title,'design':s.design,'population':s.population,'finding':s.finding,'limitation':s.limitation,'beverage_evidence':s.beverage_evidence,'source':source_data(s.source)} for s in c.studies.all()]} for c in m.Compound.objects.prefetch_related('studies__source').order_by('name')[:100]],'notice':'Plant composition is not beverage exposure. Study results do not establish effects of a commercial drink.'})

@require_POST
@auth()
@api
def submit(request):
    data=body(request); clean=clean_submission(data)
    item=m.Submission.objects.create(user=request.user,payload=clean)
    audit(request,'submission.created',item.id); return reply({'id':item.id,'status':'pending'},201)

def clean_submission(data):
    fields={'brand':120,'name':160,'country':80,'description':4000,'source_url':1000,'ingredients':4000,'market':80}
    clean={k:str(data.get(k,'')).strip() for k in fields}
    for k,n in fields.items():
        if not clean[k] or len(clean[k])>n: raise ValueError(f'{k}: required; maximum {n} characters.')
    from django.core.validators import URLValidator
    URLValidator(schemes=['https'])(clean['source_url'])
    clean['category']=str(data.get('category','Gin')).strip()
    if not 1<=len(clean['category'])<=40: raise ValueError('Category is required; maximum 40 characters.')
    clean['abv']=float(data['abv']); clean['volume_ml']=int(data['volume_ml'])
    if not 0<=clean['abv']<=100 or not 1<=clean['volume_ml']<=30000: raise ValueError('Invalid strength or bottle size.')
    return clean

@require_POST
@auth()
@api
def review(request,slug):
    p=get_object_or_404(m.Product,slug=slug,status='published'); data=body(request)
    rating=int(data['rating']); note=str(data['text']).strip()
    if not 0<=rating<=5 or not 1<=len(note)<=2000: raise ValueError('Use a rating from 0 to 5 and a note under 2,000 characters.')
    m.Review.objects.update_or_create(user=request.user,product=p,defaults=review_fields(data,rating,note))
    return reply({'status':'pending'})

@auth()
@api
def collection(request):
    if request.method=='GET': return reply({'items':[{'state':c.state,'product':card(c.product)} for c in m.Collection.objects.filter(user=request.user).select_related('product__brand','product__place__source').prefetch_related('product__variants__source','product__assets').order_by('-updated_at')[:500]]})
    if request.method!='POST': return reply({'error':'Method not allowed'},405)
    data=body(request); p=get_object_or_404(m.Product,slug=data['slug'],status='published')
    if data['state']=='remove': m.Collection.objects.filter(user=request.user,product=p).delete()
    elif data['state'] in ['wishlist','owned','tasted']: m.Collection.objects.update_or_create(user=request.user,product=p,defaults={'state':data['state']})
    else: raise ValueError('Invalid collection state.')
    return reply({'ok':True})

@require_GET
@auth(True)
def operations(request):
    return reply({'jobs':[{'id':j.id,'kind':j.kind,'status':j.status,'created_at':j.created_at,'size':j.size,'sha256':j.checksum,'error':j.error} for j in m.Job.objects.order_by('-created_at')[:50]],'discovery_candidates':m.DiscoveryCandidate.objects.count(),'discovery_images':m.DiscoveryCandidate.objects.exclude(image_path='').count(),'cursors':list(m.DiscoveryCursor.objects.values('key','cursor','exhausted')),'pending_submissions':m.Submission.objects.filter(status='pending').count(),'pending_reviews':m.Review.objects.filter(approved=False).count(),'pending_photos':m.BottlePhoto.objects.filter(approved=False).count()})

@require_POST
@auth(True)
@api
def create_job(request):
    data=body(request); kind=data.get('kind')
    if kind not in ['json','jsonl','sql','discover','research','prices']: raise ValueError('Choose json, jsonl, sql, discover, research or prices.')
    if m.Job.objects.filter(status__in=['queued','running']).count()>=5: return reply({'error':'Queue is full. Wait for current jobs.'},429)
    job=m.Job.objects.create(kind=kind,created_by=request.user); audit(request,'export.queued',job.id,{'kind':kind})
    return reply({'id':job.id,'status':job.status},202)

@require_POST
@auth(True)
@api
def import_data(request):
    data=body(request); doc=data['document']; counts=validate_document(doc)
    if not data.get('commit'): return reply({'valid':True,'counts':counts,'mode':'Upsert by UUID; no deletion. Replaces fields on matching records.'})
    if m.Job.objects.filter(status__in=['queued','running']).count()>=5: return reply({'error':'Queue is full.'},429)
    job=m.Job.objects.create(kind='import',created_by=request.user)
    settings.EXPORT_ROOT.mkdir(parents=True,exist_ok=True)
    path=settings.EXPORT_ROOT/f'{job.id}.input'; path.write_text(json.dumps(doc)); path.chmod(0o600)
    audit(request,'import.queued',job.id,counts); return reply({'id':job.id,'status':'queued'},202)

@require_GET
@auth(True)
@api
def download(request,job_id,manifest=False):
    job=get_object_or_404(m.Job,id=job_id,status='done')
    filename=f'{job.id}.manifest.json' if manifest else job.filename
    path=settings.EXPORT_ROOT/filename
    if path.parent!=settings.EXPORT_ROOT or not path.is_file(): raise Http404()
    return FileResponse(path.open('rb'),as_attachment=True,filename=filename)

@require_GET
def schema(request): return reply(json.loads(settings.SCHEMA_FILE.read_text()))

@auth()
@api
def observations(request,slug):
    p=get_object_or_404(m.Product,slug=slug,status='published')
    states=[s for s,_ in m.Observation.STATES]
    if request.method=='POST':
        d=body(request)
        if d.get('from_state') not in states or d.get('to_state') not in states: raise ValueError('Invalid observation state.')
        note=str(d.get('notes',''))[:500]
        m.Observation.objects.create(user=request.user,product=p,from_state=d['from_state'],to_state=d['to_state'],notes=note)
    elif request.method!='GET': return reply({'error':'Method not allowed.'},405)
    rows=m.Observation.objects.filter(user=request.user,product=p)
    counts={state:{other:0 for other in states} for state in states}
    for row in rows.values('from_state','to_state').annotate(n=Count('id')): counts[row['from_state']][row['to_state']]=row['n']
    matrix={state:{other:(n/sum(values.values()) if sum(values.values()) else None) for other,n in values.items()} for state,values in counts.items()}
    return reply({'states':states,'counts':counts,'transition_matrix':matrix,'row_observations':{state:sum(values.values()) for state,values in counts.items()},'unobserved_states':[state for state,values in counts.items() if not sum(values.values())],'observations':rows.count(),'scope':'Your own self-reports only. Empirical one-step frequencies; no causal inference, pharmacokinetic calibration or prediction. Unobserved rows are null.'})

@require_GET
@api
@public_cache(60)
def ingredient_detail(request,slug):
    ingredient=get_object_or_404(m.Ingredient,slug=slug)
    links=m.IngredientCompound.objects.filter(ingredient=ingredient).select_related('compound','source').prefetch_related('compound__studies__source','compound__mechanisms__source')
    return reply({'name':ingredient.name,'scientific_name':ingredient.scientific_name,'family':ingredient.family,'notes':ingredient.notes,'plant_part':ingredient.plant_part,'sensory_role':ingredient.sensory_role,'preparation':ingredient.preparation,'technical_notes':ingredient.technical_notes,'profile_source':source_data(ingredient.profile_source) if ingredient.profile_source_id else None,'compounds':[{'name':x.compound.name,'association':x.notes,'source':source_data(x.source),'studies':[{'title':s.title,'design':s.design,'population':s.population,'finding':s.finding,'limitation':s.limitation,'beverage_evidence':s.beverage_evidence,'source':source_data(s.source)} for s in x.compound.studies.all()],'mechanisms':[{'target':v.target,'action':v.action,'context':v.evidence_context,'limitation':v.limitation,'source':source_data(v.source)} for v in x.compound.mechanisms.all()]} for x in links],'exposure':'No finished-bottle concentration inferred from plant identity.'})

AROMA_TAGS=['floral','juniper','citrus','herbal','spicy','woody','smoky','fruity','vanilla','nutty','sweet','dry','bitter','smooth','warming']
def review_fields(data,rating,note):
    values={'rating':rating,'text':note,'approved':False}
    for key in ['aroma','taste','finish','value','design']:
        v=data.get(key)
        values[key]=None if v in [None,''] else int(v)
        if values[key] is not None and not 0<=values[key]<=5:raise ValueError('Dimension ratings must be between 0 and 5.')
    context=data.get('context','')
    if context not in ['', 'neat','ice','tonic','cocktail']:raise ValueError('Invalid tasting context.')
    tags=data.get('tags',[])
    if not isinstance(tags,list) or len(tags)>8 or any(t not in AROMA_TAGS for t in tags):raise ValueError('Choose up to eight supported aroma tags.')
    buy=data.get('buy_again')
    if buy not in [None,True,False,'','yes','no']:raise ValueError('Invalid purchase-again preference.')
    values.update(context=context,tags=list(dict.fromkeys(tags)),buy_again=True if buy in [True,'yes'] else False if buy in [False,'no'] else None)
    return values

@require_POST
@auth()
@api
def propose_photo(request,slug):
    product=get_object_or_404(m.Product,slug=slug,status='published')
    if request.POST.get('rights_confirmed')!='yes':raise ValueError('Confirm that you may share this photograph under the stated license.')
    photo=m.BottlePhoto(product=product,user=request.user,view=request.POST.get('view',''),photo=request.FILES.get('photo'),credit=request.POST.get('credit',''),license=request.POST.get('license',''),source_url=request.POST.get('source_url',''),caption=request.POST.get('caption',''))
    photo.full_clean();photo.save()
    return reply({'status':'pending','id':photo.id},201)


@require_GET
@api
@public_cache(60)
def discover(request):
    data=find(request.GET);groups=set(filter(None,request.GET.get('groups','').split(',')))
    items=[]
    for p in data.pop('objects'):
        indexed=indexed_ingredients(p);grouped={}
        for item in indexed.values():
            if item['group']:grouped.setdefault(item['group'],[]).append(item['name'])
        items.append({**card(p),'ingredient_groups':grouped,'matches':sorted(x['name'] for x in indexed.values() if x['group'] in groups),'indexed_ingredients':len(indexed)})
    return reply({**data,'items':items})
