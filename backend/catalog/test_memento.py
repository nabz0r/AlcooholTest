"""Memento integrity, source scope, private-data exclusion and bounded media access."""
import copy
import hashlib
import json
import tempfile
import uuid
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from . import models as m
from .memento import (MAX_ASSET_BYTES, build_capsules, canonical, licensed_asset, local_asset_bytes,
                      memento_capsule, memento_index, persist_snapshot, public_document, sha256,
                      staff_memento, verify_capsule, write_bundle, refresh_snapshot)


def fixture():
    return {'tables': {
        'sources': [{'id':'s1','title':'Public house','url':'https://example.com/gin','publisher':'House',
                     'kind':'manufacturer','accessed_on':'2026-10-25','license_note':'Reference only','password':'DO-NOT-EXPORT'}],
        'brands':[{'id':'b1','slug':'house','name':'House','country':'Japan','website':'https://example.com/'}],
        'products':[{'id':'p1','slug':'public-gin','name':'Public gin','status':'published','brand_id':'b1',
                     'history':'An original editorial history.','history_source_id':'s1'},
                    {'id':'p2','slug':'secret-draft','name':'DRAFT-MARKER','status':'draft','brand_id':'b1','history_source_id':'s1'}],
        'variants':[{'id':'v1','product_id':'p1','name':'Original','source_id':'s1','volume_ml':700,'abv':'40.0'},
                    {'id':'v2','product_id':'p2','name':'DRAFT-BOTTLING','source_id':'s1'}],
        'price_observations':[{'id':'price1','variant_id':'v1','source_id':'s1','observed_on':None,
                               'observed_period':'2003-05','date_precision':'month','amount':'12.50','currency':'USD','basis':'wholesale_list'},
                              {'id':'price2','variant_id':'v2','source_id':'s1','notes':'DRAFT-PRICE'}],
        'external_photo_references':[{'id':'r1','product_id':'p1','view':'back','source_page':'https://photos.example.com/gin',
                                      'image_url':'https://photos.example.com/gin.jpg','publisher':'Shop','verified_on':'2026-10-25',
                                      'rights_note':'Permission not established','edition_note':'Rear of reference packaging','verified':True},
                                     {'id':'r2','product_id':'p1','verified':False,'edition_note':'PENDING-REFERENCE'}],
        'market_price_indexes':[{'id':'i1','product_id':'p1','source_id':'s1','verified':True,'title':'Public survey'},
                                {'id':'i2','product_id':'p1','source_id':'s1','verified':False,'title':'UNVERIFIED-SURVEY'}],
        'market_price_index_points':[{'id':'ip1','index_id':'i1','period':'2000-01','value':'1234'},
                                     {'id':'ip2','index_id':'i2','period':'2000-01','value':'999999'}],
        'users':[{'email':'PRIVATE-EMAIL','password':'PRIVATE-HASH'}],
        'reviews':[{'text':'PRIVATE-MEMBER-NOTE'}],
        'discovery_candidates':[{'payload':{'html':'PRIVATE-RAW-HTML'}}],
    }}


class MementoPureTests(SimpleTestCase):
    def test_public_scope_uses_explicit_fields_and_filters_unpublished_relations(self):
        document=fixture()
        document['tables']['sources'].append({'id':'s2','title':'ORPHAN-SOURCE','url':'https://draft.example.com','publisher':'PRIVATE-PUBLISHER','accessed_on':'2026-10-25'})
        document['tables']['brands'].append({'id':'b2','name':'DRAFT-ONLY-BRAND','website':'https://draft.example.com'})
        document['tables']['places']=[{'id':'pl2','name':'DRAFT-ONLY-PLACE','source_id':'s2'}]
        document['tables']['products'][1].update({'brand_id':'b2','place_id':'pl2','history_source_id':'s2'})
        capsules=build_capsules(document);content=canonical(capsules).decode()
        for secret in ['DO-NOT-EXPORT','DRAFT-MARKER','DRAFT-BOTTLING','DRAFT-PRICE','PENDING-REFERENCE',
                       'UNVERIFIED-SURVEY','999999','PRIVATE-EMAIL','PRIVATE-HASH','PRIVATE-MEMBER-NOTE','PRIVATE-RAW-HTML','ORPHAN-SOURCE','PRIVATE-PUBLISHER','DRAFT-ONLY-BRAND','DRAFT-ONLY-PLACE']:
            self.assertNotIn(secret,content)
        source=next(c for c in capsules if c['source_key']=='source:s1')
        self.assertIn('public-gin',source['products'])
        price=next(r for r in source['records'] if r['table']=='price_observations')['fields']
        self.assertIsNone(price['observed_on'])
        self.assertEqual(price['observed_period'],'2003-05')
        self.assertEqual(price['date_precision'],'month')
        self.assertTrue(all(verify_capsule(c) for c in capsules))

    def test_public_url_match_does_not_publish_draft_only_source_metadata(self):
        document=fixture()
        document['tables']['sources'].append({'id':'private-source','title':'PRIVATE-SOURCE-TITLE',
            'url':'https://example.com/','publisher':'PRIVATE-PUBLISHER-METADATA','accessed_on':'2026-10-25',
            'license_note':'PRIVATE-LICENSE-METADATA'})
        document['tables']['products'][1]['history_source_id']='private-source'
        capsules=build_capsules(document)
        content=canonical(capsules).decode()
        for sentinel in ['PRIVATE-SOURCE-TITLE','PRIVATE-PUBLISHER-METADATA','PRIVATE-LICENSE-METADATA']:
            self.assertNotIn(sentinel,content)
        self.assertFalse(any(c['source_key']=='source:private-source' for c in capsules))
        public_reference=next(c for c in capsules if c['source'].get('original_url')=='https://example.com/')
        self.assertEqual(public_reference['kind'],'reference')
        self.assertEqual(public_reference['source']['title'],'House')
        self.assertTrue(any(r['table']=='brands' for r in public_reference['records']))
        self.assertEqual(public_document(document)['tables']['sources'][0]['id'],'s1')

    def test_facts_hash_is_not_relabelled_as_original_page_hash(self):
        report={'points':[{'source_url':'https://example.com/gin','content_sha256':'a'*64,
                           'hash_scope':'Canonical JSON evidence_facts only; not raw HTML.','evidence_facts':{'price':'12.50'}}]}
        capsule=next(c for c in build_capsules(fixture(), [('prices/current-source-research.json',report)]) if c['source_key']=='source:s1')
        self.assertEqual(capsule['original_content_hashes'],[])
        self.assertEqual(capsule['source_proofs'][0]['content_sha256'],'a'*64)
        self.assertFalse(capsule['source_proofs'][0]['original_content_copied'])
        self.assertEqual(capsule['status'],'fact_extract_only')
        raw=build_capsules(fixture(),[('prices/archive-research.json',report)])
        self.assertEqual(next(c for c in raw if c['source_key']=='source:s1')['original_content_hashes'],['a'*64])

    def test_research_sources_without_foreign_keys_preserve_scoped_claims_and_exclude_drafts(self):
        report={'products':[
            {'product':'public-gin','first_release_year':None,'release_not_before_year':2016,
             'source_url':'https://owner.example/report.pdf','publisher':'Brand owner','source_kind':'brand_owner_annual_report',
             'exact_claim_scope':'Brand entry only; expression launch unknown.','reviewed_on':'2026-10-25',
             'source_retrieval':{'http_status':200,'checked_on':'2026-10-25','sha256':'b'*64,
                                 'hash_scope':'Downloaded raw PDF; full copyrighted document retained only in ignored research work directory.'},
             'additional_sources':[{'source_url':'https://trade.example/introduction','publisher':'Trade journal',
                                    'published_on':'2017-10-27','claim_scope':'Contemporary distribution report; no original response hash.'}],
             'private_unknown_field':'DO-NOT-COPY'},
            {'product':'secret-draft','source_url':'https://owner.example/report.pdf','exact_claim_scope':'PRIVATE-RESEARCH',
             'content_sha256':'c'*64,'evidence_facts':{'marker':'PRIVATE-PROOF-FACTS'}}]}
        capsules=build_capsules(fixture(),[('prices/additional-launch-research.json',report)])
        owner=next(c for c in capsules if c['source']['original_url']=='https://owner.example/report.pdf')
        self.assertEqual(owner['original_content_hashes'],['b'*64])
        self.assertEqual(owner['original_content_status'],'not_copied')
        self.assertEqual(owner['products'],['public-gin'])
        fields=owner['records'][0]['fields'];self.assertIsNone(fields['first_release_year'])
        self.assertEqual(fields['release_not_before_year'],2016)
        self.assertIn('expression launch unknown',fields['exact_claim_scope'])
        secondary=next(c for c in capsules if c['source']['original_url']=='https://trade.example/introduction')
        self.assertIsNone(secondary['source']['accessed_on'])
        self.assertEqual(secondary['original_content_hashes'],[])
        self.assertNotIn('DO-NOT-COPY',canonical(capsules).decode())
        self.assertNotIn('PRIVATE-RESEARCH',canonical(capsules).decode())
        self.assertNotIn('PRIVATE-PROOF-FACTS',canonical(capsules).decode())
        self.assertFalse(any(c['source']['original_url']=='https://draft.example/private-report' for c in capsules))

    def test_immutable_capsules_reuse_content_and_new_facts_create_new_revision(self):
        first=build_capsules(fixture());self.assertEqual(first,build_capsules(fixture()))
        changed=fixture();changed['tables']['products'][0]['history']='A corrected source-linked history.'
        second=build_capsules(changed)
        old=next(c for c in first if c['source_key']=='source:s1')['snapshot_sha256']
        new=next(c for c in second if c['source_key']=='source:s1')['snapshot_sha256']
        self.assertNotEqual(old,new)
        with tempfile.TemporaryDirectory() as folder:
            persist_snapshot(first,folder,'2026-10-25T01:00:00Z');path=Path(folder)/'capsules'/f'{old}.json';before=path.read_bytes()
            persist_snapshot(second,folder,'2026-10-25T02:00:00Z')
            self.assertEqual(path.read_bytes(),before)
            self.assertTrue((Path(folder)/'capsules'/f'{new}.json').exists())
            tampered=copy.deepcopy(first[0]);tampered['notice']='Altered'
            self.assertFalse(verify_capsule(tampered))

    def test_external_photograph_is_a_link_and_never_requests_source_bytes(self):
        capsules=build_capsules(fixture());reference=next(c for c in capsules if c['kind']=='external_photo_reference')
        self.assertEqual(reference['status'],'external_link_only')
        self.assertEqual(reference['source']['image_url'],'https://photos.example.com/gin.jpg')
        with tempfile.TemporaryDirectory() as folder, patch('catalog.memento.http.client.HTTPConnection') as network:
            manifest=persist_snapshot(capsules,folder);bundle=write_bundle(Path(folder)/'all.zip',manifest,folder)
            network.assert_not_called();self.assertEqual(bundle['external_reference_files_copied'],0)
            with zipfile.ZipFile(Path(folder)/'all.zip') as archive:
                self.assertFalse(any(name.startswith('media/') for name in archive.namelist()))

    def test_media_rejects_remote_paths_traversal_redirects_hash_mismatch_and_oversize(self):
        data=b'licensed local image';asset={'path':'/bottles/gin.jpg','sha256':sha256(data),'license':'CC BY 4.0',
                                         'license_url':'https://creativecommons.org/licenses/by/4.0/'}
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'public';root.mkdir();(root/'bottles').mkdir();(root/'bottles/gin.jpg').write_bytes(data)
            self.assertEqual(local_asset_bytes(asset,root),data)
            with self.assertRaises(ValueError):local_asset_bytes({**asset,'sha256':'f'*64},root)
            for path in ['https://evil.example/file.jpg','/bottles/../../secret.jpg','/bottles/gin.jpg?url=http://evil','/media/gin.jpg']:
                self.assertFalse(licensed_asset({**asset,'path':path}))
            outside=Path(folder)/'elsewhere.jpg';outside.write_bytes(data);(root/'bottles/escape.jpg').symlink_to(outside)
            # A symlink outside the selected asset root must be rejected.
            with self.assertRaises(ValueError):local_asset_bytes({**asset,'path':'/bottles/escape.jpg'},root)
        with patch('catalog.memento.http.client.HTTPConnection') as connect:
            response=connect.return_value.getresponse.return_value;response.status=302
            with self.assertRaises(ValueError):local_asset_bytes(asset)
            connect.assert_called_once_with('web',8080,timeout=8)
            connect.return_value.request.assert_called_once_with('GET','/bottles/gin.jpg',headers={'Accept':'image/jpeg,image/png,image/webp'})
        with patch('catalog.memento.http.client.HTTPConnection') as connect:
            response=connect.return_value.getresponse.return_value;response.status=200;response.getheader.return_value=str(MAX_ASSET_BYTES+1)
            with self.assertRaises(ValueError):local_asset_bytes(asset)
            response.read.assert_not_called()

    def test_bounded_listing_and_current_manifest_gate_on_capsule_downloads(self):
        with tempfile.TemporaryDirectory() as folder, override_settings(MEMENTO_ROOT=Path(folder)), patch('catalog.memento.current_publication_state',return_value=None):
            manifest=persist_snapshot(build_capsules(fixture()),folder)
            request=RequestFactory().get('/api/v1/memento',{'limit':'999999','product':'public-gin'})
            response=memento_index(request);result=json.loads(response.content)
            self.assertLessEqual(len(result['items']),60)
            self.assertTrue(all('public-gin' in row['products'] for row in result['items']))
            digest=manifest['items'][0]['sha256'];response=memento_capsule(RequestFactory().get('/'),digest)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.headers['ETag'],'"'+digest+'"')
            self.assertEqual(memento_capsule(RequestFactory().get('/',HTTP_IF_NONE_MATCH='"'+digest+'"'),digest).status_code,304)
            with self.assertRaises(Http404):memento_capsule(RequestFactory().get('/'),'../secret')
            persist_snapshot([],folder)
            with self.assertRaises(Http404):memento_capsule(RequestFactory().get('/'),digest)
            self.assertEqual(memento_index(RequestFactory().get('/',{'limit':'oops'})).status_code,400)
            self.assertEqual(memento_index(RequestFactory().post('/')).status_code,405)


class MementoPermissionTests(TestCase):
    def test_view_only_staff_cannot_queue_a_bundle(self):
        user=get_user_model().objects.create_user('source-reader',password='a secure test password',is_staff=True)
        user.user_permissions.add(Permission.objects.get(codename='view_source'))
        request=RequestFactory().post('/admin/catalog/source/memento/',{'action':'regenerate'})
        request.user=user;request._dont_enforce_csrf_checks=True
        with self.assertRaises(PermissionDenied):staff_memento(request)
        self.assertEqual(m.Job.objects.filter(kind='memento').count(),0)

    def test_authorized_regeneration_queues_one_durable_public_bundle(self):
        from django.contrib.messages.storage.fallback import FallbackStorage
        user=get_user_model().objects.create_superuser('memento-editor',password='a secure test password')
        for unused in range(2):
            request=RequestFactory().post('/admin/catalog/source/memento/',{'action':'regenerate'})
            request.user=user;request._dont_enforce_csrf_checks=True;request.session={};request._messages=FallbackStorage(request)
            self.assertEqual(staff_memento(request).status_code,302)
        self.assertEqual(m.Job.objects.filter(kind='memento',status='queued').count(),1)
        self.assertEqual(m.Audit.objects.filter(action='memento.queued').count(),1)

    def test_regeneration_post_requires_csrf_even_for_authorized_staff(self):
        user=get_user_model().objects.create_superuser('memento-owner',password='a secure test password')
        request=RequestFactory().post('/admin/catalog/source/memento/',{'action':'regenerate'});request.user=user
        response=staff_memento(request)
        self.assertEqual(response.status_code,403)
        self.assertEqual(m.Job.objects.filter(kind='memento').count(),0)


class MementoPublicationTests(TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.override=override_settings(MEMENTO_ROOT=Path(self.folder.name));self.override.enable();self.addCleanup(self.override.disable)
        self.source=m.Source.objects.create(title='Only this bottle',url='https://example.com/bottle',publisher='House',kind='manufacturer',accessed_on='2026-10-25')
        self.brand=m.Brand.objects.create(slug='public-house',name='Public house',country='Japan',website='https://example.com/')
        self.product=m.Product.objects.create(slug='public-bottle',name='Public bottle',brand=self.brand,status='published',description='Original description',history='Public history',history_source=self.source)

    def test_draft_only_source_brand_and_place_never_enter_database_snapshot(self):
        self.product.status='draft';self.product.save()
        manifest=refresh_snapshot()
        self.assertFalse(manifest['items'])
        self.assertNotIn('Only this bottle',json.dumps(manifest))

    def test_app_policy_upgrade_refreshes_legacy_manifest_with_unchanged_public_ids(self):
        manifest=refresh_snapshot()
        membership={'products':[str(self.product.pk)],'bottle_assets':[],
                    'approved_photographs':[],'external_photo_references':[],'market_price_indexes':[]}
        legacy_fingerprint=sha256(canonical(membership))
        self.assertNotEqual(manifest['publication_state_sha256'],legacy_fingerprint)
        legacy=dict(manifest);legacy.pop('snapshot_sha256')
        legacy['publication_state_sha256']=legacy_fingerprint
        legacy['snapshot_sha256']=sha256(canonical(legacy))
        index_path=Path(self.folder.name)/'index.json';index_path.write_bytes(canonical(legacy)+b'\n')
        with patch('catalog.memento.refresh_snapshot',wraps=refresh_snapshot) as refresh:
            response=memento_index(RequestFactory().get('/api/v1/memento'))
            self.assertEqual(response.status_code,200)
            refresh.assert_called_once_with()
        updated=json.loads(index_path.read_text())
        self.assertEqual(updated['publication_state_sha256'],manifest['publication_state_sha256'])
        self.assertEqual(updated['capsules'],manifest['capsules'])
        self.assertEqual([item['sha256'] for item in updated['items']],
                         [item['sha256'] for item in manifest['items']])

    def test_withdrawn_product_invalidates_previously_public_capsule_without_deleting_archive(self):
        manifest=refresh_snapshot();item=next(x for x in manifest['items'] if x['source_key']=='source:'+str(self.source.pk))
        archived=Path(self.folder.name)/'capsules'/(item['sha256']+'.json');self.assertTrue(archived.exists())
        m.Product.objects.filter(pk=self.product.pk).update(status='draft')
        with self.assertRaises(Http404):memento_capsule(RequestFactory().get('/'),item['sha256'])
        self.assertTrue(archived.exists())
        result=json.loads(memento_index(RequestFactory().get('/')).content)
        self.assertEqual(result['capsules'],0)

    def test_withdrawn_photo_reference_loses_public_access_even_while_product_stays_published(self):
        reference=m.ExternalPhotoReference.objects.create(product=self.product,view='back',source_page='https://example.com/rear',image_url='https://example.com/rear.jpg',publisher='Shop',rights_note='External link only',edition_note='Rear reference',verified_on='2026-10-25',verified=True)
        manifest=refresh_snapshot();item=next(x for x in manifest['items'] if x['source_key']=='photo-reference:'+str(reference.pk))
        m.ExternalPhotoReference.objects.filter(pk=reference.pk).update(verified=False)
        with self.assertRaises(Http404):memento_capsule(RequestFactory().get('/'),item['sha256'])
        self.assertEqual(m.Product.objects.get(pk=self.product.pk).status,'published')
