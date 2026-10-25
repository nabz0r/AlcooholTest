# Source date precision and price level

Price records retain the precision printed by their source. A dated retailer capture stores its actual source day in `observed_on`, an empty `observed_period`, and `date_precision: "day"`. A catalogue identifying only a month stores `observed_on: null`, its `YYYY-MM` in `observed_period`, and `date_precision: "month"`. An arbitrary first day is never inserted. The database and model validation require exactly one matching representation, and monthly records have their own uniqueness constraint.

The public product API returns `date: null`, `period: "2003-05"`, and `date_precision: "month"` for a month-only record. A chart may position the period on a monthly time axis, but its label remains the source month. JSON and JSONL dumps preserve both fields. They are optional additive fields in the public schema: older day-based documents still import with their original meaning and identifiers.

`wholesale_list` identifies an original published trade price. For example, the May 2003 Iowa Liquor Quarterly lists Citadelle Gin at USD 19.99 per 750 ml bottle, 88 U.S. proof (44% ABV). The six-bottle case cost is a separate source fact, not the bottle price. This record is neither a consumer retail offer nor a transaction. The source PDF and full provenance are linked from `data/prices/remaining-gap-research.json`.

Coverage can count evidence in a known source year without claiming continuous data. Overall evidence spans may cross markets, formats and price levels; their scope remains explicit. Comparable spans retain the variant, seller, currency, country, known tax basis and retail-versus-wholesale level. Wholesale and retail observations never form one comparable series. Recommendations and unknown price levels are excluded from comparable spans.

For a conservative elapsed span, a month-only earliest observation may fall on that month's final day; a latest observation may fall on its first day. These internal bounds reduce the claimed duration near a twenty-year threshold. They are calculation bounds, never stored observation dates. Source periods remain unchanged in admin, API, exports and coverage reports.

Migration `0020_source_month_precision_and_wholesale_prices` adds these fields, constraints and a monthly lookup index. It follows `0019_provider_review_holds`. Existing archival collectors and acceptance still require the actual capture day; month-only document records do not enter that capture parser.
