# A dated price notebook — Volume 05

Every price belongs to a named bottling, source context and source date or period. A current offer cannot establish an earlier price. A twenty-year interval between two records cannot establish twenty years of continuous coverage.

## The shipped snapshot

The reviewed distribution dated 25 October 2026 contains **613 individual price observations**, with price evidence for each of the **55 canonical products**. The oldest accepted record is dated 14 August 2001. These are source facts, not a live price feed or purchase ledger.

| Stored basis | Records | Meaning |
| --- | ---: | --- |
| `archive_capture` | 537 | Actual archived retailer offers; capture date is not a transaction date. |
| `retail_offer` | 57 | Current source views on 25 October 2026, including the initial Luxembourg observations. |
| `launch_msrp` | 12 | Manufacturer/importer recommendations in dated launch or introduction announcements. |
| `historical_ad` | 6 | Prices in original dated advertisements or retailer publications. |
| `wholesale_list` | 1 | A published trade price, separate from consumer retail. |

There is also **one separate Kakubin survey series with 321 monthly points**, January 2000–September 2026. These statistics are not included in the 613 bottle-price observations.

The portable [seed](../data/catalog/seed.json) contains the accepted records. [Generated coverage](../data/prices/coverage.json) reports each product's actual start/end, date precision, years with evidence, gaps, price bases and comparable span. The [Volume 04 report](../data/prices/archive-research.json) retains provenance for its initial 38 captures; it is not the current total.

## What “twenty years” means

**29 products have an overall evidence span of at least twenty years.** An overall span can cross markets, sellers, bottle sizes, strengths and price levels. Citadelle has a May 2003 wholesale quotation and later retail offers. These establish different source facts; joining them does not measure consumer price appreciation.

**Five products currently reach twenty years within a comparable series.** Comparable spans retain the same variant, seller, currency, country, known tax basis and retail/wholesale level. MSRP and unknown price levels are excluded. Missing years remain missing. Currency conversion, inflation adjustment, resale returns, investment performance and daily values are not inferred.

**23 products cannot have a twenty-year branded history as of this snapshot.** The registry has 21 sourced post-2006 introductions plus two owner-confirmed brand bounds: Malfy appeared in 2016 and Don Papa in 2012, while their expression-specific first-release years remain unknown. `release_not_before_year` preserves a bound separately from `first_release_year`. Distillery foundation, maturation age and category history are not substituted for a product launch.

Three other early bottle-price gaps remain explicit:

- **Kakubin:** individual observations begin in 2017. Its independent 2000–2026 monthly survey series does not create early retailer observations.
- **Four Roses Small Batch:** the producer confirms September 2006 introduction; the earliest accepted exact-format bottle price is from 2008. No 2006 MSRP or retail price was verified.
- **Diplomático Reserva Exclusiva:** the earliest accepted exact-format price is from 2008. Older bottles, vintage years and modern auctions do not supply a pre-2007 retail price.

The [launch registry](../data/prices/coverage-research.json), [additional launch evidence](../data/prices/additional-launch-research.json) and [remaining-gap report](../data/prices/remaining-gap-research.json) retain the scope and unresolved work. Field presence and completed collection jobs do not mean a finished historical series.

## Dates keep their source precision

A daily archived offer stores the actual capture date in `observed_on`, an empty `observed_period`, and `date_precision: "day"`. A source stating only a month stores `observed_on: null`, a `YYYY-MM` period and `date_precision: "month"`. Admin, API and public dumps preserve that distinction.

The May 2003 Iowa Liquor Quarterly quotation for Citadelle is **USD 19.99 per 750 ml bottle**, printed at **88 U.S. proof**, equivalent to 44% ABV. Its six-bottle case costs USD 119.94. The table explicitly identifies a wholesale list. The cover supplies May 2003, not May 1; later archive-capture, file-modification and retrieval dates are not the price date. Tax treatment is unknown. The complete PDF was integrity checked and its cover and relevant table visually reviewed; its bytes remain outside the public bundle.

Elapsed spans use conservative bounds for month-only evidence: the earliest observation could fall at month end, and the latest at month start. Calculation bounds are never stored as invented observation days. See [source-date fields and migrations](SOURCE_DATES.md).

## Offers, recommendations and statistics

The bottle page separates series by currency, country, volume, ABV, retailer, tax treatment and price level. `null` tax or promotion means unknown. It does not mean tax excluded, a discount or an ordinary undiscounted offer. A manufacturer recommendation, wholesale quote, shop offer and completed auction transaction have different meanings; no conversion between them is inferred.

Kakubin's **Japan monthly city-price median** is an independent `market_price_indexes` record with `market_price_index_points`. It retains the median statistic, JPY unit, 700 ml reference, tax scope, survey method and specification changes. It is not one retailer's price or a transaction. See [Kakubin research](../data/prices/kakubin-research.json) and [market-index sources](../data/prices/market-indexes/). January 2000 is not converted into an invented first-of-month bottle observation.

Historical labels retain their context too. Appleton's owner confirms Signature was originally released as V/X in 1987 and separately confirms the 2015 rename without a liquid change at that rename. This supports four 2003–2006 V/X offers, all 700 ml / 40%, VAT included. It does not establish identical markets, age statements or formulations across every decade. [Appleton predecessor evidence](../data/prices/appleton-predecessor-research.json).

## Maintain the notebook from admin

Open **Admin → Products → Photographs & price archives** at `/admin/catalog/product/research/`. The all-55 workbench shows hosted-image gaps, external references, actual price years, overall/comparable spans and reviewed collection targets. Download its coverage/config JSON when needed. A year with one source record is different from a fully sampled year.

1. Open a product dossier to manage bottlings, sources, prices, expression launch years and earliest brand bounds.
2. Edit a **Price archive target**: reviewed retailer ID, permitted title words, exclusions, known URL generations and optional Actinic/TheDrinkShop mappings.
3. Queue one target or all enabled targets. Existing queued/running targets are skipped; progress and provider errors remain visible.
4. Open **Discovery candidates**, resolve the canonical product, inspect the primary title, format, price node, date and tax scope, then use **Accept reviewed archival prices**.
5. Regenerate public JSON/JSONL or a **Source Memento** bundle after review. Collection and publication are separate actions.

Acceptance creates no new canonical product and does not silently reprice an existing observation. Configuration and editorial changes are audited. Provider review holds preserve unresolved anomalies, including historical Campari 15% and Disaronno 29% records. Those values are not normalized to modern strengths. Clear a hold only after resolving the actual conflict.

A document-only monthly quote uses the ordinary price editor with its exact period and price basis. It does not enter a parser requiring a daily Wayback capture. Schema and PostgreSQL constraints reject competing day/month representations and duplicate observations within the same declared scope.

## Collection and reproduction

The archived collection uses reviewed retailer IDs, bounded CDX queries and actual captured HTML. The product parser reads known primary offer nodes, not sidebar recommendations, unit prices or basket totals. The Actinic adapter requires one reviewed `PROD_REF`, title, age, explicit volume/ABV and VAT-inclusive price within the same row. TheDrinkShop has a separate source identity and exact primary bottle-price table. A category page is never treated as one product.

From the repository root:

```sh
# Collect source candidates; inspect results and errors before accepting them.
python3 scripts/collect_price_archives.py
python3 scripts/collect_legacy_price_archives.py
python3 scripts/collect_drinkshop_price_archives.py

# After review, rebuild the accepted portable data and coverage.
python3 scripts/build_seed.py
python3 scripts/build_data_exports.py
python3 scripts/build_research_audit.py
```

Collectors cache source responses and checkpoint reports. A denied request or unsupported layout is not evidence that a price did not exist. Broad Internet coverage is not guaranteed by success status. [Current browser-source offers](../data/prices/current-source-research.json) have explicitly scoped fact-extract hashes; they are not labeled as preserved full HTML or automatically reproduced daily observations.

The original subset, expanded captures, documents, announcements and current views retain separate reports under [`data/prices/`](../data/prices/). The seed and generated coverage are the consolidated accepted view. Do not add report lengths together or count held candidates as published prices.

## Keep facts portable

Raw copyrighted retailer pages, full newspaper/catalogue PDFs and review renders stay in ignored local research directories. Public records preserve extracted price facts, source links, date precision and hash scope. A hash of extracted facts does not authenticate an unavailable complete source page.

[Source Memento](MEMENTO.md) preserves public fact capsules and their provenance with immutable hashes. Its optional ZIP contains only already hosted, individually licensed bottle photographs with credit/license manifests. It does not fetch arbitrary source URLs, mirror external-only photographs or redistribute full copyrighted publications. Public exports exclude accounts, private observations and moderation queues; SQL backups remain separate and private.
