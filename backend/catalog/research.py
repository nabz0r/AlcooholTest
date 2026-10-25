"""Editorial coverage of actual photographs and dated observations, never inferred years."""
from collections import defaultdict
from datetime import date
from django.db import transaction
from django.utils import timezone
from . import models as m
from .price_dates import price_bounds,price_label,conservative_span,comparable_basis

@transaction.atomic
def queue_targets(queryset,actor):
    queued=0
    for target in queryset.select_for_update().filter(enabled=True,product__merged_into__isnull=True).order_by('pk'):
        params={'target_id':str(target.pk)}
        if m.Job.objects.filter(kind='prices',status__in=['queued','running'],parameters=params).exists():continue
        job=m.Job.objects.create(kind='prices',created_by=actor,parameters=params)
        m.Audit.objects.create(actor=actor,action='price.archive.queued',target=str(job.pk),detail={'target':str(target.pk),'product':str(target.product_id)})
        queued+=1
    return queued

def coverage_rows(queryset=None):
    today=timezone.localdate();start_year=today.year-20
    qs=queryset if queryset is not None else m.Product.objects.filter(status='published',edition_of__isnull=True,merged_into__isnull=True)
    qs=qs.select_related('brand','research_plan').prefetch_related('assets','community_photos','external_photo_references','variants__prices','price_archive_targets')
    rows=[]
    for p in qs.order_by('brand__name','name'):
        assets=list(p.assets.all())+[a for a in p.community_photos.all() if a.approved]
        references=[x for x in p.external_photo_references.all() if x.verified]
        prices=[price for v in p.variants.all() for price in v.prices.all()]
        dated=sorted(prices,key=price_bounds)
        research=getattr(p,'research_plan',None);launch=(research.first_release_year or research.release_not_before_year) if research else None
        expected=list(range(max(start_year,launch or start_year),today.year+1))
        valid=[price for price in dated if not launch or price_bounds(price)[0].year>=launch]
        years={price_bounds(price)[0].year for price in valid};groups=defaultdict(list)
        for price in prices:
            if launch and price_bounds(price)[0].year<launch:continue
            category=comparable_basis(price.basis)
            if category and price.tax_included is not None:groups[(price.variant_id,price.currency,price.country,price.retailer,category,price.tax_included)].append(price)
        spans=[conservative_span(records) for records in groups.values()]
        evidence_span=conservative_span(valid)
        earliest=dated[0] if dated else None;latest=max(dated,key=lambda price:price_bounds(price)[1]) if dated else None
        rows.append({'evidence_span_years':round(evidence_span,1),'twenty_year_evidence':evidence_span>=20,'front_references':[x for x in references if x.view=='front'],'back_references':[x for x in references if x.view=='back'],'product':p,'front':bool(p.photo) or any(a.view=='front' for a in assets),'back':any(a.view=='back' for a in assets),'prices':len(prices),'earliest':price_label(earliest) if earliest else None,'latest':price_label(latest) if latest else None,'earliest_label':price_label(earliest) if earliest else None,'latest_label':price_label(latest) if latest else None,'earliest_precision':earliest.date_precision if earliest else None,'latest_precision':latest.date_precision if latest else None,'span_method':'Conservative elapsed time: earliest source month may end on its final day; latest source month may begin on its first day. Internal bounds are not asserted observation dates.','years':[{'year':year,'present':year in years} for year in expected],'missing_years':[year for year in expected if year not in years],'covered_years':len(years.intersection(expected)),'expected_years':len(expected),'comparable_span_years':round(max(spans,default=0),1),'twenty_year_series':max(spans,default=0)>=20,'prelaunch_observations':sum(price_bounds(price)[0].year<launch for price in dated) if launch else 0,'launch_year':launch,'research':research,'targets':list(p.price_archive_targets.all())})
    return rows
