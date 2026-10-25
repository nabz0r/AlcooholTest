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
    def save_formset(self,request,form,formset,change):
        instances=formset.save(commit=False)
        for obj in formset.deleted_objects:
            m.Audit.objects.create(actor=request.user,action='admin.inline.delete',target=f'{obj._meta.label}:{obj.pk}')
            obj.delete()
        for obj in instances:
            obj.save()
            m.Audit.objects.create(actor=request.user,action='admin.inline.save',target=f'{obj._meta.label}:{obj.pk}',detail={'parent':str(form.instance.pk)})
        formset.save_m2m()
    def delete_model(self,request,obj):
        m.Audit.objects.create(actor=request.user,action='admin.delete',target=f'{obj._meta.label}:{obj.pk}')
        super().delete_model(request,obj)
    def delete_queryset(self,request,queryset):
        for obj in queryset: m.Audit.objects.create(actor=request.user,action='admin.delete',target=f'{obj._meta.label}:{obj.pk}')
        super().delete_queryset(request,queryset)

class VariantInline(admin.TabularInline): model=m.Variant; extra=0; show_change_link=True; autocomplete_fields=['source']
class RecipeInline(admin.TabularInline): model=m.Recipe; extra=0; show_change_link=True; autocomplete_fields=['source']
class RecipeIngredientInline(admin.TabularInline): model=m.RecipeIngredient; extra=0; autocomplete_fields=['ingredient','source']
class AssetInline(admin.StackedInline):
    model=m.BottleAsset;extra=0;show_change_link=True
class CriticInline(admin.StackedInline):
    model=m.CriticReview;extra=0;autocomplete_fields=['source'];show_change_link=True
class PackagingInline(admin.StackedInline):
    model=m.BottlePhoto;extra=0;exclude=['user'];show_change_link=True

class ArchiveTargetInline(admin.StackedInline):
    model=m.PriceArchiveTarget;extra=0;show_change_link=True;readonly_fields=['last_checked','last_result']
class ExternalPhotoInline(admin.StackedInline):
    model=m.ExternalPhotoReference;extra=0;show_change_link=True
class ResearchInline(admin.StackedInline):
    model=m.ProductResearch;extra=0;max_num=1

@admin.register(m.Product)
class ProductAdmin(AuditedAdmin):
    def get_urls(self):
        from django.urls import path
        return [path('research/',self.admin_site.admin_view(self.research_view),name='catalog_product_research'),path('dossiers/',self.admin_site.admin_view(self.dossier_view),name='catalog_product_dossiers'),path('<uuid:object_id>/merge/',self.admin_site.admin_view(self.merge_view),name='catalog_product_merge')]+super().get_urls()
    def research_view(self,request):
        from django.core.exceptions import PermissionDenied
        from django.template.response import TemplateResponse
        from django.http import JsonResponse,HttpResponseRedirect
        from django.urls import reverse
        from .research import coverage_rows,queue_targets
        if not self.has_view_permission(request):raise PermissionDenied
        if request.method=='POST':
            if not self.has_change_permission(request) or not request.user.has_perm('catalog.add_job'):raise PermissionDenied
            target_id=request.POST.get('target_id')
            targets=m.PriceArchiveTarget.objects.all()
            if target_id:
                import uuid
                try:target_id=uuid.UUID(target_id)
                except ValueError:raise PermissionDenied
                targets=targets.filter(pk=target_id)
            elif request.POST.get('scope')!='all':raise PermissionDenied
            count=queue_targets(targets,request.user)
            self.message_user(request,f'{count} archival collection jobs queued. Results require editorial acceptance; existing running/queued targets were skipped.')
            return HttpResponseRedirect(reverse('admin:catalog_product_research'))
        rows=coverage_rows();total=len(rows)
        if request.GET.get('format')=='json':
            data=[]
            for row in rows:
                data.append({**{k:v for k,v in row.items() if k not in ['product','research','targets','front_references','back_references']},'product':row['product'].slug,'external_references':[{'view':x.view,'source_page':x.source_page,'image_url':x.image_url,'rights_note':x.rights_note,'edition_note':x.edition_note,'verified_on':x.verified_on} for x in row['front_references']+row['back_references']],'launch_source_url':row['research'].release_source_url if row['research'] else '', 'research_notes':row['research'].notes if row['research'] else '', 'targets':[{**t.as_target(),'id':str(t.pk),'enabled':t.enabled,'source_url':t.source_url,'last_checked':t.last_checked,'last_result':t.last_result} for t in row['targets']]})
            response=JsonResponse({'scope':'Actual photograph presence and dated observations. Annual coverage across formats is descriptive; comparable spans are grouped by variant, retailer, currency, country and tax basis.','rows':data})
            response['Content-Disposition']='attachment; filename="atlas-research-coverage.json"';return response
        selected=request.GET.get('missing','')
        if selected in ['front','back']:rows=[r for r in rows if not r[selected]]
        elif selected=='twenty':rows=[r for r in rows if not r['twenty_year_evidence']]
        elif selected=='targets':rows=[r for r in rows if not any(t.enabled for t in r['targets'])]
        return TemplateResponse(request,'admin/catalog/product/research.html',{**self.admin_site.each_context(request),'opts':self.model._meta,'title':'Photographs & price archives','rows':rows,'total':total,'selected':selected,'can_queue':self.has_change_permission(request) and request.user.has_perm('catalog.add_job')})

    def dossier_view(self,request):
        from django.core.exceptions import PermissionDenied
        from django.template.response import TemplateResponse
        from .editorial import dossier_rows,CHECKS
        if not self.has_view_permission(request):raise PermissionDenied
        rows=dossier_rows();total=len(rows);complete=sum(r['complete'] for r in rows)
        missing=request.GET.get('missing','')
        if missing in dict(CHECKS):rows=[r for r in rows if missing in r['missing']]
        elif missing=='any':rows=[r for r in rows if not r['complete']]
        return TemplateResponse(request,'admin/catalog/product/dossiers.html',{**self.admin_site.each_context(request),'opts':self.model._meta,'title':'Catalogue dossier workbench','rows':rows,'checks':CHECKS,'selected':missing,'total':total,'complete':complete})
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

    list_display=['name','brand','status','disclosure','updated_at']; list_filter=['status','disclosure','category','brand']; search_fields=['name','slug','brand__name']; autocomplete_fields=['brand','place','edition_of','history_source']; inlines=[VariantInline,RecipeInline,CriticInline,PackagingInline,AssetInline,ExternalPhotoInline,ResearchInline,ArchiveTargetInline]
@admin.register(m.Recipe)
class RecipeAdmin(AuditedAdmin):
    list_display=['product','version','declared_count']; search_fields=['product__name','version']; autocomplete_fields=['product','source']; inlines=[RecipeIngredientInline]
@admin.register(m.Brand)
class BrandAdmin(AuditedAdmin): search_fields=['name','slug']; list_display=['name','country']
@admin.register(m.Source)
class SourceAdmin(AuditedAdmin):
    search_fields=['title','publisher','url'];list_display=['title','kind','accessed_on','memento_link'];list_filter=['kind'];readonly_fields=['memento_link']
    def get_urls(self):
        from django.urls import path
        from .memento import staff_memento
        return [path('memento/',self.admin_site.admin_view(staff_memento),name='catalog_source_memento'),path('<uuid:source_id>/memento/',self.admin_site.admin_view(staff_memento),name='catalog_source_item_memento')]+super().get_urls()
    @admin.display(description='Source Memento')
    def memento_link(self,obj):
        from django.urls import reverse
        from django.utils.html import format_html
        return format_html('<a href="{}">Open preserved facts ↗</a>',reverse('admin:catalog_source_item_memento',args=[obj.pk])) if obj.pk else 'Save this source first.'
@admin.register(m.Ingredient)
class IngredientAdmin(AuditedAdmin): search_fields=['name','slug','scientific_name']; list_display=['name','scientific_name','family','navigation_group']; list_filter=['navigation_group','family']; autocomplete_fields=['profile_source']
@admin.register(m.Compound)
class CompoundAdmin(AuditedAdmin): search_fields=['name','cas']; list_display=['name','cas']

@admin.action(description='Accept into catalogue as DRAFT (review sources before publishing)',permissions=['change'])
def accept_submissions(modeladmin,request,queryset):
    from django.core.exceptions import PermissionDenied
    if not request.user.has_perm('catalog.change_submission') or not request.user.has_perm('catalog.add_product'):raise PermissionDenied
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
@admin.action(description='Reject selected pending proposals',permissions=['change'])
def reject_submissions(modeladmin,request,queryset):
    from django.core.exceptions import PermissionDenied
    if not request.user.has_perm('catalog.change_submission'):raise PermissionDenied
    for item in queryset.filter(status='pending'):
        item.status='rejected'; item.reviewed_by=request.user; item.save()
        m.Audit.objects.create(actor=request.user,action='submission.rejected',target=str(item.id))
@admin.register(m.Submission)
class SubmissionAdmin(AuditedAdmin):
    list_display=['id','user','status','created_at']; list_filter=['status']; readonly_fields=['user','payload','status','created_at','reviewed_by']; actions=[accept_submissions,reject_submissions]
    def has_add_permission(self,request): return False
@admin.action(description='Publish selected tasting notes',permissions=['change'])
def approve_reviews(modeladmin,request,queryset):
    from django.core.exceptions import PermissionDenied
    if not request.user.has_perm('catalog.change_review'):raise PermissionDenied
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
for model in [m.RecipeIngredient,m.IngredientCompound,m.Study,m.Measurement,m.Collection]: admin.site.register(model,AuditedAdmin)

@admin.register(m.Place)
class PlaceAdmin(AuditedAdmin):
    search_fields=['name','region','country'];list_display=['name','region','country'];autocomplete_fields=['source']
@admin.register(m.BottleAsset)
class BottleAssetAdmin(AuditedAdmin):
    list_display=['product','view','license','author'];search_fields=['product__name','author'];autocomplete_fields=['product']

for model in [m.Mechanism,m.CriticReview,m.Observation]: admin.site.register(model,AuditedAdmin)

@admin.action(description='Accept selected Wikidata candidates as editorial drafts',permissions=['change'])
def accept_candidates(modeladmin,request,queryset):
    from django.core.exceptions import PermissionDenied
    if not request.user.has_perm('catalog.change_discoverycandidate') or not request.user.has_perm('catalog.add_product'):raise PermissionDenied
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

class PriceInline(admin.TabularInline):
    model=m.PriceObservation;extra=0;autocomplete_fields=['source'];show_change_link=True
@admin.register(m.Variant)
class VariantAdmin(AuditedAdmin):
    list_display=['product','name','market','abv','volume_ml'];search_fields=['product__name','product__brand__name','name','barcode'];autocomplete_fields=['product','source'];inlines=[PriceInline]
@admin.register(m.PriceObservation)
class PriceAdmin(AuditedAdmin):
    list_display=['variant','observed_on','observed_period','date_precision','amount','currency','country','retailer'];list_filter=['basis','date_precision','currency','country','retailer'];search_fields=['variant__product__name','variant__product__brand__name','retailer'];autocomplete_fields=['variant','source'];date_hierarchy='observed_on'


@admin.action(description='Publish selected licensed bottle photographs',permissions=['change'])
def approve_photos(modeladmin,request,queryset):
    from django.core.exceptions import PermissionDenied
    if not request.user.has_perm('catalog.change_bottlephoto'):raise PermissionDenied
    for photo in queryset:
        photo.approved=True;photo.save();m.Audit.objects.create(actor=request.user,action='photo.approved',target=str(photo.id))
@admin.register(m.BottlePhoto)
class BottlePhotoAdmin(AuditedAdmin):
    readonly_fields=['preview']
    def preview(self,obj):
        from django.utils.html import format_html
        return format_html('<img src="{}" style="max-width:420px;max-height:500px" alt="Submitted packaging photograph">',obj.photo.url) if obj.photo else 'No photograph'
    list_display=['product','view','credit','license','approved'];list_filter=['view','approved'];autocomplete_fields=['product'];actions=[approve_photos]


@admin.action(description='Accept reviewed archival prices into the published price notebook',permissions=['change'])
def accept_price_captures(modeladmin,request,queryset):
    from django.core.exceptions import PermissionDenied
    if not request.user.has_perm('catalog.change_discoverycandidate') or not request.user.has_perm('catalog.add_priceobservation'):raise PermissionDenied
    from .prices import accept_price_capture
    for candidate in queryset.filter(provider='wayback',status='pending'):
        try:accept_price_capture(candidate,request.user)
        except (ValueError,KeyError) as exc:modeladmin.message_user(request,str(exc),level=messages.ERROR)
CandidateAdmin.actions=[accept_candidates,accept_price_captures]

@admin.action(description='Queue archival collection for selected enabled targets',permissions=['change'])
def queue_archive_targets(modeladmin,request,queryset):
    from django.core.exceptions import PermissionDenied
    from .research import queue_targets
    if not request.user.has_perm('catalog.add_job') or not request.user.has_perm('catalog.change_pricearchivetarget'):raise PermissionDenied
    count=queue_targets(queryset,request.user)
    modeladmin.message_user(request,f'{count} archival jobs queued; duplicates already queued/running skipped.')
@admin.register(m.PriceArchiveTarget)
class ArchiveTargetAdmin(AuditedAdmin):
    list_display=['product','retailer_id','enabled','last_checked'];list_filter=['enabled'];search_fields=['product__name','product__slug','retailer_id'];autocomplete_fields=['product'];readonly_fields=['last_checked','last_result'];actions=[queue_archive_targets]
@admin.register(m.ProductResearch)
class ProductResearchAdmin(AuditedAdmin):
    list_display=['product','first_release_year'];search_fields=['product__name','product__slug','notes'];autocomplete_fields=['product']

@admin.register(m.ExternalPhotoReference)
class ExternalPhotoReferenceAdmin(AuditedAdmin):
    list_display=['product','view','publisher','verified','verified_on'];list_filter=['view','verified','publisher'];search_fields=['product__name','product__slug','edition_note'];autocomplete_fields=['product']

@admin.register(m.MarketPriceIndex)
class MarketPriceIndexAdmin(AuditedAdmin):
    list_display=['title','product','currency','territory','statistic','verified']
    list_filter=['verified','currency','territory']
    search_fields=['title','slug','product__name','product__slug','method']
    autocomplete_fields=['product','source']

@admin.register(m.MarketPriceIndexPoint)
class MarketPriceIndexPointAdmin(AuditedAdmin):
    list_display=['index','period','value']
    list_filter=['index']
    search_fields=['index__title','index__product__name','period']
    autocomplete_fields=['index']
    ordering=['index','period']
