from django.contrib import admin,messages
from django.db import transaction
from django.utils.text import slugify
from . import models as m
from .views import clean_submission

class AuditedAdmin(admin.ModelAdmin):
    list_per_page=40
    def save_model(self,request,obj,form,change):
        super().save_model(request,obj,form,change)
        m.Audit.objects.create(actor=request.user,action='admin.update' if change else 'admin.create',target=f'{obj._meta.label}:{obj.pk}',detail={'fields':list(form.changed_data)})
    def delete_model(self,request,obj):
        m.Audit.objects.create(actor=request.user,action='admin.delete',target=f'{obj._meta.label}:{obj.pk}')
        super().delete_model(request,obj)
    def delete_queryset(self,request,queryset):
        for obj in queryset: m.Audit.objects.create(actor=request.user,action='admin.delete',target=f'{obj._meta.label}:{obj.pk}')
        super().delete_queryset(request,queryset)

class VariantInline(admin.TabularInline): model=m.Variant; extra=0; autocomplete_fields=['source']
class RecipeInline(admin.TabularInline): model=m.Recipe; extra=0; autocomplete_fields=['source']
class RecipeIngredientInline(admin.TabularInline): model=m.RecipeIngredient; extra=0; autocomplete_fields=['ingredient','source']
@admin.register(m.Product)
class ProductAdmin(AuditedAdmin):
    def get_urls(self):
        from django.urls import path
        return [path('<uuid:object_id>/merge/',self.admin_site.admin_view(self.merge_view),name='catalog_product_merge')]+super().get_urls()
    def merge_view(self,request,object_id):
        from django import forms
        from django.shortcuts import get_object_or_404,redirect
        from django.template.response import TemplateResponse
        from django.core.exceptions import PermissionDenied,ValidationError
        from .duplicates import preview,merge
        original=get_object_or_404(m.Product,pk=object_id)
        if not self.has_change_permission(request,original):raise PermissionDenied
        class MergeForm(forms.Form):
            target=forms.ModelChoiceField(queryset=m.Product.objects.filter(brand=original.brand,status='published',merged_into__isnull=True,edition_of__isnull=True).exclude(pk=original.pk),label='Keep this canonical product')
        form=MergeForm(request.POST or None);report=None
        if request.method=='POST' and form.is_valid():
            try:
                report=preview(original,form.cleaned_data['target'])
                if request.POST.get('confirm')=='yes':
                    merge(original,form.cleaned_data['target'],request.user)
                    self.message_user(request,'Duplicate archived and relationships reconciled. Review retained conflicts in the audit log.')
                    return redirect('admin:catalog_product_change',form.cleaned_data['target'].pk)
            except ValidationError as exc:form.add_error(None,exc)
        return TemplateResponse(request,'admin/catalog/product/merge.html',{**self.admin_site.each_context(request),'form':form,'original':original,'preview':report,'opts':self.model._meta,'title':'Resolve duplicate'})

    list_display=['name','brand','status','disclosure','updated_at']; list_filter=['status','disclosure','category','brand']; search_fields=['name','slug','brand__name']; autocomplete_fields=['brand','place','edition_of','history_source']; inlines=[VariantInline,RecipeInline]
@admin.register(m.Recipe)
class RecipeAdmin(AuditedAdmin):
    list_display=['product','version','declared_count']; search_fields=['product__name','version']; autocomplete_fields=['product','source']; inlines=[RecipeIngredientInline]
@admin.register(m.Brand)
class BrandAdmin(AuditedAdmin): search_fields=['name','slug']; list_display=['name','country']
@admin.register(m.Source)
class SourceAdmin(AuditedAdmin): search_fields=['title','publisher','url']; list_display=['title','kind','accessed_on']; list_filter=['kind']
@admin.register(m.Ingredient)
class IngredientAdmin(AuditedAdmin): search_fields=['name','slug','scientific_name']; list_display=['name','scientific_name','family']; list_filter=['family']
@admin.register(m.Compound)
class CompoundAdmin(AuditedAdmin): search_fields=['name','cas']; list_display=['name','cas']

@admin.action(description='Accept into catalogue as DRAFT (review sources before publishing)')
def accept_submissions(modeladmin,request,queryset):
    from datetime import date
    for item in queryset:
        with transaction.atomic():
            item=m.Submission.objects.select_for_update().get(pk=item.pk)
            if item.status!='pending': continue
            d=clean_submission(item.payload)
            suffix=str(item.id)[:8]
            brand,_=m.Brand.objects.get_or_create(slug=slugify(d['brand'])[:45],defaults={'name':d['brand'],'country':d['country'],'website':d['source_url']})
            src=m.Source.objects.create(title=f'Contributor reference: {d["name"]}',url=d['source_url'],publisher='Contributor supplied; editorial verification required',kind='secondary',accessed_on=date.today())
            product=m.Product.objects.create(slug=f'{slugify(d["brand"]+"-"+d["name"])[:40]}-{suffix}',brand=brand,name=d['name'],category=d['category'],description=d['description'],status='draft',disclosure='partial')
            m.Variant.objects.create(product=product,name='Contributor edition',market=d['market'],abv=d['abv'],volume_ml=d['volume_ml'],source=src)
            recipe=m.Recipe.objects.create(product=product,version='Contributor proposal',source=src,notes='Unverified submission. Confirm each ingredient before publication.')
            for name in [x.strip() for x in d['ingredients'].split(',') if x.strip() and x.strip().lower() not in ['unknown','not disclosed']][:100]:
                ingredient,_=m.Ingredient.objects.get_or_create(slug=slugify(name)[:50],defaults={'name':name[:120]})
                m.RecipeIngredient.objects.get_or_create(recipe=recipe,ingredient=ingredient,defaults={'source':src,'certainty':'reported','stage':'unspecified'})
            item.status='approved'; item.reviewed_by=request.user; item.save()
            m.Audit.objects.create(actor=request.user,action='submission.accepted_as_draft',target=str(item.id),detail={'product':str(product.id)})
    modeladmin.message_user(request,'Proposals converted to drafts. Verify citations and publish through Products.',messages.SUCCESS)
@admin.action(description='Reject selected pending proposals')
def reject_submissions(modeladmin,request,queryset):
    for item in queryset.filter(status='pending'):
        item.status='rejected'; item.reviewed_by=request.user; item.save()
        m.Audit.objects.create(actor=request.user,action='submission.rejected',target=str(item.id))
@admin.register(m.Submission)
class SubmissionAdmin(AuditedAdmin):
    list_display=['id','user','status','created_at']; list_filter=['status']; readonly_fields=['user','payload','status','created_at','reviewed_by']; actions=[accept_submissions,reject_submissions]
    def has_add_permission(self,request): return False
@admin.action(description='Publish selected tasting notes')
def approve_reviews(modeladmin,request,queryset):
    for review in queryset:
        review.approved=True; review.save(); m.Audit.objects.create(actor=request.user,action='review.approved',target=str(review.id))
@admin.register(m.Review)
class ReviewAdmin(AuditedAdmin): list_display=['product','user','rating','approved']; list_filter=['approved']; actions=[approve_reviews]; autocomplete_fields=['product']; search_fields=['text','user__username']
@admin.register(m.Job)
class JobAdmin(admin.ModelAdmin):
    list_display=['id','kind','status','created_at']; list_filter=['status','kind']; readonly_fields=[f.name for f in m.Job._meta.fields]
    def has_add_permission(self,r): return False
    def has_delete_permission(self,r,obj=None): return False
@admin.register(m.Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display=['created_at','actor','action','target']; readonly_fields=[f.name for f in m.Audit._meta.fields]; search_fields=['action','target']
    def has_add_permission(self,r): return False
    def has_delete_permission(self,r,obj=None): return False
for model in [m.Variant,m.RecipeIngredient,m.IngredientCompound,m.Study,m.Measurement,m.Collection]: admin.site.register(model,AuditedAdmin)

@admin.register(m.Place)
class PlaceAdmin(AuditedAdmin):
    search_fields=['name','region','country'];list_display=['name','region','country'];autocomplete_fields=['source']
@admin.register(m.BottleAsset)
class BottleAssetAdmin(AuditedAdmin):
    list_display=['product','license','author'];search_fields=['product__name','author'];autocomplete_fields=['product']

for model in [m.Mechanism,m.CriticReview,m.Observation]: admin.site.register(model,AuditedAdmin)

@admin.action(description='Accept selected Wikidata candidates as editorial drafts')
def accept_candidates(modeladmin,request,queryset):
    from datetime import date
    from django.utils.text import slugify
    for c in queryset.filter(provider='wikidata',status='pending'):
        with transaction.atomic():
            c=m.DiscoveryCandidate.objects.select_for_update().get(pk=c.pk)
            if c.resolved_product_id:
                c.status='accepted';c.save();m.Audit.objects.create(actor=request.user,action='candidate.linked_existing',target=str(c.id),detail={'product':str(c.resolved_product_id)})
                continue
            src=m.Source.objects.create(title='Wikidata candidate: '+c.label[:180],url=c.source_url,publisher='Wikidata contributors',kind='secondary',accessed_on=date.today(),license_note='CC0 structured data; unverified discovery candidate.')
            brand,_=m.Brand.objects.get_or_create(slug='discovered-'+c.external_id.lower(),defaults={'name':c.label[:120],'country':'Unverified','website':c.source_url})
            p,_=m.Product.objects.get_or_create(slug='discovered-'+c.external_id.lower(),defaults={'brand':brand,'name':c.label[:160],'category':c.category,'description':'Discovered public record. Verify brand, product identity, bottling and sources before publication.','status':'draft','disclosure':'unknown'})
            if c.image_path and not p.photo:
                p.photo=c.image_path;p.photo_credit=c.image_metadata.get('author','See source');p.photo_license=c.image_metadata.get('license','')+' — '+c.image_metadata.get('license_url','');p.save()
            c.status='accepted';c.save();m.Audit.objects.create(actor=request.user,action='candidate.accepted_as_draft',target=str(c.id),detail={'product':str(p.id)})
    modeladmin.message_user(request,'Drafts created. Verify the candidate image and product identity; no strength or formula was invented.')
@admin.register(m.DiscoveryCandidate)
class CandidateAdmin(AuditedAdmin):
    list_display=['label','provider','category','status','updated_at'];list_filter=['provider','category','status'];search_fields=['label','external_id'];readonly_fields=['payload','image_metadata'];autocomplete_fields=['resolved_product'];actions=[accept_candidates]
@admin.register(m.DiscoveryCursor)
class CursorAdmin(admin.ModelAdmin):
    list_display=['key','cursor','exhausted','updated_at'];readonly_fields=['updated_at']

admin.site.register(m.PriceObservation,AuditedAdmin)
