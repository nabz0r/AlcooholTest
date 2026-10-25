# Monthly market context

Kakubin includes 321 actual monthly survey values from January 2000 through September 2026. They appear in a separate chart on its product page. Each point stores its real `YYYY-MM` period: no arbitrary day, interpolation or synthetic retailer observation is introduced.

The source is [Nedan Hakusho's whisky survey page](https://nedan-hakusho.jp/items/2033/). This independent service calculates a median across available city prices from Japan's Retail Price Survey. The [government dataset reference](https://www.e-stat.go.jp/dbview?sid=0003421913) supplies context; this project has not downloaded or independently recomputed the primary city records. The imported values were read from all 321 visible accessible chart tooltips and checked against the page's latest twelve-month table and published checkpoints. The original CSV was unavailable during this collection; no CSV download or CSV checksum is claimed.

The survey unit is one 700 ml bottle, nominal JPY including tax. Survey brand and strength definitions change: Shin Kakubin becomes Kakubin in July 2005, and the specified strength interval narrows in January 2007. The source joins those observations. This is documented brand lineage, not proof of an identical liquid or exact ABV across 26 years. It remains separate from format-specific offers, launch recommendations and transactions. Historical city counts are unknown; the source's latest count must not be copied backward.

## Editorial management

`Market price indexes` in Django admin holds the product, source, currency, territory, statistic, unit, methodology and source-extraction hash. `Market price index points` contains independently editable monthly values, with filtering and search by series or period. Verification defaults to off. Only verified series belonging to published products appear in the public API and public JSON/JSONL dumps. Changes use the existing audit trail. A series can be withdrawn immediately by clearing `Verified`.

The database enforces one point per series/month, a positive numeric value and a valid monthly period. It does not force continuity: genuine missing months remain missing. The chart does not connect a line across a missing month.

## Reproduction and interchange

The source facts and extraction metadata are in `data/prices/market-indexes/kakubin.json`. `evidence_facts` contains only the exact period/value pairs. Its canonical UTF-8 JSON SHA-256 is checked by `scripts/apply_market_indexes.py` before seed generation. This is a fact-extraction hash, not an original page, CSV or government-dataset hash. The seed step creates deterministic identifiers without adding market variants or retailer prices.

Migration `0018_monthly_market_price_indexes` creates the normalized metadata and point tables. Public dump tables `market_price_indexes` and `market_price_index_points` are additive and optional, so older documents remain valid. Foreign keys and repeated periods are validated before transactional import. Existing JSON/JSONL export and import jobs include the new records. The product API returns `market_indexes`, with source metadata and points ordered by month; empty or unverified series do not appear.

The public chart uses an SVG line, real month labels, hover values, an expandable methodology and a scrollable complete month table. Numeric facts retain source attribution. No remote chart image or copied source-page artwork is distributed.
