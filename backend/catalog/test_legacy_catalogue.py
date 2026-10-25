"""Identity and price-boundary checks for the pre-2007 catalogue adapter."""
import gzip
import unittest

from .legacy_catalogue import parse_legacy_catalogue, parse_drinkshop_capture


TARGET = {
    "product": "suntory-yamazaki-12-years-old", "retailer_id": 2940,
    "legacy_url": "http://www.thewhiskyexchange.com/acatalog/The_Whisky_Exchange__JAPANESE_263.html",
    "legacy_ref": "JAPAN/008", "legacy_titles": ["Suntory Yamazaki"], "legacy_age": "12yo",
}
ORIGINAL = TARGET["legacy_url"]
STAMP = "20060105060218"


def row(reference="JAPAN/008", title="Suntory Yamazaki", age="12yo", volume="70cl", strength="43%", inclusive="43.99"):
    return f'''<TR><TD></TD><TD><A NAME="aJAPAN_2f008"></A><B><!-- SEARCHAID1 -->{title}<!-- SEARCHAID2 --></B></TD><TD></TD><TD>{age}</TD><TD></TD><TD>{strength}</TD><TD>{volume}</TD><TD><Actinic:PRICES PROD_REF="{reference}"><B>&#163;37&#46;44</B><FONT>&#163;{inclusive}&nbsp;Inc.</FONT></Actinic:PRICES></TD><TD></TD></TR>'''


class LegacyCatalogueTests(unittest.TestCase):
    def parse(self, text, **kwargs):
        return parse_legacy_catalogue(text.encode(), TARGET, STAMP, kwargs.get("original", ORIGINAL))

    def test_uses_explicit_tax_inclusive_price_and_captured_bottling(self):
        point = self.parse(row())
        self.assertEqual((point["amount"], point["volume_ml"], point["abv"]), ("43.99", 700, "43"))
        self.assertEqual(point["observed_on"], "2006-01-05")
        self.assertTrue(point["tax_included"])
        self.assertTrue(point["source_url"].endswith("#aJAPAN_2f008"))

    def test_neighbouring_expression_cannot_supply_price(self):
        page = row(reference="JAPAN/027", age="10yo", inclusive="25.50") + row()
        self.assertEqual(self.parse(page)["amount"], "43.99")
        with self.assertRaises(ValueError):
            self.parse(row(reference="JAPAN/027", age="10yo"))

    def test_duplicate_reviewed_reference_is_rejected(self):
        with self.assertRaises(ValueError):
            self.parse(row() + row())

    def test_wrong_name_age_or_unstated_format_is_rejected(self):
        for changed in [row(title="Other whisky"), row(age="18yo"), row(volume="One bottle"), row(strength="86 Proof")]:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                self.parse(changed)

    def test_ex_vat_value_is_never_promoted_without_inclusive_value(self):
        with self.assertRaises(ValueError):
            self.parse(row().replace("Inc.", "ex VAT"))

    def test_only_exact_reviewed_catalogue_url_is_accepted(self):
        for original in [ORIGINAL.replace("thewhiskyexchange.com", "example.com"), ORIGINAL.replace("JAPANESE_263", "GIN_162"), ORIGINAL + "?market=us"]:
            with self.subTest(original=original), self.assertRaises(ValueError):
                self.parse(row(), original=original)

    def test_gzip_payload_is_read_with_same_evidence_hash(self):
        raw = row().encode()
        point = parse_legacy_catalogue(gzip.compress(raw), TARGET, STAMP, ORIGINAL)
        self.assertEqual(point["content_sha256"], self.parse(row())["content_sha256"])


DRINKSHOP_TARGET = {
    "product": "bombay-sapphire", "retailer_id": 2249, "source_retailer_id": 244,
    "legacy_titles": ["BOMBAY SAPPHIRE"], "volume_ml": 700,
}
DRINKSHOP_URL = "http://www.thedrinkshop.com/products/nlpdetail.php?prodid=244"


def drinkshop_offer(size="70cl Bottle", amount="16.19", product="244", unit=""):
    return f'''<tr><td>{size}</td><td>(Immediate)</td><td>£ {amount}</td><td>{unit}</td><td><a href="/pages/basket.php?action=add&amp;prod={product}&amp;price=405">Buy</a></td><td></td></tr>'''


def drinkshop_page(offers, abv="40.0%", title="BOMBAY SAPPHIRE"):
    return f'''<html><meta content="text/html; charset=iso-8859-1"><span class="pTitle">{title}</span><b>ABV:</b> &nbsp; {abv}<br><table class="PriceTable">{offers}</table></html>'''.encode("cp1252")


class DrinkShopCatalogueTests(unittest.TestCase):
    def parse(self, raw):
        return parse_drinkshop_capture(raw, DRINKSHOP_TARGET, "20060323043045", DRINKSHOP_URL)

    def test_pack_and_unit_prices_are_not_single_bottle_offers(self):
        offers = drinkshop_offer("12x 5cl Miniatures", "21.99", unit="£1.83") + drinkshop_offer() + drinkshop_offer("6x 70cl Bottles", "91.38", unit="£15.23")
        point = self.parse(drinkshop_page(offers))
        self.assertEqual((point["amount"], point["volume_ml"], point["abv"]), ("16.19", 700, "40.0"))
        self.assertIsNone(point["tax_included"])

    def test_unknown_abv_and_mismatched_purchase_identity_are_rejected(self):
        for page in [drinkshop_page(drinkshop_offer(), abv=""), drinkshop_page(drinkshop_offer(product="999")), drinkshop_page(drinkshop_offer(), title="BOMBAY BRAMBLE")]:
            with self.subTest(page=page), self.assertRaises(ValueError):
                self.parse(page)

    def test_duplicate_same_size_offers_are_ambiguous(self):
        with self.assertRaises(ValueError):
            self.parse(drinkshop_page(drinkshop_offer() + drinkshop_offer(amount="15.23")))

    def test_recommendation_abv_and_unreviewed_urls_are_not_accepted(self):
        page = drinkshop_page(drinkshop_offer(), abv="") + b"<b>ABV:</b> 40%"
        with self.assertRaises(ValueError):
            self.parse(page)
        with self.assertRaises(ValueError):
            parse_drinkshop_capture(drinkshop_page(drinkshop_offer()), DRINKSHOP_TARGET, "20060323043045", DRINKSHOP_URL + "&prodid=999")

