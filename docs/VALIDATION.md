# Validation — 2026-10-25

Executed locally on Apple Silicon macOS with Docker Desktop. This report scopes evidence; it is not a third-party security, accessibility or performance certification.

## Functional evidence

- Docker builds the TypeScript/Vite UI and Python API; PostgreSQL 17, Redis 8, Nginx, API and worker run successfully with only the loopback web port published.
- **47 Django tests passed against PostgreSQL** (latest full run approximately 6.2 seconds). Coverage includes transactional/idempotent seed imports, strict schema/cross-references, exported data privacy, drafts, cursor search, sessions/CSRF, editorial authorization, rate limiting, moderated ratings, zero monkeys, proposal drafting, raster validation, worker exports, canonical edition grouping, market variants, private transition matrices, candidate linking, audited non-destructive duplicate merging and price observations.
- Migration drift check reports no changes; Django system check reports no issues. Frontend TypeScript/build succeeds. Production npm audit and pip-audit of all 19 pinned Python dependencies report zero known vulnerabilities at the time checked (Pillow was upgraded to 13.0.0 after the initial scan); this does not cover every operating-system dependency or constitute a complete security audit.
- Generated real JSON, JSONL and PostgreSQL custom SQL backups. Restored the newest SQL backup into an isolated temporary PostgreSQL database, verified **56 product rows**, and removed that temporary database. A separate media restore was not performed.
- Reconciled the original development seed's superseded Almond assertion into the source-specific Bitter almond assertion, retaining its prior row in an audit entry. Public runtime now contains 69 ingredients and the Bombay named set contains 10 entries.

## Browser evidence

Verified the black photographic arrival, catalogue navigation, product page, source/price display, 3D studio, botanical group controls, neuro sculpture, audio toggle and editorial operations in the in-app browser. The admin duplicate resolution page renders and enforces a concrete preview/confirmation workflow. Screenshots are in `docs/screenshots`. No browser error logs were observed during the tested studio interactions. Audio toggle state and absence of runtime errors were checked; this is not an acoustic quality or loudness certification.

The UI includes responsive layouts, reduced-motion handling, keyboard controls, visible focus and HTML alternatives. Physical-phone testing and an independent screen-reader/WCAG audit were not performed. There is no claim of flawless behavior on every browser/GPU. WebGL gracefully falls back to the photograph/recipe when unavailable.

## Executed data acquisition

- Wikidata run 1: **105 candidates**, no curated publication and zero successfully stored discovery images due to an initial worker media-mount error.
- Wikidata run 2 after correcting the shared media mount: **27 candidates and 4 downloaded licensed images**. Their individual attribution and modification records are committed with the image files.
- PubMed run: **100 bibliographic records** across five documented queries. No copied paper bodies or automatic clinical conclusions.
- Curated catalogue: **54 canonical products + 2 editions**, 47 brands, 14 detailed places, 69 ingredients, 93 source-linked ingredient assertions, 20 licensed packaging references, 9 curated studies, 4 selected mechanisms, 1 curated critic summary, 2 first dated price observations and **zero finished-product compound measurements**. Forty expansion entries remain intentionally incomplete in bottling/recipe details. Historical text varies in depth and is source-attributed.

Raw dumps, final run summaries and image attribution are under `data/discovery`. Public provider counts do not mean every record is a bottle; a queue is not a verified inventory. Commons throttled some optional photo searches; missing images remain explicit illustrations rather than invented photographs.

## Measured reads

20 live HTTP requests, concurrency 2, Nginx/Redis/API/PostgreSQL, on 54 canonical products: **20 successes, 0 errors**, median **3.07 ms**, p95 **48.02 ms**. Mixed catalogue and ingredient-search reads; small local sample, no internet/TLS claim. Cache misses affect the distribution.

Rollback-only synthetic benchmark with **10,000 additional products** (10,056 total), one variant and one ingredient per synthetic product, 30 requests/path, concurrency 1, in-process Django client and PostgreSQL, cache bypassed:

| Path | Median | p95 |
|---|---:|---:|
| Catalogue | 11.54 ms | 12.95 ms |
| Ingredient search | 47.10 ms | 51.59 ms |

Synthetic rows were rolled back and never published. This is not evidence for a million-row catalogue, arbitrary complex recipes, concurrent writes or production internet throughput. An earlier aggressive Nginx burst triggered its configured rate limiter; that result was not reported as successful throughput.

## Explicit delivery limits

The studio is procedural art, not a scanned bottle collection. Neural positions and pulses are abstract. Sound is original generative interpretation. Prices begin with two dated observations; no invented past trend is provided. SSO and hybrid post-quantum TLS are documented plans; no public TLS/PQ transport is configured. The entire internet, all secret recipes, all bottle histories and a security/compliance certification are not delivered or claimed.
