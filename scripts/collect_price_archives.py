#!/usr/bin/env python3
"""Collect bounded public archival facts; never publish an inferred price."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from catalog.price_archive import collect
if __name__=='__main__':
 targets=json.loads((ROOT/'data/prices/targets.json').read_text())
 report=collect(targets,ROOT/'work/price-archive',max_captures=20,notify=lambda p:print(p['product'],p['observed_on'],p['amount'],flush=True))
 # Collection stages candidates. The reviewed distribution changes only after explicit review/merge.
 (ROOT/'data/prices/archive-expansion.json').write_text(json.dumps(report,indent=2)+'\n')
 print({'parsed':len(report['points']),'errors':len(report['errors'])},flush=True)
