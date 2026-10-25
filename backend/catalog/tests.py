import json, tempfile, copy, uuid
from io import BytesIO
from pathlib import Path
from PIL import Image
from django.test import TestCase, Client, override_settings
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from . import models as m
from .interchange import import_document,validate_document,export_file,run_job
from .admin import accept_submissions,approve_reviews

class CatalogueTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.doc=json.loads(settings.SEED_FILE.read_text()); import_document(cls.doc)
        cls.admin=get_user_model().objects.create_superuser('editor',password='very-long-random-test-password')
        cls.member=get_user_model().objects.create_user('member',password='different-long-test-password')
        m.Installation.objects.create(pk=1,completed=True)
    def post(self,path,data): return self.client.post('/api/v1/'+path,json.dumps(data),content_type='application/json')
    def test_seed_idempotent(self):
        import_document(self.doc);self.assertEqual(m.Product.objects.count(),len(self.doc['tables']['products']))
    def test_catalogue_cursor_and_limits(self):
        data=self.client.get('/api/v1/products?limit=2').json();self.assertEqual(len(data['items']),2)
        nxt=self.client.get('/api/v1/products',{'limit':2,'after':data['next']}).json()
        self.assertTrue(set(p['id'] for p in data['items']).isdisjoint(p['id'] for p in nxt['items']))
        self.assertEqual(self.client.get('/api/v1/products?limit=500').status_code,200)
    def test_ingredient_search(self):
        data=self.client.get('/api/v1/products?q=nutmeg').json();self.assertEqual(len(data['items']),1)
        self.assertEqual(data['items'][0]['brand'],'Monkey 47')
    def test_market_variants(self):
        data=self.client.get('/api/v1/products/roku-japanese-craft').json()
        self.assertEqual({v['abv'] for v in data['variants']},{'43.0','47.0'})
    def test_drafts_private(self):
        p=m.Product.objects.first();p.status='draft';p.save()
        self.assertEqual(self.client.get('/api/v1/products/'+p.slug).status_code,404)
    def test_unknowns_not_zero(self):
        data=self.client.get('/api/v1/products/monkey-47-schwarzwald').json()
        self.assertTrue(all(x['amount'] is None for x in data['recipes'][0]['ingredients']))
        self.assertEqual(data['measurements'],[])
    def test_invalid_cursor(self): self.assertEqual(self.client.get('/api/v1/products?after=bad').status_code,400)
    def test_sql_injection_is_literal(self): self.assertEqual(self.client.get('/api/v1/products',{'q':"' OR 1=1 --"}).json()['items'],[])
    def test_write_requires_session(self): self.assertEqual(self.post('jobs',{'kind':'json'}).status_code,401)
    def test_member_not_staff(self):
        self.client.force_login(self.member);self.assertEqual(self.post('jobs',{'kind':'json'}).status_code,403)
        self.assertEqual(self.client.get('/api/v1/operations').status_code,403)
    def test_csrf_required(self):
        c=Client(enforce_csrf_checks=True);c.force_login(self.admin)
        self.assertEqual(c.post('/api/v1/jobs',json.dumps({'kind':'json'}),content_type='application/json').status_code,403)
    def test_csrf_cookie_and_write(self):
        c=Client(enforce_csrf_checks=True);c.force_login(self.admin);c.get('/api/v1/session')
        self.assertEqual(c.post('/api/v1/jobs',json.dumps({'kind':'json'}),content_type='application/json',HTTP_X_CSRFTOKEN=c.cookies['csrftoken'].value).status_code,202)
    def test_setup_cannot_repeat(self):
        with override_settings(SETUP_TOKEN='test-token'): self.assertEqual(self.post('setup',{'token':'test-token'}).status_code,409)
    def test_registration_cannot_set_staff(self):
        response=self.post('register',{'username':'new-reader','password':'a-very-strong-reader-password','is_staff':True})
        self.assertEqual(response.status_code,201);self.assertFalse(get_user_model().objects.get(username='new-reader').is_staff)
    def test_weak_password_rejected(self): self.assertEqual(self.post('register',{'username':'reader','password':'123'}).status_code,400)
    def test_registration_can_close(self):
        with override_settings(REGISTRATION_OPEN=False): self.assertEqual(self.post('register',{}).status_code,403)
    def test_bad_login(self): self.assertEqual(self.post('login',{'username':'member','password':'wrong'}).status_code,401)
    def test_collection_is_private(self):
        self.client.force_login(self.member);p=m.Product.objects.first()
        self.assertEqual(self.post('collection',{'slug':p.slug,'state':'owned'}).status_code,200)
        self.assertEqual(len(self.client.get('/api/v1/collection').json()['items']),1)
        self.client.force_login(self.admin);self.assertEqual(self.client.get('/api/v1/collection').json()['items'],[])
    def test_review_moderation(self):
        self.client.force_login(self.member);p=m.Product.objects.first()
        self.assertEqual(self.post(f'products/{p.slug}/reviews',{'rating':5,'text':'Juniper and citrus.'}).status_code,200)
        self.assertEqual(self.client.get(f'/api/v1/products/{p.slug}').json()['reviews'],[])
        m.Review.objects.update(approved=True)
        self.assertEqual(len(self.client.get(f'/api/v1/products/{p.slug}').json()['reviews']),1)
        self.assertEqual(self.post(f'products/{p.slug}/reviews',{'rating':6,'text':'Invalid'}).status_code,400)
    def test_submission_validated(self):
        self.client.force_login(self.member)
        self.assertEqual(self.post('submissions',{'name':'missing-fields'}).status_code,400)
    def test_export_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'catalog.json';export_file(path,'json');doc=json.loads(path.read_text())
            self.assertEqual(validate_document(doc)['products'],len(self.doc['tables']['products']));import_document(doc)
            self.assertNotIn('users',doc['tables']);self.assertNotIn('reviews',doc['tables'])
    def test_export_excludes_drafts(self):
        p=m.Product.objects.first();p.status='draft';p.save()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'c.json';export_file(path,'json');doc=json.loads(path.read_text());self.assertEqual(validate_document(doc)['products'],len(self.doc['tables']['products'])-1)
    def test_extra_fields_rejected(self):
        doc=copy.deepcopy(self.doc);doc['tables']['products'][0]['photo']='../../secret'
        with self.assertRaises(ValueError): validate_document(doc)
    def test_missing_references_rejected(self):
        doc=copy.deepcopy(self.doc);doc['tables']['variants'][0]['source_id']=str(uuid.uuid4())
        with self.assertRaises(ValueError): validate_document(doc)
    def test_bad_model_validation_rolls_back(self):
        doc=copy.deepcopy(self.doc);doc['tables']['brands'][0]['name']='Changed';doc['tables']['variants'][0]['abv']='120'
        with self.assertRaises(ValidationError): import_document(doc)
        self.assertFalse(m.Brand.objects.filter(name='Changed').exists())
    def test_job_files_manifest_and_jsonl(self):
        with tempfile.TemporaryDirectory() as d,override_settings(EXPORT_ROOT=Path(d)):
            for kind in ['json','jsonl']:
                job=m.Job.objects.create(kind=kind,created_by=self.admin);run_job(job);job.refresh_from_db();self.assertEqual(job.status,'done')
                self.assertEqual(len(job.checksum),64);self.assertTrue((Path(d)/f'{job.id}.manifest.json').exists())
    def test_download_is_staff_only(self):
        self.client.force_login(self.member);self.assertEqual(self.client.get(f'/api/v1/jobs/{uuid.uuid4()}/download').status_code,403)
    def test_image_reencoded(self):
        buf=BytesIO();Image.new('RGB',(10,10),'red').save(buf,'PNG')
        p=m.Product.objects.first();p.photo=SimpleUploadedFile('safe.png',buf.getvalue(),content_type='image/png');p.photo_credit='Original';p.photo_license='CC0';p.full_clean();self.assertTrue(p.photo.name.endswith('.jpg'))
    def test_svg_upload_rejected(self):
        p=m.Product.objects.first();p.photo=SimpleUploadedFile('evil.svg',b'<svg onload="alert(1)"/>');p.photo_credit='X';p.photo_license='CC0'
        with self.assertRaises(ValidationError): p.full_clean()
    def test_photo_attribution_required(self):
        p=m.Product.objects.first();p.photo=SimpleUploadedFile('x.png',b'bad')
        with self.assertRaises(ValidationError): p.full_clean()
    def test_body_size_limit(self):
        self.assertEqual(self.client.post('/api/v1/login',b'x',content_type='application/json',CONTENT_LENGTH=str(7*1024*1024)).status_code,413)
    def test_login_rate_limit(self):
        for _ in range(20): self.post('login',{'username':'unknown','password':'wrong'})
        self.assertEqual(self.post('login',{'username':'unknown','password':'wrong'}).status_code,429)
    def test_json_preview_no_mutation(self):
        self.client.force_login(self.admin)
        response=self.post('imports',{'document':self.doc,'commit':False});self.assertEqual(response.status_code,200);self.assertFalse(m.Job.objects.exists())
    def test_worker_runs_queued_job(self):
        with tempfile.TemporaryDirectory() as d,override_settings(EXPORT_ROOT=Path(d)):
            job=m.Job.objects.create(kind='json',created_by=self.admin);call_command('worker',once=True);job.refresh_from_db();self.assertEqual(job.status,'done')
    def test_editor_without_operations_permission(self):
        user=get_user_model().objects.create_user('limited-editor',password='long-editor-password',is_staff=True)
        self.client.force_login(user);self.assertEqual(self.post('jobs',{'kind':'sql'}).status_code,403)
    def test_valid_submission_becomes_draft(self):
        self.client.force_login(self.member)
        response=self.post('submissions',{'brand':'New Brand','name':'Botanical Edition','country':'France','market':'EU','abv':42,'volume_ml':700,'description':'Contributor proposal','source_url':'https://example.org/source','ingredients':'Juniper, Coriander'})
        self.assertEqual(response.status_code,201)
        self.assertEqual(m.Submission.objects.count(),1)
        self.assertFalse(m.Product.objects.filter(name='Botanical Edition').exists())
        from django.test import RequestFactory
        request=RequestFactory().get('/');request.user=self.admin
        class AdminStub:
            def message_user(self,*args): pass
        accept_submissions(AdminStub(),request,m.Submission.objects.all())
        p=m.Product.objects.get(name='Botanical Edition');self.assertEqual(p.status,'draft')
        self.assertEqual(self.client.get('/api/v1/products/'+p.slug).status_code,404)
        self.assertTrue(all(x.certainty=='reported' for x in m.RecipeIngredient.objects.filter(recipe__product=p)))
    def test_duplicate_slug_import_rolls_back(self):
        from django.db import IntegrityError
        doc=copy.deepcopy(self.doc);doc['tables']['brands'][1]['slug']=doc['tables']['brands'][0]['slug']
        with self.assertRaises((IntegrityError,ValidationError)): import_document(doc)
        self.assertEqual(m.Brand.objects.count(),len(self.doc['tables']['brands']))
    def test_queued_import_roundtrip(self):
        with tempfile.TemporaryDirectory() as d,override_settings(EXPORT_ROOT=Path(d)):
            self.client.force_login(self.admin);r=self.post('imports',{'document':self.doc,'commit':True});self.assertEqual(r.status_code,202)
            call_command('worker',once=True);job=m.Job.objects.get(pk=r.json()['id']);self.assertEqual(job.status,'done')
    def test_admin_crud_pages(self):
        self.client.force_login(self.admin)
        for entity in ['product','recipe','source','brand','ingredient','compound','study','measurement','submission','job','audit']:
            self.assertEqual(self.client.get('/admin/catalog/'+entity+'/').status_code,200)

    def test_editions_group_under_original(self):
        items=self.client.get('/api/v1/products?q=monkey').json()['items']
        self.assertEqual([p['slug'] for p in items],['monkey-47-schwarzwald'])
        self.assertEqual(len(items[0]['editions']),2)
        self.assertEqual(len(self.client.get('/api/v1/products?q=monkey&editions=all').json()['items']),3)
    def test_market_bottlings_share_product(self):
        p=self.client.get('/api/v1/products/roku-japanese-craft').json()
        self.assertEqual(len(p['variants']),2)
    def test_private_transition_matrix(self):
        p=m.Product.objects.first();self.client.force_login(self.member)
        path=f'products/{p.slug}/observations'
        self.assertEqual(self.post(path,{'from_state':'baseline','to_state':'relaxed'}).status_code,200)
        d=self.client.get('/api/v1/'+path).json()
        self.assertEqual(d['transition_matrix']['baseline']['relaxed'],1)
        self.assertIsNone(d['transition_matrix']['sleepy']['relaxed'])
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/api/v1/'+path).json()['observations'],0)
    def test_zero_monkeys_valid(self):
        self.client.force_login(self.member);p=m.Product.objects.first()
        self.assertEqual(self.post(f'products/{p.slug}/reviews',{'rating':0,'text':'Not my taste'}).status_code,200)
    def test_merge_preserves_duplicate_and_redirects(self):
        from .duplicates import merge
        original=m.Product.objects.get(slug='monkey-47-schwarzwald')
        duplicate=m.Product.objects.create(slug='test-duplicate',brand=original.brand,name='Duplicate listing',description='Disposable test fixture',status='published')
        v=m.Variant.objects.create(product=duplicate,name='750 ml listing',market='Test market',abv=47,volume_ml=750,source=m.Source.objects.first())
        photo=m.BottlePhoto.objects.create(product=duplicate,view='back',photo='test-fixture.jpg',credit='Test',license='Test',source_url='https://example.com')
        merge(duplicate,original,self.admin);duplicate.refresh_from_db();v.refresh_from_db();photo.refresh_from_db()
        self.assertEqual(photo.product,original)
        self.assertEqual(self.client.get('/spirits/test-duplicate/').status_code,301)
        self.assertEqual(duplicate.status,'archived');self.assertEqual(duplicate.merged_into,original);self.assertEqual(v.product,original)
        self.assertEqual(self.client.get('/api/v1/products/test-duplicate').status_code,302)
        self.assertTrue(m.Audit.objects.filter(action='product.merged').exists())
    def test_merge_rejects_distinct_edition(self):
        from .duplicates import merge
        with self.assertRaises(ValidationError):merge(m.Product.objects.get(slug='monkey-47-cut-2024'),m.Product.objects.get(slug='monkey-47-schwarzwald'),self.admin)
    def test_price_observation_roundtrip(self):
        v=m.Variant.objects.first()
        m.PriceObservation.objects.create(variant=v,observed_on='2026-10-25',amount='39.90',currency='EUR',country='Test country',retailer='Test fixture',source=m.Source.objects.first())
        r=self.client.get('/api/v1/products/'+v.product.slug).json()['prices'][0]
        self.assertEqual(r['amount'],'39.90');self.assertEqual(r['currency'],'EUR')
    def test_candidate_links_existing_without_fork(self):
        from .admin import accept_candidates
        p=m.Product.objects.first();count=m.Product.objects.count()
        c=m.DiscoveryCandidate.objects.create(provider='wikidata',external_id='Q123',label='Another listing',category='Gin',source_url='https://www.wikidata.org/wiki/Q123',payload={},resolved_product=p)
        class Stub:
            def message_user(self,*a,**kw):pass
        request=type('Request',(),{'user':self.admin})()
        accept_candidates(Stub(),request,m.DiscoveryCandidate.objects.filter(pk=c.pk))
        c.refresh_from_db();self.assertEqual(c.status,'accepted');self.assertEqual(m.Product.objects.count(),count)

    def test_public_html_is_readable_and_canonical(self):
        r=self.client.get('/spirits/monkey-47-schwarzwald/')
        self.assertContains(r,'Schwarzwald Dry Gin');self.assertContains(r,'application/ld+json')
        self.assertContains(r,'http://localhost:8088/spirits/monkey-47-schwarzwald/')
        self.assertContains(r,'Origin, culture and legacy');self.assertContains(r,'Juniper')
        self.assertEqual(self.client.get('/unknown-section/').status_code,404)
    def test_private_pages_noindex_and_sitemap(self):
        self.assertEqual(self.client.get('/shelf/')['X-Robots-Tag'],'noindex, nofollow')
        r=self.client.get('/sitemap.xml');self.assertContains(r,'/spirits/monkey-47-schwarzwald/')
        self.assertNotContains(r,'/shelf/');self.assertContains(self.client.get('/robots.txt'),'Disallow: /admin/')
    def test_html_never_leaks_draft(self):
        p=m.Product.objects.get(slug='monkey-47-schwarzwald');p.status='draft';p.save()
        self.assertEqual(self.client.get('/spirits/'+p.slug+'/').status_code,404)
        self.assertNotContains(self.client.get('/sitemap.xml'),'/spirits/'+p.slug+'/')
    def test_detailed_review_moderation_and_averages(self):
        self.client.force_login(self.member)
        r=self.post('products/monkey-47-schwarzwald/reviews',{'rating':4,'text':'QA tasting note','aroma':5,'taste':4,'finish':3,'value':0,'design':5,'tags':['floral','citrus'],'context':'tonic','buy_again':'yes'})
        self.assertEqual(r.status_code,200)
        p=m.Product.objects.get(slug='monkey-47-schwarzwald');review=p.reviews.get(user=self.member)
        self.assertFalse(review.approved);self.assertTrue(review.buy_again);self.assertEqual(review.value,0)
        data=self.client.get('/api/v1/products/'+p.slug).json();self.assertIsNone(data['review_dimensions']['aroma'])
        review.approved=True;review.save();data=self.client.get('/api/v1/products/'+p.slug).json()
        self.assertEqual(data['review_dimensions']['aroma'],5);self.assertEqual(data['review_dimensions']['aroma_count'],1)
        self.assertEqual(data['review_dimensions']['value'],0)
    def test_detailed_review_rejects_unsupported_values(self):
        self.client.force_login(self.member)
        for extra in [{'taste':6},{'tags':['hallucinogenic']},{'context':'injected'},{'buy_again':'maybe'}]:
            self.assertEqual(self.post('products/monkey-47-schwarzwald/reviews',{'rating':3,'text':'Test',**extra}).status_code,400)
    def test_packaging_photos_require_rights_and_moderation(self):
        self.client.force_login(self.member)
        with tempfile.TemporaryDirectory() as media,override_settings(MEDIA_ROOT=media):
            out=BytesIO();Image.new('RGB',(30,40)).save(out,format='PNG')
            payload={'view':'back','credit':'Test photographer','license':'Own photo CC BY-SA 4.0','source_url':'https://example.com/photo','photo':SimpleUploadedFile('back.png',out.getvalue(),content_type='image/png')}
            self.assertEqual(self.client.post('/api/v1/products/monkey-47-schwarzwald/photos',payload).status_code,400)
            payload['photo']=SimpleUploadedFile('back.png',out.getvalue(),content_type='image/png');payload['rights_confirmed']='yes'
            r=self.client.post('/api/v1/products/monkey-47-schwarzwald/photos',payload);self.assertEqual(r.status_code,201)
            photo=m.BottlePhoto.objects.get(pk=r.json()['id']);self.assertFalse(photo.approved);self.assertTrue(photo.photo.name.endswith('.jpg'))
            p=self.client.get('/api/v1/products/monkey-47-schwarzwald').json();self.assertNotIn(str(photo.id),[str(x['id']) for x in p['photos']])
            photo.approved=True;photo.save();p=self.client.get('/api/v1/products/monkey-47-schwarzwald').json();self.assertIn(str(photo.id),[str(x['id']) for x in p['photos']])
    def test_curated_packaging_views(self):
        p=self.client.get('/api/v1/products/heering-cherry-liqueur').json()
        self.assertEqual({x['view'] for x in p['photos']},{'front','back'})
    def test_photo_rejects_non_raster(self):
        with tempfile.TemporaryDirectory() as media,override_settings(MEDIA_ROOT=media):
            photo=m.BottlePhoto(product=m.Product.objects.first(),view='back',credit='QA',license='QA',source_url='https://example.com',photo=SimpleUploadedFile('bad.svg',b'<svg onload="alert(1)"></svg>'))
            with self.assertRaises(ValidationError):photo.full_clean()

    def test_discovery_groups_count_and_explanation(self):
        d=self.client.get('/api/v1/discover?category=Gin&groups=floral&limit=24').json()
        self.assertIn('roku-japanese-craft',[x['slug'] for x in d['items']])
        for p in d['items']:
            self.assertTrue(p['matches']);self.assertIn('floral',p['ingredient_groups'])
            self.assertEqual(p['category'],'Gin');self.assertEqual(p['coverage']['total'],6)
        self.assertTrue(next(x for x in d['groups'] if x['key']=='floral')['count']>0)
    def test_discovery_is_canonical_and_excludes_drafts(self):
        p=m.Product.objects.get(slug='monkey-47-schwarzwald');p.status='draft';p.save()
        d=self.client.get('/api/v1/discover?limit=24').json()
        self.assertNotIn(p.slug,[x['slug'] for x in d['items']])
        self.assertFalse(any('cut-202' in x['slug'] for x in d['items']))
    def test_discovery_invalid_filters(self):
        for query in ['groups=hallucinogenic','min_abv=nan','min_abv=70&max_abv=40','coverage=7','sort=cheap']:
            self.assertEqual(self.client.get('/api/v1/discover?'+query).status_code,400)
    def test_discovery_strength_applies_to_same_bottling(self):
        d=self.client.get('/api/v1/discover?q=roku&min_abv=44&max_abv=46').json()
        self.assertEqual(d['total'],0)
        self.assertEqual(self.client.get('/api/v1/discover?q=roku&min_abv=46').json()['total'],1)
    def test_coverage_does_not_count_empty_history(self):
        p=m.Product.objects.get(slug='monkey-47-schwarzwald');p.history='';p.save()
        d=self.client.get('/api/v1/products/'+p.slug).json()
        self.assertFalse(next(x for x in d['coverage']['areas'] if x['key']=='history')['documented'])
    def test_alternatives_explain_overlap_and_privacy(self):
        d=self.client.get('/api/v1/products/monkey-47-schwarzwald').json()
        self.assertEqual(len(d['alternatives']),3)
        for p in d['alternatives']:
            self.assertNotEqual(p['slug'],'monkey-47-schwarzwald');self.assertEqual(p['category'],'Gin')
            self.assertTrue(p['shared_ingredients']);self.assertEqual(p['basis'],'Shared indexed ingredients')
    def test_discovery_pagination_and_order(self):
        first=self.client.get('/api/v1/discover?limit=6').json();second=self.client.get('/api/v1/discover?limit=6&page=2').json()
        self.assertTrue({x['id'] for x in first['items']}.isdisjoint(x['id'] for x in second['items']))
        values=[x['coverage']['documented'] for x in first['items']];self.assertEqual(values,sorted(values,reverse=True))
    def test_discovery_query_count_is_bounded(self):
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        with CaptureQueriesContext(connection) as queries:self.client.get('/api/v1/discover?limit=24')
        self.assertLessEqual(len(queries),12)

    def test_navigation_group_is_optional_for_old_imports(self):
        older=copy.deepcopy(self.doc)
        for row in older['tables']['ingredients']:row.pop('navigation_group',None)
        validate_document(older);import_document(older)
        self.assertEqual(m.Ingredient.objects.get(slug='lavender').navigation_group,'floral')
    def test_publisher_scores_do_not_become_community_votes(self):
        d=self.client.get('/api/v1/products/monkey-47-schwarzwald').json()
        self.assertEqual(len(d['critic_reviews']),2);self.assertEqual(d['rating']['count'],0)
        self.assertIsNone(d['rating']['average'])
        panel=m.CriticReview.objects.get(critic__startswith='Seattle');self.assertEqual(str(panel.score),'3.74');self.assertIsNone(panel.published_on)
    def test_approved_member_front_photo_is_discoverable(self):
        p=m.Product.objects.create(brand=m.Brand.objects.first(),slug='qa-member-photo',name='QA Photo',status='published')
        photo=m.BottlePhoto.objects.create(product=p,view='front',photo='test-fixture.jpg',credit='QA',license='QA',source_url='https://example.com')
        self.assertEqual(self.client.get('/api/v1/discover?q=QA+Photo&photo=1').json()['total'],0)
        photo.approved=True;photo.save()
        d=self.client.get('/api/v1/discover?q=QA+Photo&photo=1').json();self.assertEqual(d['total'],1)
        self.assertEqual(d['items'][0]['image_credit'],'QA')
