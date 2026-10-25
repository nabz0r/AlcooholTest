"""Real source precision must survive storage, public APIs, coverage and dumps."""
from datetime import date
import json
from pathlib import Path
import tempfile
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError,transaction
from django.test import TestCase
from . import models as m
from .interchange import export_file,import_document,validate_document
from .price_dates import price_bounds,price_label,conservative_span
from .research import coverage_rows


class SourceDatePrecisionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source=m.Source.objects.create(title='Original monthly wholesale catalogue',url='https://example.org/catalogue.pdf',publisher='Public catalogue publisher',kind='regulator',accessed_on=date(2026,10,25))
        brand=m.Brand.objects.create(slug='month-fixture',name='Month fixture',country='United States',website='https://example.org/')
        cls.product=m.Product.objects.create(slug='month-fixture',brand=brand,name='Named expression',description='Date precision fixture.',status='published')
        cls.variant=m.Variant.objects.create(product=cls.product,name='750 ml / 44%',market='United States',abv='44',volume_ml=750,source=cls.source)

    def setUp(self):cache.clear()

    def observation(self,**changes):
        values=dict(variant=self.variant,source=self.source,basis='wholesale_list',observed_on=None,observed_period='2003-05',date_precision='month',amount='19.99',currency='USD',country='United States',retailer='Original state wholesale list',tax_included=None)
        values.update(changes)
        return m.PriceObservation(**values)

    def test_month_storage_and_api_never_supply_a_day(self):
        price=self.observation();price.full_clean();price.save()
        self.observation(observed_on=date(2026,10,25),observed_period='',date_precision='day',basis='retail_offer').save()
        prices=self.client.get('/api/v1/products/'+self.product.slug).json()['prices']
        self.assertIsNone(prices[0]['date'])
        self.assertEqual(prices[0]['period'],'2003-05')
        self.assertEqual(prices[0]['date_precision'],'month')
        self.assertEqual(prices[0]['basis'],'wholesale_list')
        self.assertEqual(prices[1]['date'],'2026-10-25')
        self.assertIsNone(prices[1]['period'])

    def test_exactly_one_matching_source_precision_is_required(self):
        for changes in [dict(observed_on=date(2003,5,1)),dict(observed_period=''),dict(date_precision='day'),dict(observed_period='2003-13'),dict(observed_period='2003-05-01')]:
            with self.subTest(changes=changes),self.assertRaises(ValidationError):self.observation(**changes).full_clean()
        with self.assertRaises(IntegrityError),transaction.atomic():
            self.observation(observed_on=date(2003,5,1)).save()

    def test_monthly_uniqueness_is_enforced_without_an_observation_day(self):
        self.observation().save()
        with self.assertRaises(IntegrityError),transaction.atomic():self.observation().save()
        self.observation(observed_period='2003-06').save()
        self.assertEqual(m.PriceObservation.objects.count(),2)

    def test_month_bounds_are_conservative_and_not_serialized_as_dates(self):
        monthly={'date_precision':'month','observed_period':'2024-02','observed_on':None}
        self.assertEqual(price_bounds(monthly),(date(2024,2,1),date(2024,2,29)))
        self.assertEqual(price_label(monthly),'2024-02')
        early={'date_precision':'month','observed_period':'2006-01','observed_on':None}
        late={'observed_on':'2026-01-01'}
        self.assertLess(conservative_span([early,late]),20)

    def test_coverage_does_not_join_wholesale_and_retail_levels(self):
        self.observation(tax_included=True).save()
        self.observation(observed_on=date(2026,10,25),observed_period='',date_precision='day',basis='retail_offer',tax_included=True).save()
        row=coverage_rows(m.Product.objects.filter(pk=self.product.pk))[0]
        self.assertTrue(row['twenty_year_evidence'])
        self.assertFalse(row['twenty_year_series'])
        self.assertEqual(row['comparable_span_years'],0)
        self.assertEqual(row['earliest_label'],'2003-05')
        self.assertEqual(row['earliest_precision'],'month')

    def test_roundtrip_preserves_month_and_old_day_documents_remain_compatible(self):
        self.observation().save()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'catalogue.json';export_file(path,'json');document=json.loads(path.read_text())
        validate_document(document);import_document(document)
        price=m.PriceObservation.objects.get()
        self.assertIsNone(price.observed_on);self.assertEqual(price.observed_period,'2003-05')
        old=document['tables']['price_observations'][0]
        old['observed_on']='2003-05-17';old.pop('observed_period');old.pop('date_precision')
        validate_document(document)

    def test_review_holds_reject_unknown_providers_and_nonfinite_strengths(self):
        target=m.PriceArchiveTarget(product=self.product,retailer_id=2254,tokens=['citadelle'],source_url='https://www.thewhiskyexchange.com/p/2254/citadelle-french-gin')
        for value in [{'unknown':{}},{'drinkshop':{'blocked_abv':['NaN']}},{'drinkshop':{'blocked_abv':[101]}},{'drinkshop':{'reason':'x'*1001}}]:
            target.review_rules=value
            with self.subTest(value=value),self.assertRaises(ValidationError):target.full_clean()
        target.review_rules={'drinkshop':{'blocked_abv':['15','29'],'reason':'Unresolved historical strength conflicts.'}}
        target.full_clean();self.assertEqual(target.as_target()['review_rules'],target.review_rules)
