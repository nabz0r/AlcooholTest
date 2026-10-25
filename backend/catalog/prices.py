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
    import re,urllib.parse
    archive=urllib.parse.urlparse(d['source_url']);match=re.fullmatch(r'/web/(\d{14})/(https?://.+)',archive.path)
    original=urllib.parse.urlparse(d.get('original_url',''))
    if d['currency']!='GBP' or d['country']!='United Kingdom' or archive.scheme!='https' or archive.hostname!='web.archive.org' or not match or original.hostname not in ['www.thewhiskyexchange.com','thewhiskyexchange.com','www.thedrinkshop.com','thedrinkshop.com'] or match.group(1)!=d['timestamp'] or match.group(2)+('?' + archive.query if archive.query else '')!=d['original_url']:raise ValueError('Unsupported archived-price provenance.')
    if not re.fullmatch(r'[0-9a-f]{64}',d['content_sha256']):raise ValueError('A valid source content fingerprint is required.')
    expected_date=date(int(d['timestamp'][:4]),int(d['timestamp'][4:6]),int(d['timestamp'][6:8]))
    if expected_date.isoformat()!=d['observed_on']:raise ValueError('Capture date does not match the observation date.')
    if d.get('parser')=='drinkshop_primary_price_table':
        target=m.PriceArchiveTarget.objects.filter(product=p,retailer_id=d['retailer_id'],drinkshop_id=d.get('source_retailer_id'),drinkshop_volume_ml=volume).first()
        if not target or original.hostname not in ['www.thedrinkshop.com','thedrinkshop.com'] or original.path!='/products/nlpdetail.php' or urllib.parse.parse_qs(original.query)!={'prodid':[str(target.drinkshop_id)]} or d['title'].casefold() not in [t.casefold() for t in target.drinkshop_titles]:raise ValueError('Confirm this exact DrinkShop product, title and bottle row before acceptance.')
        rule=target.review_rules.get('drinkshop',{})
        if any(abv==Decimal(str(v)) for v in rule.get('blocked_abv',[])):raise ValueError(rule.get('reason','This historical strength needs independent editorial verification.'))
    elif d.get('parser')=='actinic_catalogue_row':
        target=m.PriceArchiveTarget.objects.filter(product=p,retailer_id=d['retailer_id'],legacy_ref=d.get('legacy_product_ref','')).first()
        if not target or original.hostname not in ['www.thewhiskyexchange.com','thewhiskyexchange.com'] or urllib.parse.urlparse(target.legacy_url).path!=original.path:raise ValueError('Confirm the exact legacy product reference in the archive target before acceptance.')
    elif original.hostname not in ['www.thewhiskyexchange.com','thewhiskyexchange.com'] or not re.match(rf'^/(?:[Pp]-{int(d["retailer_id"])}\.aspx$|[Pp]/{int(d["retailer_id"])}/)',original.path):raise ValueError('Original price URL belongs to another product.')
    research=getattr(p,'research_plan',None)
    earliest=(research.first_release_year or research.release_not_before_year) if research else None
    if earliest and expected_date.year<earliest:raise ValueError('This capture predates the documented expression launch or earliest possible year; review identity.')
    if d['retailer']!=('TheDrinkShop.com' if d.get('parser')=='drinkshop_primary_price_table' else 'The Whisky Exchange'):raise ValueError('Retailer label does not match the archived source.')
    source=m.Source.objects.create(title=d['title'][:180]+' — archived retailer price',url=d['source_url'],publisher=d['retailer']+' / Internet Archive',kind='secondary',accessed_on=date.today(),license_note='Parsed price facts only. Original archived text and images retain their rights. SHA-256 '+d['content_sha256'])
    abv_text=format(abv.normalize(),'f')
    variant,_=m.Variant.objects.get_or_create(product=p,name=f'Archive reference · {volume} ml / {abv_text}%',market='United Kingdom archive',volume_ml=volume,defaults={'abv':abv,'source':source})
    if variant.abv!=abv:raise ValueError('Existing reference has another strength; review the candidate.')
    price,created=m.PriceObservation.objects.get_or_create(variant=variant,observed_on=d['observed_on'],retailer=d['retailer'],currency='GBP',country=d['country'],defaults={'amount':amount,'source':source,'basis':'archive_capture','tax_included':d.get('tax_included'),'notes':'Archive capture, not a transaction. '+d['date_scope']+' Content SHA-256 '+d['content_sha256']})
    if not created:
        if price.amount!=amount or price.tax_included!=d.get('tax_included'):raise ValueError('A different price already exists for this bottling, seller and date. Review the conflict manually.')
        source.delete()
    candidate.status='accepted';candidate.save()
    m.Audit.objects.create(actor=actor,action='price.archive.accepted',target=str(price.id),detail={'candidate':str(candidate.id),'created':created})
    return price
