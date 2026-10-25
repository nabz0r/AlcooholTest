"""Conservative adapter for reviewed, pre-2007 Actinic retailer catalogue rows.

A category page is never treated as a single product. The reviewed product code,
named row, age, explicit volume, strength and VAT-inclusive price must all agree.
"""
import gzip
import hashlib
import html
import re
import urllib.parse
from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO


def _plain(value):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())


def parse_legacy_catalogue(raw, target, timestamp, original):
    if not re.fullmatch(r"\d{14}", timestamp):
        raise ValueError("Invalid capture timestamp")
    source = urllib.parse.urlparse(original)
    expected = urllib.parse.urlparse(target["legacy_url"])
    if source.hostname not in ["www.thewhiskyexchange.com", "thewhiskyexchange.com"]:
        raise ValueError("Unreviewed catalogue host")
    if source.path != expected.path or source.query or not re.fullmatch(
        r"/acatalog/The_Whisky_Exchange__[A-Za-z0-9_]+\.html", source.path
    ):
        raise ValueError("Capture does not match the reviewed category URL")
    if raw.startswith(b"\x1f\x8b"):
        with gzip.GzipFile(fileobj=BytesIO(raw)) as stream:
            raw = stream.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("Catalogue response too large")
    encoding = "iso-8859-1" if b"charset=iso-8859-1" in raw.lower() else "utf-8"
    text = raw.decode(encoding, errors="replace")
    reference = str(target["legacy_ref"])
    if not re.fullmatch(r"[A-Za-z]+/[A-Za-z0-9]+", reference):
        raise ValueError("Invalid reviewed Actinic product reference")
    matches = []
    for heading in re.finditer(r"<!--\s*SEARCHAID1\s*-->(.*?)<!--\s*SEARCHAID2\s*-->", text, re.S | re.I):
        start = text.lower().rfind("<tr", 0, heading.start())
        end = text.lower().find("</tr>", heading.end())
        if start < 0 or end < 0:
            continue
        row = text[start:end + 5]
        refs = re.findall(r"<Actinic:PRICES\b[^>]*\bPROD_REF=[\"']([^\"']+)[\"']", row, re.I)
        if refs == [reference]:
            matches.append((heading, row))
    if len(matches) != 1:
        raise ValueError("Reviewed product reference is absent or duplicated")
    heading, row = matches[0]
    title = _plain(heading.group(1))
    cells = [_plain(c) for c in re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S | re.I)]
    if len(cells) != 9:
        raise ValueError("Unsupported catalogue row structure")
    if title.casefold() not in [v.casefold() for v in target["legacy_titles"]]:
        raise ValueError("Catalogue product name does not match reviewed reference")
    if cells[3].casefold() != target.get("legacy_age", "").casefold():
        raise ValueError("Catalogue age does not match reviewed bottling")
    volume = re.fullmatch(r"(\d+(?:\.\d+)?)\s*cl", cells[6], re.I)
    strength = re.fullmatch(r"(\d+(?:\.\d+)?)\s*%", cells[5])
    if not volume or not strength:
        raise ValueError("Explicit catalogue volume or ABV is missing")
    prices = re.findall(r"£\s*([\d,]+\.\d{2})\s+Inc\.", cells[7], re.I)
    if len(prices) != 1:
        raise ValueError("Unique VAT-inclusive catalogue price is missing")
    amount = Decimal(prices[0].replace(",", ""))
    if not 0 < amount < 1000000 or not 0 < Decimal(strength.group(1)) <= 100:
        raise ValueError("Catalogue amount or strength outside accepted bounds")
    anchor = re.search(r"<a\s+name=[\"']([^\"']+)[\"']", row, re.I)
    observed = datetime.strptime(timestamp, "%Y%m%d%H%M%S").date().isoformat()
    return {
        "product": target["product"], "retailer_id": target["retailer_id"],
        "legacy_product_ref": reference, "title": " ".join([title, cells[3]]).strip(),
        "observed_on": observed, "timestamp": timestamp, "amount": format(amount, ".2f"),
        "currency": "GBP", "country": "United Kingdom", "retailer": "The Whisky Exchange",
        "volume_ml": round(Decimal(volume.group(1)) * 10), "abv": strength.group(1),
        "tax_included": True, "basis": "archive_capture", "parser": "actinic_catalogue_row",
        "source_url": "https://web.archive.org/web/" + timestamp + "/" + original + ("#" + anchor.group(1) if anchor else ""),
        "original_url": original, "content_sha256": hashlib.sha256(raw).hexdigest(),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "date_scope": "Archive capture date; not a transaction or guaranteed start of the offer.",
        "notes": "Named, reviewed Actinic product row; volume and strength are transcribed from this historical listing and do not assert an unchanged formulation.",
    }


def parse_drinkshop_capture(raw, target, timestamp, original):
    """Read one reviewed bottle row from TheDrinkShop's old product template."""
    if not re.fullmatch(r"\d{14}", timestamp):
        raise ValueError("Invalid capture timestamp")
    source = urllib.parse.urlparse(original)
    expected_id = str(target["source_retailer_id"])
    if source.hostname not in ["www.thedrinkshop.com", "thedrinkshop.com"] or source.path != "/products/nlpdetail.php":
        raise ValueError("Unreviewed DrinkShop product URL")
    if urllib.parse.parse_qs(source.query) != {"prodid": [expected_id]}:
        raise ValueError("Capture URL does not match the reviewed DrinkShop identifier")
    if raw.startswith(b"\x1f\x8b"):
        with gzip.GzipFile(fileobj=BytesIO(raw)) as stream:
            raw = stream.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("Catalogue response too large")
    text = raw.decode("cp1252" if b"charset=iso-8859-1" in raw.lower() else "utf-8", errors="replace")
    headings = list(re.finditer(r"<(?P<tag>span|div)\b[^>]*class=(?:[\"']pTitle[\"']|pTitle)(?=[\s>])[^>]*>(?P<title>.*?)</(?P=tag)>", text, re.S | re.I))
    if len(headings) != 1:
        raise ValueError("Unique primary DrinkShop product title is missing")
    title = _plain(headings[0].group("title"))
    if title.casefold() not in [v.casefold() for v in target["legacy_titles"]]:
        raise ValueError("Primary DrinkShop title does not match the reviewed expression")
    tables = list(re.finditer(r"<table\b[^>]*class=(?:[\"']PriceTable[\"']|PriceTable)(?=[\s>])[^>]*>(.*?)</table>", text, re.S | re.I))
    if len(tables) != 1 or tables[0].start() < headings[0].end():
        raise ValueError("Unique primary DrinkShop pricing table is missing")
    details = text[headings[0].end():tables[0].start()]
    # Earlier templates use an ABV-labelled numeric value without a trailing %.
    # Require the following line break so other nearby numbers cannot supply it.
    strengths = re.findall(r"<b>\s*ABV:\s*</b>\s*(\d+(?:\.\d+)?)\s*%?\s*<br\s*/?>", html.unescape(details), re.I)
    if len(strengths) != 1 or not 0 < Decimal(strengths[0]) <= 100:
        raise ValueError("Explicit primary DrinkShop ABV is missing")
    offers = []
    for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", tables[0].group(1), re.S | re.I):
        cells = [_plain(c) for c in re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S | re.I)]
        if len(cells) != 6:
            continue
        bottle = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(cl|ml|litre)\s+Bottle", cells[0], re.I)
        if not bottle:
            continue
        scale = {"cl": 10, "ml": 1, "litre": 1000}[bottle.group(2).lower()]
        volume = round(Decimal(bottle.group(1)) * scale)
        if volume != int(target["volume_ml"]):
            continue
        amount = re.fullmatch(r"£\s*([\d,]+\.\d{2})", cells[2])
        if not amount:
            raise ValueError("A single explicit GBP bottle price is required")
        # The purchase link must identify this product, rather than a sidebar or
        # nearby recommendation. Unit prices and case discounts are ignored.
        purchase = re.search(r"href=[\"']([^\"']*basket\.php[^\"']+)[\"']", row, re.I)
        params = urllib.parse.parse_qs(urllib.parse.urlparse(html.unescape(purchase.group(1))).query) if purchase else {}
        if params.get("prod") != [expected_id]:
            raise ValueError("DrinkShop price row does not identify the reviewed product")
        number = Decimal(amount.group(1).replace(",", ""))
        if not 0 < number < 1000000:
            raise ValueError("DrinkShop bottle price outside accepted bounds")
        offers.append((number, volume, cells[1]))
    if len(offers) != 1:
        raise ValueError("Unique reviewed single-bottle format is missing")
    amount, volume, availability = offers[0]
    return {
        "product": target["product"], "retailer_id": target["retailer_id"],
        "source_retailer_id": int(expected_id), "title": title,
        "observed_on": datetime.strptime(timestamp, "%Y%m%d%H%M%S").date().isoformat(),
        "timestamp": timestamp, "amount": format(amount, ".2f"), "currency": "GBP",
        "country": "United Kingdom", "retailer": "TheDrinkShop.com",
        "volume_ml": volume, "abv": strengths[0], "tax_included": None,
        "availability": availability,
        "basis": "archive_capture", "parser": "drinkshop_primary_price_table",
        "source_url": "https://web.archive.org/web/" + timestamp + "/" + original,
        "original_url": original, "content_sha256": hashlib.sha256(raw).hexdigest(),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "date_scope": "Archive capture date; not a transaction or guaranteed start of the offer.",
        "notes": "Reviewed product title and exact single-bottle row. Captured ABV is explicit. VAT inclusion is unknown in this page and has not been inferred from another date or source.",
    }
