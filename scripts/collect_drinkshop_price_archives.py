#!/usr/bin/env python3
"""Collect reviewed pre-2007 TheDrinkShop bottles; stage factual candidates only."""
import concurrent.futures
import json
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from catalog.price_archive import fetch
from catalog.legacy_catalogue import parse_drinkshop_capture


def get(url, path):
    for attempt in range(3):
        try:
            return fetch(url, path)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))


def collect_one(target, cache):
    report = {"indexes": [], "points": [], "errors": []}
    ident = target["source_retailer_id"]
    query = {"url": target["legacy_url"], "output": "json", "filter": ["statuscode:200", "mimetype:text/html"],
             "collapse": "timestamp:4", "from": "1999", "to": "2006", "limit": "20"}
    url = "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(query, doseq=True)
    try:
        rows = json.loads(get(url, cache / f"drinkshop-{ident}-index.json"))[1:]
        report["indexes"].append({"product": target["product"], "url": url, "captures": len(rows)})
        for row in rows:
            stamp, original = row[1], row[2]
            try:
                destination = cache / f"drinkshop-{ident}-{stamp}.html"
                was_cached = destination.exists()
                raw = get("https://web.archive.org/web/" + stamp + "id_/" + original, destination)
                point = parse_drinkshop_capture(raw, target, stamp, original)
                report["points"].append(point)
                print(target["product"], stamp, point["amount"], point["volume_ml"], point["abv"], flush=True)
                if not was_cached:
                    time.sleep(1)
            except Exception as exc:
                report["errors"].append({"product": target["product"], "timestamp": stamp,
                                         "source_url": "https://web.archive.org/web/" + stamp + "/" + original,
                                         "error": str(exc)[:200]})
    except Exception as exc:
        report["errors"].append({"product": target["product"], "index_url": url, "error": str(exc)[:200]})
    return report


def main():
    cache = ROOT / "work" / "archive-v5"
    cache.mkdir(parents=True, exist_ok=True)
    targets = json.loads((ROOT / "data" / "prices" / "drinkshop-targets.json").read_text())
    report = {"scope": "Actual pre-2007 retailer product captures. Reviewed primary titles, explicit ABV and exact single-bottle price rows are required; packs and unit prices are rejected. VAT treatment remains unknown where not stated in the capture.",
              "retrieved_at": datetime.now(timezone.utc).isoformat(), "indexes": [], "points": [], "errors": []}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(lambda target: collect_one(target, cache), targets):
            for key in ["indexes", "points", "errors"]:
                report[key].extend(result[key])
            (cache / "drinkshop-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print({"parsed": len(report["points"]), "errors": len(report["errors"])}, flush=True)


if __name__ == "__main__":
    main()
