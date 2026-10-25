# Real photographs, with their provenance

Every canonical bottle has a visually checked front reference and rear reference. This is access to genuine source images, not a claim that every file can be redistributed from this repository.

The accepted library contains 85 licensed local files: 44 canonical products have a local front, 22 have a local rear, and 22 have reviewed source-record/series pairs. Another 51 external references provide 11 missing fronts and 40 rear references, including alternatives to several now-local rears. The combined coverage is 55/55 fronts and 55/55 rears. Public pages display local licensed files; external buttons open the exact image at its publisher and retain a separate source-page link. They do not silently load third-party images into the page.

A pair means a common reviewed source barcode or photographic series. Upload dates can differ; it does not mean the same physical bottle, market, year or an unchanged formula. Barcodes, visible sizes, historical labels and uncertain details are preserved in captions. The procedural 3D bottle remains an illustration, not a scan of the photographs.

## Maintain from the admin

Open **Products → Photographs & price archives**. Each row links to:

- Front/rear upload forms, preselected to the canonical bottle and view.
- Licensed asset records and editable packaging captions, credit, source, license and integrity hash.
- External photographic references, with separate review state, side, image URL, source page, publisher, rights note and review date.
- The photographic audit candidate containing checked providers and rejected false matches.

Only verified external references and approved community uploads appear publicly. A front packshot, carton or ingredient crop does not count as a rear bottle. Use the public **Packaging reference** control to select a reviewed front/rear pair, then inspect or enlarge the actual image. New uploaded pairs can be assigned a common reviewed pair key in the admin.

## Reproduce and audit

`python3 scripts/fetch_assets.py --verify-only` verifies pinned sizes and SHA-256 values without a network request. The normal command downloads only the fixed Commons/Open Food Facts image hosts, rejects redirects elsewhere, bounds each file and checks the expected hash before replacement. See [photography research](../data/photography/README.md), [all-55 coverage](../data/photography/coverage.json), [external references](../data/photography/external-references.json) and [source-specific terms](../data/photography/LICENSE.md).

Discovery results are candidates, not automatic publication. The research deliberately rejected Bombay Original mislabeled as Sapphire, SKYY assigned to a Campari barcode, another age of Chivas, and a Monkey photograph uploaded to a Hendrick's record. The actual pixels and expression decide the match.
