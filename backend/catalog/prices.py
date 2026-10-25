"""Audited acceptance of explicit archival prices; no inferred identity or volume."""
from datetime import date
from decimal import Decimal
from django.db import transaction
from . import models as m
@transaction.atomic
def accept_price_capture(candidate,actor):
    candidate=m.DiscoveryCandidate.objects.select_for_update().get(pk=candidate.pk)
    if candidate.provider!='wayback' or candidate.status!='pending':raise ValueError('Choose a pending Wayback price candidate.')
    d=candidate.payload;p=candidate.resolved_product
    if not p or p.slug!=d['product'] or p.merged_into_id:raise ValueError('Confirm the canonical product before accepting a price.')
    amount=Decimal(d['amount']);abv=Decimal(d['abv']);volume=int(d['volume_ml'])
    if not 0<amount<1000000 or not 0<abv<=100 or not 1<=volume<=30000:raise ValueError('Price or bottling is outside accepted bounds.')
    if d['currency']!='GBP' or d['country']!='United Kingdom' or not d['source_url'].startswith('https://web.archive.org/web/'):raise ValueError('Unsupported archived-price provenance.')
    source=m.Source.objects.create(title=d['title'][:180]+' — archived retailer price',url=d['source_url'],publisher='The Whisky Exchange / Internet Archive',kind='secondary',accessed_on=date.today(),license_note='Parsed price facts only. Original archived text and images retain their rights. SHA-256 '+d['content_sha256'])
    variant,_=m.Variant.objects.get_or_create(product=p,name=f'Archive reference · {volume} ml / {abv}%',market='United Kingdom archive',volume_ml=volume,defaults={'abv':abv,'source':source})
    if variant.abv!=abv:raise ValueError('Existing reference has another strength; review the candidate.')
    price,created=m.PriceObservation.objects.get_or_create(variant=variant,observed_on=d['observed_on'],retailer=d['retailer'],currency='GBP',country=d['country'],defaults={'amount':amount,'source':source,'tax_included':True,'notes':'Archive capture, not a transaction. '+d['date_scope']+' Content SHA-256 '+d['content_sha256']})
    if not created:source.delete()
    candidate.status='accepted';candidate.save()
    m.Audit.objects.create(actor=actor,action='price.archive.accepted',target=str(price.id),detail={'candidate':str(candidate.id),'created':created})
    return price
