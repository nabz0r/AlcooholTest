# Current distribution — Volume 04

55 canonical products plus two distinct editions; 804 source records, 125 ingredient/input records, 265 source-linked recipe assertions, 56 critic accounts, 85 licensed local photographs and 51 verified external photo references, nine studies and 613 price observations. All 55 canonical products have source-linked histories, attributed criticism, price evidence and front/rear references. Hosted photos cover 44 fronts and 22 rears; external-only references retain their original hosting. Twenty-nine products have an overall evidence span of at least 20 years, but only five have a single comparable retail series spanning 20 years. The 321 Kakubin monthly survey values are separate. Field presence does not establish a complete proprietary recipe, continuous prices or a measured exposure.

Ingredient technical fields are optional additions to catalogue 1.0: `plant_part`, `sensory_role`, `preparation`, `technical_notes`, nullable `profile_source_id`. The updated strict schema preserves old ingredient rows without these keys. Editorial profiles may explicitly state an unknown species, part, concentration or preparation. They are not clinical monographs. The source overlays live in `data/enrichment/dossiers.json`; reviewed archive price facts live in `data/prices/archive-research.json`. Reproduction uses `scripts/build_seed.py` and `scripts/build_data_exports.py`.

The following contract/history sections are retained for the original schema and prior releases; their old dataset counts are historical, not the current distribution.

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

The distribution contains 57 product records: 55 canonical roots and two Monkey 47 Distiller’s Cut editions grouped under their original. Forty expansion entries establish source-linked identity; many deliberately omit market-specific ABV, volume, ingredient membership and detailed locality pending curation. Do not interpret this as 57 complete formulas or 57 confirmed packaging photographs. Twenty-two curated reference photographs retain per-file licenses. Two dated Luxembourg price observations establish a starting notebook, not a past price trend. Scientific measurements remain zero.

History is original attributed editorial prose, sometimes a limited portfolio description rather than a complete researched biography. Provider discovery is a separate staged corpus. Brand classifications, photos and retailer names must be reconciled to canonical products before publication. See IDENTITY.md, INGESTION.md and SCIENCE.md.


Packaging assets have an explicit front/back/detail view (default front for older 1.0 documents). The 1.0 schema accepts this additive field; old seed documents remain valid. Two Heering files document a historical 70 cl front/rear pair, not two products or an asserted current-market bottling. Member BottlePhoto uploads and detailed reviews are private operational tables, excluded from public interchange; approved photo metadata appears on the product API. Back up their SQL rows and media files together.

Volume 03 adds optional `Ingredient.navigation_group` with a bounded editorial vocabulary (empty is unclassified), persisted/admin-editable and indexed. `data/navigation/ingredient-groups.json` reproduces the initial mapping. This is navigational grouping, not taxonomic classification, a tasting profile or evidence of effects. Existing `family` remains separate. Six attributed critic accounts now exist (five new original summaries plus the earlier Citadelle account), with no invented score for qualitative records. See DECISIONS.md and the source input `data/navigation/critic-perspectives.json`.

## Volume 05 photographic and price provenance

Public export remains schema 1.0 with additive optional fields: `bottle_assets.pair_key`, `bottle_assets.barcode`, `price_observations.basis` and nullable `tax_included`. The optional `external_photo_references` table contains verified click-through references; it contains no third-party image bytes. Older documents without that table remain importable. `archive_capture`, `retail_offer`, `launch_msrp` and `unspecified` price bases are distinct. MSRP is never silently combined with retailer offers. Null taxes remain unknown.

Image licenses are per-file. Open Food Facts-derived photographic metadata retains ODbL/DbCL terms, including the corresponding `bottle_assets` table in public exports; the original-data CC0 dedication does not replace them. See [photography provenance](../data/photography/LICENSE.md) and [data license scope](../data/LICENSE). A barcode/source series pair does not prove the same physical bottle or capture date.

Editable archive targets and launch research plans are operational/editorial configuration rather than public catalogue tables. Export them from **Admin → Products → Photographs & price archives → Download coverage & targets JSON**; private SQL backups also retain them. `sync_research` adds missing shipped records and preserves existing editor values and disabled targets. Photography audit candidates retain checked sources and rejected mismatches for all canonical products.
