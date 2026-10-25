# Data contract and evidence policy

## Files

- `data/catalog/seed.json`: full curated starter dataset, schema version 1.0.
- `data/catalog/schema.json`: strict Draft 2020-12 JSON Schema, generated from model fields.
- `data/catalog/catalog.jsonl`: one manifest line, then one `{table, record}` envelope per line.
- `data/catalog/manifest.json`: dataset counts and SHA-256 file checksums.

A JSON document has `schema_version`, `generated_at` and `tables`. Tables are sources, brands, ingredients, compounds, ingredient_compounds, products, variants, recipes, recipe_ingredients, studies and measurements. Every row uses UUID identity. Foreign keys use `<field>_id`. Decimal values are strings on export to avoid float precision loss. Null amount is unknown. A zero is a measured or explicitly stated zero and must not stand for missing data.

Validation rejects unexpected fields, missing tables, duplicate IDs, missing foreign references, invalid choices, invalid model fields and out-of-range values. Database uniqueness is also enforced transactionally during import; a conflict rolls back the entire import. Importing a full snapshot is an upsert, not replacement/deletion. Photo paths and private user data are not part of the public contract.

## Source assertions

Manufacturer confirmation establishes a disclosed ingredient, not an independent chemical measurement. “Complete” means the named ingredient set is disclosed, not that proportions or chemistry are known. Counts can refer to local botanicals, a base distillate or additional infusions; record context in recipe notes. A product can have an empty ingredient inventory without asserting an empty recipe.

Do not silently inherit ingredients between annual editions or markets. Add a new recipe version with a source when the recipe is known to change. `RecipeIngredient.certainty` is confirmed, reported or hypothesis. Keep hypotheses visible and never promote them by inference alone. A submitted source URL is initially secondary/unverified until an editor checks it.

## Evidence boundaries

Plant identity → constituent presence → distillation transfer → measured beverage concentration → absorbed dose → human outcome are different questions. Link them only with appropriate evidence. Animal or cell studies stay labeled. Oral extract results cannot be copied into distilled-drink effects. The starter dataset contains no finished-product measurements and no proof of a product-specific intoxication effect.

The five compound/intervention entries include one explicitly labeled whole-plant intervention (lemon balm extract). Its type is described in notes; a future schema version should split interventions into a separate table if the research catalogue grows beyond its current scope. The thujone and beta-caryophyllene studies are searchable in the evidence library, but are not automatically attached to unmeasured bottles through unsourced ingredient links.

## Reproduction

```sh
python3 scripts/build_seed.py
# Requires installed backend dependencies and development environment variables:
python backend/manage.py build_schema
python3 scripts/build_data_exports.py
```

`build_data_exports.py` validates shape and foreign references, then writes JSONL and checksums. It does not scrape external websites. The checked-in data contains original factual summaries, bibliographic metadata and links rather than copied source publications. All seed references were reviewed during initial research; accessed_on identifies that review date, not a promise the remote page never changes.

## Current collection and identity

The distribution contains 56 product records: 54 canonical roots and two Monkey 47 Distiller’s Cut editions grouped under their original. Forty expansion entries establish source-linked identity; many deliberately omit market-specific ABV, volume, ingredient membership and detailed locality pending curation. Do not interpret this as 56 complete formulas or 56 confirmed packaging photographs. Twenty curated reference photographs retain per-file licenses. Two dated Luxembourg price observations establish a starting notebook, not a past price trend. Scientific measurements remain zero.

History is original attributed editorial prose, sometimes a limited portfolio description rather than a complete researched biography. Provider discovery is a separate staged corpus. Brand classifications, photos and retailer names must be reconciled to canonical products before publication. See IDENTITY.md, INGESTION.md and SCIENCE.md.
