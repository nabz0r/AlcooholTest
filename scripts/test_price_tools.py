"""Reject chronologically impossible source imports before creating public facts."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid
import enrich_prices


class PriceToolTests(unittest.TestCase):
    def test_seed_enrichment_respects_earliest_bound_without_an_exact_launch_year(self):
        root=Path(__file__).resolve().parents[1]
        point=copy.deepcopy(next(row for row in json.loads((root/'data/prices/archive-research.json').read_text())['points'] if row['product']=='malfy-originale'))
        # Invalid chronology exists only in this deliberately rejected fixture.
        point['source_url']=point['source_url'].replace('/web/'+point['timestamp']+'/', '/web/20150615120000/')
        point.update(timestamp='20150615120000',observed_on='2015-06-15')
        tables={'products':[{'slug':point['product'],'id':str(uuid.uuid4())}],'sources':[],'variants':[],'price_observations':[]}
        with tempfile.TemporaryDirectory() as directory:
            temporary=Path(directory);(temporary/'data/prices').mkdir(parents=True)
            (temporary/'data/prices/archive-research.json').write_text(json.dumps({'points':[point]}))
            (temporary/'data/prices/coverage-research.json').write_text(json.dumps([{'product':point['product'],'first_release_year':None,'release_not_before_year':2016}]))
            with patch.object(enrich_prices,'ROOT',temporary),self.assertRaisesRegex(ValueError,'earliest possible year'):
                enrich_prices.apply_prices(tables,lambda key:str(uuid.uuid5(uuid.NAMESPACE_URL,key)))
        self.assertEqual(tables['sources'],[])
        self.assertEqual(tables['variants'],[])
        self.assertEqual(tables['price_observations'],[])


if __name__=='__main__':unittest.main()
