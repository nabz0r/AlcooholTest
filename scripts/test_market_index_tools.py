"""Protect reviewed monthly fact extraction and explicit publication decisions."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import uuid
from apply_market_indexes import apply_market_indexes


class MarketIndexToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document=json.loads((Path(__file__).resolve().parents[1]/'data/prices/market-indexes/kakubin.json').read_text())

    def normalize(self,document):
        tables={'products':[{'slug':'suntory-kakubin-blended-whisky','id':str(uuid.uuid4())}],'sources':[]}
        with tempfile.TemporaryDirectory() as directory:
            Path(directory,'series.json').write_text(json.dumps(document))
            apply_market_indexes(tables,lambda key:str(uuid.uuid5(uuid.NAMESPACE_URL,key)),directory)
        return tables

    def test_source_pairs_are_hash_checked_without_creating_offers_or_variants(self):
        tables=self.normalize(self.document)
        self.assertEqual(len(tables['market_price_index_points']),321)
        self.assertNotIn('variants',tables)
        self.assertNotIn('price_observations',tables)
        changed=copy.deepcopy(self.document);changed['indexes'][0]['points'][0]['value']='1'
        with self.assertRaisesRegex(ValueError,'reviewed source fact extraction'):self.normalize(changed)
        changed=copy.deepcopy(self.document);changed['indexes'][0]['content_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'hash mismatch'):self.normalize(changed)

    def test_new_series_cannot_publish_without_explicit_review_flag(self):
        document=copy.deepcopy(self.document);document['indexes'][0].pop('verified')
        self.assertFalse(self.normalize(document)['market_price_indexes'][0]['verified'])

    def test_a_duplicate_month_is_rejected_even_with_a_matching_extraction_hash(self):
        document=copy.deepcopy(self.document);series=document['indexes'][0]
        series['points'].append(copy.deepcopy(series['points'][0]))
        series['evidence_facts'].append(copy.deepcopy(series['evidence_facts'][0]))
        series['point_count']+=1
        series['content_sha256']=hashlib.sha256(json.dumps(series['evidence_facts'],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        with self.assertRaisesRegex(ValueError,'Duplicate monthly index period'):self.normalize(document)


if __name__=='__main__':unittest.main()
