#!/usr/bin/env python3
"""Collect reviewed Actinic rows from actual annual captures through 2006."""
import json
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from catalog.price_archive import fetch
from catalog.legacy_catalogue import parse_legacy_catalogue


def get(url, path):
    for attempt in range(3):
        try:
            return fetch(url, path)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))


def main():
    cache = ROOT / "work" / "archive-v5"
    cache.mkdir(parents=True, exist_ok=True)
    targets = json.loads((ROOT / "data" / "prices" / "legacy-targets.json").read_text())
    report = {"scope": "Actual pre-2007 category captures, accepted only for exact reviewed Actinic product rows with named item, age, explicit volume, ABV and VAT-inclusive GBP price. Missing observations remain missing.",
              "retrieved_at": datetime.now(timezone.utc).isoformat(), "indexes": [], "points": [], "errors": []}
    for target in targets:
        category = target["legacy_url"].split("The_Whisky_Exchange__", 1)[1].removesuffix(".html")
        query = {"url": target["legacy_url"], "output": "json", "filter": ["statuscode:200", "mimetype:text/html"],
                 "collapse": "timestamp:4", "from": "1999", "to": "2006", "limit": "20"}
        url = "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(query, doseq=True)
        try:
            rows = json.loads(get(url, cache / f"acatalog-{category}-index.json"))[1:]
            report["indexes"].append({"product": target["product"], "url": url, "captures": len(rows)})
            for row in rows:
                stamp, original = row[1], row[2]
                try:
                    raw = get("https://web.archive.org/web/" + stamp + "id_/" + original, cache / f"acatalog-{category}-{stamp}.html")
                    point = parse_legacy_catalogue(raw, target, stamp, original)
                    report["points"].append(point)
                    print(target["product"], stamp, point["amount"], point["volume_ml"], point["abv"], flush=True)
                except Exception as exc:
                    report["errors"].append({"product": target["product"], "timestamp": stamp,
                                             "source_url": "https://web.archive.org/web/" + stamp + "/" + original,
                                             "error": str(exc)[:200]})
                time.sleep(1)
        except Exception as exc:
            report["errors"].append({"product": target["product"], "index_url": url, "error": str(exc)[:200]})
        (cache / "legacy-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print({"parsed": len(report["points"]), "errors": len(report["errors"])}, flush=True)


if __name__ == "__main__":
    main()
