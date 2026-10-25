# Validation — 2026-10-25

Executed locally on Apple Silicon macOS with Docker Desktop. This report scopes evidence; it is not a third-party security, accessibility or performance certification.

## Functional evidence

- Docker builds the TypeScript/Vite UI and Python API; PostgreSQL 17, Redis 8, Nginx, API and worker run successfully with only the loopback web port published.
- **55 Django tests passed against PostgreSQL** (Volume 02 run: 6.177 seconds). Coverage includes transactional/idempotent seed imports, strict schema/cross-references, exported data privacy, drafts, cursor search, sessions/CSRF, editorial authorization, rate limiting, moderated ratings, zero monkeys, proposal drafting, raster validation, worker exports, canonical edition grouping, market variants, private transition matrices, candidate linking, audited non-destructive duplicate merging and price observations. New cases cover server-rendered canonical pages, draft privacy/sitemap, noindex, detailed review validation/averages, real curated front/back views, and moderated photo rights/raster handling. Duplicate-merge coverage now verifies member photo preservation and the HTML canonical redirect.
- Migration drift check reports no changes; Django system check reports no issues. Frontend TypeScript/build succeeds. Production npm audit and pip-audit of all 19 pinned Python dependencies report zero known vulnerabilities at the time checked (Pillow was upgraded to 13.0.0 after the initial scan); this does not cover every operating-system dependency or constitute a complete security audit.
- Generated real JSON, JSONL and PostgreSQL custom SQL backups. Restored the newest SQL backup into an isolated temporary PostgreSQL database, verified **56 product rows**, and removed that temporary database. A separate media restore was not performed.
- Reconciled the original development seed's superseded Almond assertion into the source-specific Bitter almond assertion, retaining its prior row in an audit entry. Public runtime now contains 69 ingredients and the Bombay named set contains 10 entries.

## Browser evidence

Verified the editorial arrival and craft tabs, separate catalogue, clean URLs, product chapters, source/price display, fullscreen 3D zoom/reset and botanical paging, abstract neuro sculpture, detailed review controls, rights-aware photo contribution, genuine rear-label inspection, comparison, research and editorial operations in the in-app browser. The mixer showed Playing and nonzero audio-output meter values; speaker-test and WAV-export controls were exercised. Speaker acoustics and the exported file bytes were not independently measured. The admin duplicate resolution page renders and enforces a concrete preview/confirmation workflow. Screenshots are in `docs/screenshots`. No browser error logs were observed during the tested studio interactions. Eighteen actual screenshots and their integrity manifest are indexed in docs/SCREENSHOTS.md. This is not an acoustic quality or loudness certification.

The UI includes responsive layouts, reduced-motion handling, keyboard controls, visible focus and HTML alternatives. Physical-phone testing and an independent screen-reader/WCAG audit were not performed. There is no claim of flawless behavior on every browser/GPU. WebGL gracefully falls back to the photograph/recipe when unavailable.

## Executed data acquisition

- Wikidata run 1: **105 candidates**, no curated publication and zero successfully stored discovery images due to an initial worker media-mount error.
- Wikidata run 2 after correcting the shared media mount: **27 candidates and 4 downloaded licensed images**. Their individual attribution and modification records are committed with the image files.
- PubMed run: **100 bibliographic records** across five documented queries. No copied paper bodies or automatic clinical conclusions.
- Curated catalogue: **55 canonical products + 2 editions**, 48 brands, 14 detailed places, 69 ingredients, 93 source-linked ingredient assertions, 22 licensed packaging references, 9 curated studies, 4 selected mechanisms, 1 curated critic summary, 2 first dated price observations and **zero finished-product compound measurements**. Forty expansion entries and the new historical Heering identity remain intentionally incomplete in bottling/recipe details. Historical text varies in depth and is source-attributed.

Raw dumps, final run summaries and image attribution are under `data/discovery`. Public provider counts do not mean every record is a bottle; a queue is not a verified inventory. Commons throttled some optional photo searches; missing images remain explicit illustrations rather than invented photographs.

## Measured reads — retained Volume 01 baseline

20 live HTTP requests, concurrency 2, Nginx/Redis/API/PostgreSQL, on 54 canonical products: **20 successes, 0 errors**, median **3.07 ms**, p95 **48.02 ms**. Mixed catalogue and ingredient-search reads; small local sample, no internet/TLS claim. Cache misses affect the distribution.

Rollback-only synthetic benchmark with **10,000 additional products** (10,056 total), one variant and one ingredient per synthetic product, 30 requests/path, concurrency 1, in-process Django client and PostgreSQL, cache bypassed:

| Path | Median | p95 |
|---|---:|---:|
| Catalogue | 11.54 ms | 12.95 ms |
| Ingredient search | 47.10 ms | 51.59 ms |

Synthetic rows were rolled back and never published. This is not evidence for a million-row catalogue, arbitrary complex recipes, concurrent writes or production internet throughput. An earlier aggressive Nginx burst triggered its configured rate limiter; that result was not reported as successful throughput.

## Explicit delivery limits

The studio is procedural art, not a scanned bottle collection. Neural positions and pulses are abstract. Sound is original generative interpretation. Prices begin with two dated observations; no invented past trend is provided. SSO and hybrid post-quantum TLS are documented plans; no public TLS/PQ transport is configured. The entire internet, all secret recipes, all bottle histories and a security/compliance certification are not delivered or claimed.

## Remote CI and publication — Volume 01 baseline

Published implementation commit `06971f7ea423794efa02fb64d47839a8be284717` to main through the authenticated GitHub connection. All uploaded Git blobs and the complete tree matched the local Git object hashes. [GitHub Actions run 40214087165](https://github.com/nabz0r/AlcooholTest/actions/runs/40214087165) completed successfully: Docker/PostgreSQL integration, frontend build/audit and Python dependency audit. This additionally validates the workflow on its Ubuntu GitHub runner; local visual/WebGL testing remains the macOS in-app browser evidence above. The subsequent documentation-only delivery commit does not change tested application code.


## Volume 02 publication state

Local code/build/migration checks and the 55-test PostgreSQL suite pass. Actual browser QA identified and resolved an aggregate alias collision, an incorrect test route, a same-page popstate reset and review-field layout issues. The price anchor was verified at the viewport while the selected Botanical explosion canvas remained mounted. Final browser console inspection returned no error entries. Screenshot capture and the repository tracking agreement are complete. Remote publication/CI results are recorded after the main update in PROGRESS.md.
