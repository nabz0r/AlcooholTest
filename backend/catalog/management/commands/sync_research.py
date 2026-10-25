"""Seed missing editorial collection settings; preserve every existing admin edit."""
import json
from django.conf import settings
from django.core.management.base import BaseCommand
from catalog import models as m
class Command(BaseCommand):
    help='Add missing reviewed archive targets/research plans from shipped evidence; never overwrite existing settings.'
    def handle(self,*args,**opts):
        base=settings.SEED_FILE.parent.parent;created=0
        for row in json.loads((base/'prices/targets.json').read_text()):
            product=m.Product.objects.filter(slug=row['product'],merged_into__isnull=True).first()
            if not product:continue
            target=m.PriceArchiveTarget(product=product,retailer_id=row['retailer_id'],tokens=row['tokens'],exclude_tokens=row.get('exclude_tokens',[]),original_urls=row.get('original_urls',[]),source_url=row.get('source_url',row.get('verified_url',f"https://www.thewhiskyexchange.com/p/{row['retailer_id']}/")),notes=row.get('notes','Reviewed target from repository research. Validate source and expression before changing identity.'))
            target.full_clean(validate_unique=False,validate_constraints=False)
            _,added=m.PriceArchiveTarget.objects.get_or_create(product=product,retailer_id=target.retailer_id,defaults={f:getattr(target,f) for f in ['tokens','exclude_tokens','original_urls','source_url','notes']});created+=added
        legacy_file=base/'prices/legacy-targets.json'
        if legacy_file.exists():
            for row in json.loads(legacy_file.read_text()):
                target=m.PriceArchiveTarget.objects.filter(product__slug=row['product'],retailer_id=row['retailer_id']).first()
                if target and not target.legacy_url and not target.legacy_ref:
                    for field in ['legacy_url','legacy_ref','legacy_titles','legacy_age']:setattr(target,field,row.get(field,'' if field!='legacy_titles' else []))
                    target.full_clean();target.save(update_fields=['legacy_url','legacy_ref','legacy_titles','legacy_age','updated_at'])
        drinkshop_file=base/'prices/drinkshop-targets.json'
        if drinkshop_file.exists():
            for row in json.loads(drinkshop_file.read_text()):
                target=m.PriceArchiveTarget.objects.filter(product__slug=row['product'],retailer_id=row['retailer_id']).first()
                if target and not target.drinkshop_id:
                    target.drinkshop_id=row['source_retailer_id'];target.drinkshop_titles=row['legacy_titles'];target.drinkshop_volume_ml=row['volume_ml'];
                    target.review_rules=row.get('review_rules',{})
                    target.full_clean();target.save(update_fields=['drinkshop_id','drinkshop_titles','drinkshop_volume_ml','review_rules','updated_at'])
        for product in m.Product.objects.filter(status='published',edition_of__isnull=True,merged_into__isnull=True):m.ProductResearch.objects.get_or_create(product=product)
        coverage=base/'prices/coverage-research.json'
        if coverage.exists():
            for row in json.loads(coverage.read_text()):
                plan=m.ProductResearch.objects.filter(product__slug=row['product']).first()
                if not plan:continue
                changed=[]
                if plan.first_release_year is None and not plan.release_source_url and (row.get('first_release_year') or row.get('release_not_before_year')) and row.get('release_source_url'):
                    plan.first_release_year=row['first_release_year'];plan.release_not_before_year=row.get('release_not_before_year');plan.release_source_url=row['release_source_url'];changed+=['first_release_year','release_not_before_year','release_source_url']
                if not plan.notes and row.get('notes'):plan.notes=row['notes'];changed.append('notes')
                if changed:plan.full_clean();plan.save(update_fields=changed+['updated_at'])
        photography=base/'photography/coverage.json'
        if photography.exists():
            for row in json.loads(photography.read_text()).get('products',[]):
                product=m.Product.objects.filter(slug=row['product_slug'],merged_into__isnull=True).first()
                if not product:continue
                m.DiscoveryCandidate.objects.get_or_create(provider='photography-audit',external_id=product.slug,defaults={'label':('Photographic research · '+str(product))[:240],'category':product.category,'source_url':'https://github.com/nabz0r/AlcooholTest/blob/main/data/photography/coverage.json','payload':row,'resolved_product':product})
        self.stdout.write(f'{created} missing archive targets created. Existing targets and research edits preserved.')
