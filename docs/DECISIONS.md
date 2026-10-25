# The discovery and decision desk — Volume 03

## Problem and intended value

The gallery is an invitation, but discovery needs more than an attractive object. Visitors need to narrow the collection, understand why an item appears, compare like attributes and recognize missing information before forming an opinion. This revision adds those tools without pretending that a sparse review corpus or secret recipe can support a reliable taste recommender.

The design rationale drew on primary UX research from [Baymard's filtering study](https://baymard.com/blog/ecommerce-filter-ui) and [comparison scannability research](https://baymard.com/blog/user-friendly-comparison-tools). The relevant principles are visible applied filters, separate sorting, aligned attributes, difference filtering and persistent column headings. These research references guide implementation; this product has not undergone a Baymard audit.

## Discovery

`/discover/` is a public, shareable search desk. Category, brand origin, any selected ingredient navigation group, documented bottling strength, minimum record coverage and photograph availability can be combined. Filters apply through an explicit button; this avoids moving results while a phone visitor is still choosing controls. Selected filters appear as removable chips. Sorting by Most documented or House/name is distinct from filtering. Counts, pagination, loading, validation errors and empty states remain visible. Query parameters restore the direction after a product visit or browser Back. Share search copies the URL with a selectable fallback if clipboard access is unavailable.

Groups are an editorial navigation vocabulary, stored in `Ingredient.navigation_group` and editable in the admin. Flowers, citrus, leaves/herbs, spices/seeds, fruit/kernels, roots and grains classify indexed ingredient records; they are not biological taxonomic families or verified tasting notes. Unclassified ingredients remain searchable by name but do not match a group. `data/navigation/ingredient-groups.json` reproduces the initial mapping. Several ingredients have more than one sensible culinary grouping; the single assigned group is a navigational choice rather than an exclusive botanical fact.

Multiple selections within the ingredient-group facet use OR; different filter types combine with AND. Facet counts honor the other current constraints and exclude the selected ingredient-group constraint, allowing visitors to see alternative group directions. Strength min/max must match the same recorded market bottling. Unknown ABV does not satisfy a strength filter. Country means brand origin, not a claim that every market bottling was manufactured there.

## Documentation coverage

Six equally weighted areas count once each: recorded bottling specification, source-linked ingredient membership, attributed nonempty history, a sourced locality, a front reference photograph or editorial product photo, and dated price observations. The result is displayed as `n / 6 areas documented`. It is not a quality, safety, authenticity, evidence-grade or completeness percentage. One dated price record satisfies the price area but does not establish a trend; a partial ingredient list satisfies ingredient presence but does not disclose the full formula. This limitation is exposed beside the controls and in the product explanation.

Coverage uses indexed SQL EXISTS checks; it does not hydrate the entire catalogue or count duplicated join rows. Public results remain canonical and published. Discovery fetches at most 24 records per page, uses stable documented/name ordering, and has a query-budget integration test. Redis caches are invalidated by editorial model changes.

## Documented connections

Product pages offer three same-category canonical alternatives ranked first by count of shared indexed ingredient IDs, then by record coverage and a stable name order. Each result states the shared names; zero overlap uses a Same category / no overlap established explanation. There is no opaque affinity percentage or recommendation learned from nonexistent community votes. Partial records cannot establish that an unrecorded ingredient is absent. Clicking Compare these two intentionally replaces the current shortlist with that pair.

## Comparison

`/compare/?bottles=slug-a,slug-b` opens a shareable shortlist, capped at four validated slugs. Public product requests are settled independently: one unavailable record does not discard the rest. Selected items can be removed; the persistent comparison tray keeps the next action visible from discovery or a product.

The matrix aligns identity, origin, bottlings, disclosure and documentation. Show differences only hides equal indexed values, with sticky headings and horizontal scrolling. A separate expandable ingredient matrix distinguishes Indexed from Not documented; it does not assert absence. Publisher perspectives remain source-attributed and are never averaged with local monkey votes. Share comparison preserves the selected records and differences toggle. An empty shortlist offers a clear discovery entry point.

## Independent perspectives

Five additional short original summaries reference the original reviewers of Monkey 47, Roku, Bombay Sapphire and Hendrick's. A Seattle Spirits Society panel provides a separate historical Monkey 47 score explicitly reported on a five-point scale. That page records a tasting date; `published_on` remains null because publication dates were not established. Qualitative summaries do not infer a numeric score or its maximum. Original articles, external member comments, photographs and paper bodies are not copied. Sources and access dates accompany the records; the seed input is `data/navigation/critic-perspectives.json`.

## Administration and extension

Admin → Ingredients filters/edits the navigation group. Existing Recipe ingredients, Sources, History, Place, Bottle assets, Price observations and Critic reviews controls determine the public decision data. No frontend rebuild is needed for normal editorial changes; the worker/import/export pipeline retains the new ingredient field. Old 1.0 documents remain importable with an omitted navigation_group (default unclassified), and the schema generator preserves the additive field's optional status. Consumers should use the updated schema when reading new exports.

A future tasting recommender requires adequate opted-in review data, evaluation and exposure controls; additional price comparisons need comparable dated market observations. Those are not simulated by the documentation tool.
