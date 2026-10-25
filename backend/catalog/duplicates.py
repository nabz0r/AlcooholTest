"""Conservative, audited canonical-product merge. No destructive cascades."""
from django.db import transaction
from django.core.exceptions import ValidationError
from . import models as m

def preview(source,target):
    if source.pk==target.pk or source.brand_id!=target.brand_id or target.status!='published' or target.merged_into_id or target.edition_of_id:
        raise ValidationError('Choose a different published canonical product of the same brand.')
    if source.edition_of_id:raise ValidationError('This is an edition. Verify identity and detach the edition relationship before merging a true duplicate.')
    return {name:getattr(source,name).count() for name in ['variants','recipes','assets','editions','discovery_occurrences']}

@transaction.atomic
def merge(source,target,actor):
    locked={p.pk:p for p in m.Product.objects.select_for_update().filter(pk__in=[source.pk,target.pk]).order_by('pk')}
    source,target=locked[source.pk],locked[target.pk];counts=preview(source,target)
    if source.merged_into_id:raise ValidationError('This occurrence is already merged.')
    moved={};retained={}
    for model,field,unique in [(m.Variant,'product',['name','market','volume_ml']),(m.Recipe,'product',['version']),(m.BottleAsset,'product',['local_path']),(m.Review,'product',['user_id']),(m.Collection,'product',['user_id'])]:
        moved[model.__name__]=[];retained[model.__name__]=[]
        for obj in model.objects.select_for_update().filter(product=source):
            criteria={k:getattr(obj,k) for k in unique}
            if model.objects.filter(product=target,**criteria).exists():
                retained[model.__name__].append(str(obj.pk));continue
            obj.product=target;obj.save();moved[model.__name__].append(str(obj.pk))
    for model,field in [(m.Observation,'product'),(m.CriticReview,'product'),(m.DiscoveryCandidate,'resolved_product'),(m.Product,'edition_of')]:
        rows=model.objects.filter(**{field:source});moved[model.__name__+':'+field]=list(map(str,rows.values_list('pk',flat=True)));rows.update(**{field:target})
    source.status='archived';source.merged_into=target;source.save()
    m.Audit.objects.create(actor=actor,action='product.merged',target=str(source.pk),detail={'canonical':str(target.pk),'counts':counts,'moved':moved,'conflicting_records_retained_on_archived_source':retained,'source_photo_retained':bool(source.photo)})
    return counts
