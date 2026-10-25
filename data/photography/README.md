# Reviewed bottle photography

This collection distinguishes locally hosted, licensed images from photographs that can only be viewed on their original publisher's site. Every accepted photograph was checked visually for the canonical product and the actual bottle side. Search-result descriptions, image filenames and provider-selected `ingredients` fields were not sufficient evidence.

## Snapshot: 25 October 2026

| Evidence | Coverage |
| --- | ---: |
| Canonical products reviewed | 55 |
| Licensed local image files | 85 |
| Products with a local front image | 44 |
| Products with a local rear image | 22 |
| Products with a reviewed local source pair | 22 |
| Verified external-only source records | 51 |
| Products with an actual front reference, local or external | 55 |
| Products with an actual rear reference, local or external | 55 |

The 51 external records include 11 fronts and 40 rears. Seven of these rear records remain useful alternative market/package references for products that also acquired a licensed local rear image. There are **33 products without a local rear file** and **11 without a local front file**. Source-link coverage is not local image-pair coverage.

Historical labels, contextual photographs, close-ups, importer stickers, visible market differences and known format differences are recorded explicitly. A genuine historical photograph is not evidence that the same artwork is current. Images of cartons are not counted as bottle rears. The downloaded bytes and label artwork have not been reconstructed, generated or repainted.

## Files

| File | Purpose |
| --- | --- |
| [`../assets.json`](../assets.json) | Accepted local image paths, source URLs, author, individual reuse license, edition notes, source pairing, SHA-256 and byte count. |
| [`external-references.json`](external-references.json) | Visually verified source-page links and image URLs where redistribution permission has not been established. No retailer image files are published. |
| [`targets.json`](targets.json) | Reviewed canonical search targets, source pages and barcodes. |
| [`coverage.json`](coverage.json) | Per-product local presence, missing local sides, external references and checked provider requests. `missing_views` concerns local files; `missing_reference_views` concerns combined reference coverage. |
| [`provider-policy.json`](provider-policy.json) | Exact image-host allowlist, size limit, source terms, review requirements and rejected product/side mismatches. |
| [`verification.json`](verification.json) | Pinned-file integrity, decoded image dimensions, source-review counts and tool-check results. |
| [`LICENSE.md`](LICENSE.md) | Original notes, per-image licenses, source-derived metadata terms and pairing limitations. |

`pair_key` associates an actual reviewed barcode record or photographic series. It does not prove that separate contributor uploads depict one physical bottle. Do not assign a pair solely because two sellers use the same canonical product name. Barcodes are source evidence; an erroneous source quantity is not promoted to a verified format.

## Discover, review, then publish

The metadata collector is bounded to the 55 reviewed targets and at most 15 Commons search results per target. It collects leads, not approved assets. Its output always marks candidates `unreviewed` and `needs-editorial-review`, including when a source payload supplies different status fields.

From the repository root:

```sh
python3 scripts/collect_photographs.py \
  --product monkey-47-schwarzwald \
  --output work/photo-discovery/monkey-leads.json

python3 scripts/collect_photographs.py \
  --all \
  --output work/photo-discovery/all-leads.json
```

Cache entries are reusable only when their request URL matches the reviewed target query. Use `--refresh` to fetch a changed query explicitly. `--cache-only` performs no network calls and reports missing cached results as errors. The original research cache is an ignored working artifact; a clean clone must first collect its own responses.

Before accepting an image, inspect the actual pixels, expression, side, visible format and market. Verify the photographer, source page and exact applicable license. Preserve meaningful fine print and orientation. Record historical packaging and partial/contextual framing. A source page that displays a photograph does not by itself grant permission to mirror it.

For a licensed accepted file, add the attribution and rights record to `data/assets.json`, preserve its original bytes or a documented provider thumbnail, and pin its SHA-256 and byte count. The restore tool accepts HTTPS only on the three exact reviewed image hosts and checks redirects before following them. Local paths must remain under `/bottles/`; each file is capped at 8 MiB. A new host requires a separately reviewed policy change.

For an exact product/side image without established reuse rights, add source metadata to `external-references.json` after visual review. Keep `rights_note`, `edition_note`, verification date, review hash and review byte count. The public experience links to the source page; it must not use an external-reference row to imply a licensed local image or a physical source pair.

## Verify or restore accepted files

```sh
# No network: verify every committed file against its pinned manifest.
python3 scripts/fetch_assets.py --verify-only

# Network: restore only already reviewed and pinned image bytes.
python3 scripts/fetch_assets.py

# Security and editorial-boundary checks.
python3 -m unittest discover -s scripts -p 'test_photo_tools.py'
```

A source that changes bytes causes restoration to fail until the changed image is reviewed and its manifest updated. Updating a hash alone is not a substitute for checking the new image. `verification.json` records a point-in-time visual and integrity review; a remote source can subsequently change or disappear.

## Administration

Use the product's photographic records to maintain licensed local assets, source pairs, source barcodes and publication status. Use external photographic references to maintain verified source links, edition notes and rights conditions independently of local assets. The product research view reports local-image gaps and external source evidence separately. Product identity remains canonical across sellers; adding a new photographic source does not create a new product.

Open Food Facts selected-image tags contain occasional wrong-product and wrong-side assignments. Recorded rejected examples include Bombay Original under a Sapphire research lead, Monkey 47 inside a Hendrick's record, SKYY under a Campari barcode and Chivas 18 under a Chivas 12 lead. The acceptance decision belongs to editorial review, not the provider tag or search rank.
