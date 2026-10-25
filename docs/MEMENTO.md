# Source Memento

The Memento is the atlas's portable source notebook. It captures **public catalogue facts and their provenance** in immutable JSON capsules. It preserves the difference between facts, project editorial summaries, source references, source-content hashes and licensed image bytes. It does not promise that every original web page has been copied.

## What the user can keep

The public `/memento/` page searches by source title, publisher and URL. Its bottle filter follows the actual public record relationships: recipes, ingredients, linked compounds and studies, origin, critics, prices, survey series and photographs. A capsule opens on demand and can be downloaded as JSON. The original source remains one click away. Dates that were not recorded remain unknown.

Each capsule includes:

- The reference URL, publisher, source kind and recorded access date, where known.
- Public extracted records, their table/record identifiers, bottle context and interpretation limits.
- Recorded source hashes with their actual scope. A fact-extract hash is never presented as the hash of an unavailable original page.
- A separate `snapshot_sha256` for the capsule itself.
- `original_content_status: not_copied` and an explicit copy status such as `fact_extract_only`, `external_link_only` or `licensed_local_asset`.

The user sees a compact source card first. The full facts and limitations sit behind an explicit open action. This is a provenance tool, not another wall of text in the bottle dossier.

## Coverage and privacy boundaries

Only source-registry entries referenced by eligible public records and the fixed public-record allowlist are captured. Brands and places must be reachable from a published product. This covers sources attached to history, places, bottlings, recipes, ingredient profiles, ingredient/compound links, studies, mechanisms, measurements, critic summaries, individual price observations and reviewed monthly survey indexes. Website and other public reference URLs create reference capsules when no Source record already represents that URL. Licensed local bottle assets and verified external photographic references have their own capsules. Approved public photograph metadata may be included; its account identifier is omitted.

Only published products, verified photographic references and verified survey indexes are eligible. An explicit field allowlist excludes unknown fields even if an input dump contains them. Accounts, password hashes, email addresses, private collections, member observations, moderation queues, discovery payloads, pending photographs, jobs and audit events are not public Memento data. `ProductResearch` contributes its sourced expression launch year, earliest-possible year, source URL and editorial research limits for published products. These notes belong to the public research record; confidential operational material must stay outside it. Explicit public chronology/identity reports also contribute their scoped facts and additional source references for published canonical bottles, including a distinction between brand bounds, expression launches, renames and unaccepted price leads. Draft-only and orphan sources, brands and places are excluded. Source metadata is public only when referenced by eligible public facts; do not store credentials there.

Project histories and critic/study summaries are original editorial records, **not original article copies or verified quotations**. Source access dates come from recorded metadata. The snapshot capture timestamp describes the local capture, not a newly verified visit to every external page.

## Rights and locally hosted media

Publicly visible does not mean licensed for republication. The Memento never downloads Source URLs or external reference images. It does not redistribute full copyrighted articles, retailer pages, subscription content or private research HTML/PDF caches. An original-content hash may identify such a privately retained research capture without including its bytes.

An optional ZIP includes the already hosted bottle images whose reviewed metadata establishes CC BY, CC BY-SA, CC0 or a documented Commons public-domain reference. Credit, license URL, source URL, modification/edition notes, local-byte SHA-256 and byte count accompany every included file. The image's local SHA identifies that hosted derivative, not an unavailable full-resolution original or its source page. Existing attribution and share-alike duties continue to apply. The ZIP's `licenses/media-manifest.json` states exactly what media was included. External photograph references remain links and report zero copied image files.

## Immutable artifacts and verification

Runtime artifacts live under `EXPORT_ROOT/memento` unless `MEMENTO_ROOT` is configured. This is a private artifact directory, not a directory exposed by the web server. Capsules use `capsules/<snapshot_sha256>.json`; version manifests use `snapshots/<snapshot_sha256>.json`. `index.json` points to the latest snapshot. Existing content-addressed files are never overwritten. A changed source or fact creates a new capsule hash. Old artifacts remain available to the operator's backup policy. The public capsule endpoint only serves hashes in the latest public manifest. Public reads compare a fingerprint of current product publication and image/index approval states, rebuilding metadata on a withdrawal so stale capsules cannot bypass current publication settings.

To verify a capsule, remove `snapshot_sha256`, serialize the remaining JSON as UTF-8 with sorted keys, no ASCII escaping and compact comma/colon separators, then compute SHA-256. Compare it with the removed value. This verifies the saved capsule, not the truth of its underlying source. `source_proofs` keeps the separately scoped research evidence. For archived retailer HTML, the recorded original hash covers the decoded, decompressed bounded capture bytes. The original HTML is not included. Current browser-view prices, launch recommendations and the Kakubin chart use fact-extract hashes where stated.

The immutable manifest has the same canonical-hash convention. Repeated captures can reuse unchanged capsule files while creating a newly dated manifest. A returned capsule has an ETag equal to its capsule digest. Normal database edits do not rewrite old snapshots: regenerate from the editorial studio to update the current Memento.

## Admin and Docker operation

The Source Memento view requires an active staff account with `catalog.view_source`. Its regeneration POST additionally requires `catalog.add_job` and valid CSRF protection. It queues a durable `memento` job. The existing worker builds a fresh public snapshot and a ZIP; job checksums and downloads use the existing operations system. An already queued or running bundle is reused. An integrity failure fails the job rather than publishing an apparently complete partial ZIP.

The worker obtains licensed image bytes only from **fixed** `http://web:8080/bottles/<reviewed-filename>` paths. The path must match `/bottles/[-a-z0-9]+.(jpg|png|webp)`, the expected SHA must be valid, and each file is limited to 8 MiB. Redirects are rejected. No destination hostname, source URL, query string or request header is accepted from a user. Total media is bounded to 256 MiB. The standalone CLI uses a fixed local asset root and rejects traversal and escaping symlinks instead of using the network.

Metadata-only public reads make no outgoing network requests. A first read can build a metadata snapshot if none exists. Subsequent reads use the latest artifact after checking current publication/approval membership. The source list is bounded to at most 60 entries per page; search input is limited to 120 characters.

## Offline build

From the repository root:

```sh
python3 scripts/build_memento.py
python3 scripts/build_memento.py --zip work/memento-public.zip
python3 scripts/build_memento.py --out work/memento-metadata --zip work/memento-metadata.zip --metadata-only
```

The default input is `data/catalog/seed.json`, public research reports are read from fixed paths below `data/`, and licensed local image bytes come from `frontend/public/`. `--out` chooses the capsule artifact directory. `--zip` is optional. The CLI does not fetch websites. It reads no account files and uses no credentials. Runtime job exports use current public database records instead of the seed.

Additional launch research, Appleton predecessor identity sources, and the bounded remaining-gap report (including the complete Citadelle May 2003 wholesale PDF hash) can create their own source capsules even before they have Source foreign keys. Their exact claims, uncertainty and separately scoped retrieval hashes are retained; no raw response is copied. Draft, merged and noncanonical product mappings do not publish research capsules.

The fixed research report list is intentional: arbitrary files, private caches, account state and unknown nested dump fields are not swept into a public bundle. If a new public provider is introduced, add a reviewed report path and document its hash scope before claiming its original content has been preserved.

## Integration hooks

- Public GET `api/v1/memento` → `catalog.memento.memento_index`.
- Public GET `api/v1/memento/capsules/<digest>` → `catalog.memento.memento_capsule`.
- Source admin views → `catalog.memento.staff_memento`, wrapped in `admin_site.admin_view`; optional `source_id` limits the displayed source.
- Worker `memento` job → `catalog.memento.memento_to_file(temp_path)`; final artifact extension is `.zip`.
- Frontend page → `renderMemento(main, {api, esc})` from `frontend/src/memento.ts`.
- Bottle section → `mementoSectionHTML(slug, esc)`, then `bindProductMemento(container, slug, {api, esc})` after insertion.

The context `api` function uses paths relative to `/api/v1/`. No remote source content is executed inside the atlas; fact text is escaped before display.
