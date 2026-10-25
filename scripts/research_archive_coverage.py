#!/usr/bin/env python3
"""Research reviewed retailer IDs, preserving failed captures and missing years.

Raw copyright pages stay in the ignored work directory. This helper does not
publish prices or create product identities. A successful parse remains a
candidate for editorial review.
"""
import argparse
import concurrent.futures
import json
import re
import shutil
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from catalog import price_archive


def fetch_with_retries(url, destination):
    for attempt in range(3):
        try:
            return price_archive.fetch(url, destination)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))


def index_rows(target, pattern, cache):
    ident = int(target["retailer_id"])
    name = f"{ident}-{pattern}-index.json"
    prior = ROOT / "work" / "price-archive" / f"{ident}-index.json"
    if pattern == "legacy" and prior.exists() and not (cache / name).exists():
        shutil.copyfile(prior, cache / name)
    query = {
        "url": f"thewhiskyexchange.com/P-{ident}.aspx" if pattern == "legacy"
        else f"thewhiskyexchange.com/p/{ident}/*",
        "output": "json", "filter": ["statuscode:200", "mimetype:text/html"],
        "collapse": "timestamp:4", "from": "1999", "to": "2026", "limit": "200",
    }
    url = "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(query, doseq=True)
    rows = json.loads(fetch_with_retries(url, cache / name))
    return url, rows[1:]


def research_one(target, cache, fetch_only=False):
    ident = int(target["retailer_id"])
    indexes, errors, records, rows = [], [], [], []
    for pattern in ["legacy", "modern"]:
        try:
            url, found = index_rows(target, pattern, cache)
            canonical = [r for r in found if not urllib.parse.urlparse(r[2]).query
                         and re.match(rf"^/(?:[Pp]-{ident}\.aspx|[Pp]/{ident}/)", urllib.parse.urlparse(r[2]).path)
                         and "%20" not in r[2] and "%C2" not in r[2]]
            indexes.append({"product": target["product"], "pattern": pattern,
                            "url": url, "indexed": len(found), "canonical": len(canonical)})
            rows.extend(canonical)
        except Exception as exc:
            errors.append({"product": target["product"], "pattern": pattern, "error": str(exc)[:200]})
    # One initial annual capture across known path aliases. Missing or out-of-stock
    # prices are recorded; no interpolation or assumed volume is introduced.
    annual = {}
    for row in sorted(rows, key=lambda row: row[1]):
        annual.setdefault(row[1][:4], row)
    for row in annual.values():
        stamp, original = row[1], row[2]
        destination = cache / f"{ident}-{stamp}.html"
        prior = ROOT / "work" / "price-archive" / destination.name
        if prior.exists() and not destination.exists():
            shutil.copyfile(prior, destination)
        source_url = "https://web.archive.org/web/" + stamp + "/" + original
        was_cached = destination.exists()
        try:
            raw = fetch_with_retries("https://web.archive.org/web/" + stamp + "id_/" + original, destination)
            if not fetch_only:
                records.append(price_archive.parse_capture(raw, target, stamp, original))
        except Exception as exc:
            errors.append({"product": target["product"], "timestamp": stamp,
                           "source_url": source_url, "cache": str(destination.relative_to(ROOT)),
                           "error": str(exc)[:200]})
        if not was_cached:
            time.sleep(1)
    print(target["product"], "annual", len(annual), "parsed", len(records), "errors", len(errors), flush=True)
    return indexes, records, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch-only", action="store_true")
    parser.add_argument("--workers", type=int, choices=[1, 2], default=2)
    args = parser.parse_args()
    cache = ROOT / "work" / "archive-v5"
    cache.mkdir(parents=True, exist_ok=True)
    targets = json.loads((ROOT / "data" / "prices" / "targets.json").read_text())
    report = {"scope": "Actual annual archive captures of reviewed retailer IDs across legacy and modern URL aliases. No missing dates or prices are interpolated. Exact bottling details are required; raw pages remain local only.",
              "retrieved_at": datetime.now(timezone.utc).isoformat(), "targets": len(targets),
              "fetch_only": args.fetch_only, "indexes": [], "points": [], "errors": []}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = {pool.submit(research_one, t, cache, args.fetch_only): t for t in targets}
        for future in concurrent.futures.as_completed(pending):
            try:
                indexes, points, errors = future.result()
                report["indexes"].extend(indexes)
                report["points"].extend(points)
                report["errors"].extend(errors)
            except Exception as exc:
                report["errors"].append({"product": pending[future]["product"], "error": str(exc)[:200]})
            (ROOT / "data" / "prices" / "archive-expansion.json").write_text(json.dumps(report, indent=2) + "\n")
    print({"targets": len(targets), "parsed": len(report["points"]), "errors": len(report["errors"])}, flush=True)


if __name__ == "__main__":
    main()
