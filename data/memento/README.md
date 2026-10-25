# Source Memento

This distribution preserves **1,160 public fact capsules**, their provenance and independently scoped hashes. Open [`snapshot.zip`](snapshot.zip) for the capsule JSON files and bundle manifest, or browse [`index.json`](index.json). The public `/memento/` page and each bottle’s Memento tab provide search and readable detail; `/admin/catalog/source/memento/` regenerates a licensed-media ZIP from the current published catalogue.

The committed snapshot contains facts and licensed-image metadata. Its image bytes already live in `frontend/public/bottles/`; the admin bundle includes those verified files. Complete copyrighted articles/PDFs and external photo files are not mirrored. Source document hashes do not imply those original bytes are inside this archive.

Reproduce: `python scripts/build_memento.py --out work/memento --zip data/memento/snapshot.zip --metadata-only`, then copy `work/memento/index.json` here. See [the complete contract](../../docs/MEMENTO.md). The generated source-date and integrity manifest identifies the capture; a capsule fingerprint verifies the stored extract, not source truth.
