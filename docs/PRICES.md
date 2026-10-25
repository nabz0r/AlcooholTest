# A dated price notebook

Admin → Price observations → Add records a specific bottling, observation date, amount, ISO-style three-letter currency, country, retailer, tax inclusion, promotion flag and reference source. Editors can enter sourced historical observations or import them in a versioned catalogue JSON. A storefront's current price is not evidence of its earlier prices.

The product page groups chart series by currency, country, volume, ABV, retailer and tax treatment. It never averages currencies, merges formats, converts exchange rates or manufactures past values. Points are genuine stored observations; connecting lines simply join those observations, not daily reconstructed prices. Two first observations were curated from Luxembourg seller pages consulted on 2026-10-25. They start the notebook; they do not constitute a historical trend. Commercial offer scraping is not enabled; future adapters require seller permission, market/variant matching, source timestamps and an explicit observation schedule.

The optimized composite index covers variant, currency, country and observation date. A uniqueness constraint prevents duplicate same-day retailer/market records for the same bottling and currency. Price records enter public JSON/JSONL and retain their source references.
