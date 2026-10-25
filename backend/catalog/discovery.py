"""Explainable catalogue navigation. Documentation coverage is not product quality."""
import math
from django.db.models import Exists,OuterRef,F,IntegerField,Q,Count,Case,When,Value,Prefetch
from django.db.models.functions import Cast
from . import models as m

AREAS=[('bottlings','Bottling specifications'),('ingredients','Source-linked ingredients'),('history','Attributed history'),('origin','Sourced locality'),('photo','Reference photograph'),('prices','Dated price observations')]

def with_coverage(qs):
    flags={
      'bottlings':Exists(m.Variant.objects.filter(product=OuterRef('pk'))),
      'ingredients':Exists(m.RecipeIngredient.objects.filter(recipe__product=OuterRef('pk'))),
      'history':Case(When(~Q(history='')&Q(history_source__isnull=False),then=Value(True)),default=Value(False)),
      'origin':Case(When(place__isnull=False,then=Value(True)),default=Value(False)),
      'photo':Exists(m.BottleAsset.objects.filter(product=OuterRef('pk'),view='front'))|Exists(m.BottlePhoto.objects.filter(product=OuterRef('pk'),view='front',approved=True)),
      'prices':Exists(m.PriceObservation.objects.filter(variant__product=OuterRef('pk'))),
    }
    qs=qs.annotate(**{'covered_'+k:v for k,v in flags.items()})
    # An editorially uploaded product photograph also satisfies the photo area.
    qs=qs.annotate(covered_photo=Case(When(~Q(photo=''),then=Value(True)),default=F('covered_photo')))
    score=sum((Cast(F('covered_'+k),IntegerField()) for k,_ in AREAS),Value(0))
    return qs.annotate(documented_areas=score).prefetch_related(Prefetch('community_photos',queryset=m.BottlePhoto.objects.filter(approved=True,view='front').order_by('id')[:1],to_attr='approved_fronts'))

def coverage(p):
    areas=[{'key':k,'label':label,'documented':bool(getattr(p,'covered_'+k))} for k,label in AREAS]
    return {'documented':sum(x['documented'] for x in areas),'total':len(areas),'areas':areas,'notice':'Coverage describes this record, not the quality or safety of the spirit.'}

def public_objects():
    return with_coverage(m.Product.objects.filter(status='published',edition_of__isnull=True,merged_into__isnull=True)).select_related('brand','place__source','history_source','edition_of','merged_into').prefetch_related('variants__source','assets','editions','recipes__ingredients__ingredient')

def ingredients(p):
    return {x.ingredient.slug:{'name':x.ingredient.name,'group':x.ingredient.navigation_group,'certainty':x.certainty} for r in p.recipes.all() for x in r.ingredients.all()}

def find(params):
    qs=public_objects();q=params.get('q','').strip()[:120]
    if q:qs=qs.filter(Q(name__icontains=q)|Q(brand__name__icontains=q)|Q(recipes__ingredients__ingredient__name__icontains=q)).distinct()
    if params.get('category'):qs=qs.filter(category=params['category'][:40])
    if params.get('country'):qs=qs.filter(brand__country=params['country'][:80])
    groups=list(dict.fromkeys(filter(None,params.get('groups','').split(','))))
    if any(g not in dict(m.NAVIGATION_GROUPS) for g in groups):raise ValueError('Choose a supported ingredient group.')
    strength={}
    for key,lookup in [('min_abv','gte'),('max_abv','lte')]:
        if params.get(key):
            value=float(params[key])
            if not math.isfinite(value) or not 0<=value<=100:raise ValueError('Strength must be between 0 and 100.')
            strength['variants__abv__'+lookup]=value
    if strength.get('variants__abv__gte',0)>strength.get('variants__abv__lte',100):raise ValueError('Minimum strength exceeds maximum strength.')
    if strength:qs=qs.filter(**strength).distinct()
    minimum=int(params.get('coverage','0'))
    if not 0<=minimum<=6:raise ValueError('Documentation coverage must be between 0 and 6.')
    qs=qs.filter(documented_areas__gte=minimum)
    if params.get('photo')=='1':qs=qs.filter(covered_photo=True)
    facet_rows=m.RecipeIngredient.objects.filter(recipe__product__in=qs.values('pk')).exclude(ingredient__navigation_group='').values('ingredient__navigation_group').annotate(count=Count('recipe__product',distinct=True))
    counts={x['ingredient__navigation_group']:x['count'] for x in facet_rows}
    if groups:qs=qs.filter(recipes__ingredients__ingredient__navigation_group__in=groups).distinct()
    order=params.get('sort','documented')
    if order not in ['documented','name']:raise ValueError('Choose documented or name ordering.')
    total=qs.count();page=max(1,min(int(params.get('page','1')),1000));limit=max(1,min(int(params.get('limit','12')),24))
    page=min(page,max(1,math.ceil(total/limit)))
    ordered=qs.order_by(*(['-documented_areas','brand__name','name','slug'] if order=='documented' else ['brand__name','name','slug']))
    return {'objects':list(ordered[(page-1)*limit:page*limit]),'total':total,'page':page,'pages':math.ceil(total/limit),'groups':[{'key':k,'label':v,'count':counts.get(k,0)} for k,v in m.NAVIGATION_GROUPS],'notice':'Ingredient groups navigate disclosed records. They are not tasting notes, allergen guarantees or predictions of effects.'}

def related(p,limit=3):
    indexed=ingredients(p);ids=list(indexed)
    qs=public_objects().filter(category=p.category).exclude(pk=p.pk)
    shared=Count('recipes__ingredients__ingredient',filter=Q(recipes__ingredients__ingredient__slug__in=ids),distinct=True)
    candidates=list(qs.annotate(shared_count=shared).order_by('-shared_count','-documented_areas','brand__name','slug')[:limit])
    return [(x,sorted(v['name'] for slug,v in ingredients(x).items() if slug in indexed)) for x in candidates]
