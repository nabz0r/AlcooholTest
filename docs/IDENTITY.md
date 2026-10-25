# Product identity and duplicate resolution

A **brand** is a house or label. A **product** is a named liquid with its own identity. A **variant** records bottling market, size, ABV and barcode. A **recipe version** records a source-dated disclosure. A **distinct edition** may have its own product record and `edition_of` relationship to the original product, for example Monkey 47 Distiller’s Cut 2024 and 2025. A new seller, URL, photo, language or pack size is not sufficient evidence for a new product.

The public catalogue defaults to root products. A family page links its editions; `GET /api/v1/products?editions=all` explicitly lists them. Roku's two market bottlings share one product. Canonical slugs are stable; keep raw provider IDs and provenance rather than treating listing counts as a product count.

## Review an imported occurrence

Studio → Review discovered candidates → open a candidate → set **Resolved product** using the autocomplete → save → run Accept. The occurrence is linked to the existing product and audited without creating another product. If no identity is resolved, acceptance creates an unverified draft; publication always requires editorial verification. Wikidata can describe a brand, category or distillery rather than a specific bottle. Never publish a discovery queue wholesale.

## Merge an existing duplicate

1. Admin → Products → open the record that is the duplicate.
2. Choose **Resolve duplicate** in the object tools.
3. Select the published canonical product of the same brand and click Preview.
4. Review affected record counts, then confirm the concrete merge.

The source product is archived, never cascade-deleted. Non-conflicting bottlings, recipe versions, image references, reviews and shelf records move. Conflicting records remain attached to the archived source for manual reconciliation; no review or recipe is silently overwritten. Observations, critic records, candidate references and child editions are reattached. Uploaded photo and historical text on the archived source are preserved there. Variant-linked price observations follow their variant when it moves. An audit entry records canonical UUID and moved/retained row IDs. Restore a backup or use the audit mapping for a carefully reviewed reversal; there is no one-click undo.

Only editors with product change permission can access the merge tool. Cross-brand merges, self-merges, already merged targets and accidental merging of a declared edition are rejected. Detach an edition only after checking the underlying identity. Take an SQL and media backup before a large reconciliation.
