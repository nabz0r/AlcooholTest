"""Survey-series identity, publication privacy and additive dump compatibility."""
import copy
import json
import tempfile
import uuid
from pathlib import Path
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError,transaction
from django.test import TestCase
from . import models as m
from .interchange import import_document,validate_document,export_file


class MarketIndexTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.doc=json.loads(settings.SEED_FILE.read_text())
        import_document(cls.doc)
        cls.index=m.MarketPriceIndex.objects.get(product__slug='suntory-kakubin-blended-whisky')

    def setUp(self):cache.clear()

    def test_all_months_have_actual_period_precision_and_source(self):
        response=self.client.get('/api/v1/products/suntory-kakubin-blended-whisky').json()
        series=response['market_indexes'][0]
        self.assertEqual(series['date_precision'],'month')
        self.assertEqual(len(series['points']),321)
        self.assertEqual(series['points'][0],{'period':'2000-01','value':'1452.00'})
        self.assertEqual(series['points'][-1],{'period':'2026-09','value':'1718.00'})
        self.assertEqual(series['source']['url'],'https://nedan-hakusho.jp/items/2033/')
        self.assertIn('2007-01',series['method'])
        self.assertNotIn('abv',series)

    def test_unverified_indexes_and_their_points_stay_out_of_public_surfaces(self):
        self.index.verified=False;self.index.save()
        self.assertEqual(self.client.get('/api/v1/products/suntory-kakubin-blended-whisky').json()['market_indexes'],[])
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'public.json';export_file(path,'json');doc=json.loads(path.read_text())
        self.assertEqual(doc['tables']['market_price_indexes'],[])
        self.assertEqual(doc['tables']['market_price_index_points'],[])

    def test_draft_product_hides_verified_index_from_exports(self):
        product=self.index.product;product.status='draft';product.save()
        self.assertEqual(self.client.get('/api/v1/products/'+product.slug).status_code,404)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'public.json';export_file(path,'json');doc=json.loads(path.read_text())
        self.assertEqual(doc['tables']['market_price_indexes'],[])
        self.assertEqual(doc['tables']['market_price_index_points'],[])

    def test_duplicate_period_and_nonpositive_value_are_database_constraints(self):
        with self.assertRaises(IntegrityError),transaction.atomic():
            m.MarketPriceIndexPoint.objects.create(index=self.index,period='2000-01',value=1)
        with self.assertRaises(IntegrityError),transaction.atomic():
            m.MarketPriceIndexPoint.objects.create(index=self.index,period='2030-01',value=0)

    def test_month_validation_rejects_fabricated_days_and_invalid_months(self):
        for period in ['2000-01-01','2000-00','2000-13','0000-01','June 2000']:
            with self.assertRaises(ValidationError):
                m.MarketPriceIndexPoint(index=self.index,period=period,value=100).full_clean()

    def test_dump_roundtrip_preserves_months_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'public.json';export_file(path,'json');doc=json.loads(path.read_text())
        validate_document(doc);import_document(doc)
        self.assertEqual(m.MarketPriceIndex.objects.count(),1)
        self.assertEqual(m.MarketPriceIndexPoint.objects.count(),321)
        self.assertEqual(m.MarketPriceIndexPoint.objects.first().period,'2000-01')

    def test_additive_tables_are_optional_for_older_public_documents(self):
        doc=copy.deepcopy(self.doc)
        for table in ['market_price_indexes','market_price_index_points']:doc['tables'].pop(table)
        validate_document(doc)

    def test_dump_validation_rejects_duplicate_period_with_distinct_ids(self):
        doc=copy.deepcopy(self.doc);row=copy.deepcopy(doc['tables']['market_price_index_points'][0]);row['id']=str(uuid.uuid4());doc['tables']['market_price_index_points'].append(row)
        with self.assertRaisesRegex(ValueError,'Duplicate monthly period'):validate_document(doc)

