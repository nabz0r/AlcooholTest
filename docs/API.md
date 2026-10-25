# HTTP API v1

Same-origin, session-cookie authentication. All JSON writes require a CSRF cookie/header pair. Obtain the cookie by GET `/api/v1/session`; send its value as `X-CSRFToken`. There are no static API keys. Replies are JSON except authenticated downloads and Django admin HTML.

| Method | Path under `/api/v1/` | Access / purpose |
|---|---|---|
| GET | health | Database liveness and app version |
| GET | session | Current user, registration and first-run state; sets CSRF cookie |
| POST | setup | First-run token, username, password; one-time admin creation |
| POST | register | Username/password; optional member registration |
| POST | login | Username/password; rotates authenticated session |
| POST | logout | Clear session |
| GET | stats | Counts and available countries |
| GET | products | Published catalogue, cursor pagination and filters |
| GET | products/{slug} | Product, bottlings, recipes, compounds, measurements, moderated ratings |
| GET | evidence | Up to 100 curated compound/intervention records and associated studies |
| POST | submissions | Member proposal, always pending |
| POST | products/{slug}/reviews | Member rating and tasting note; always pending after update |
| GET | collection | Current member's own collection, up to 500 entries |
| POST | collection | Set state or remove own item |
| GET | operations | Operations-authorized staff: job queue and moderation counts |
| POST | jobs | Operations-authorized staff: generate `json`, `jsonl`, `sql` |
| POST | imports | Operations-authorized staff: validate or queue catalogue JSON |
| GET | jobs/{uuid}/download | Authorized download of a completed job |
| GET | jobs/{uuid}/manifest | SHA-256 manifest of completed output |
| GET | schema | JSON Schema for catalogue interchange |

## Catalogue search

`?q=juniper&country=Germany&disclosure=partial&limit=24&after=<uuid>`

Additional exact filters: `brand=<brand-slug>`, `ingredient=<ingredient-slug>`. `q` is a literal case-insensitive substring across product names, brand names and associated ingredient names, bounded to 120 characters. Limit is 1–60. Reply: `{items: [...], next: <uuid|null>}`. Cursor order is UUID; do not assume alphabetical or creation order. Short search terms and joined OR conditions may not use trigram indexes efficiently.

## Writes

```json
{"slug":"monkey-47-schwarzwald","state":"wishlist"}
```

Collection states: wishlist, owned, tasted, remove. Review body: `{rating: 1..5, text: "..."}`; maximum 2,000 characters.

Proposal body: brand, name, country, market, abv, volume_ml, description, source_url (HTTPS), ingredients (comma-separated). The server does not retrieve the URL. Approved proposals become drafts and require editorial publication.

Job body: `{kind: "json"}`. Reply HTTP 202 with job UUID. Import preview: `{document: <catalogue object>, commit: false}`; inspect counts, then repeat with `commit: true` to queue. Browser JSON imports are limited to 5 MiB, HTTP bodies to 6 MiB. Maximum five queued/running jobs is a best-effort load guard, not a global concurrency guarantee under racing requests.

## Status and limits

400 validation error, 401 sign-in required, 403 CSRF/permissions, 404 not found, 409 setup conflict, 413 oversized request, 429 application rate limit or full queue. Nginx additionally applies 20 API requests/second/IP with a 40-request burst and may reject bursts with 503. Application JSON writes are limited to 100/5 min/IP and authentication writes to 20/5 min/IP. Admin HTML endpoints follow Django's permission model and need edge throttling for remote deployments.

Django's default 404/CSRF error pages may be HTML. Consumers must check HTTP status and content type rather than assume every error is JSON. Data exports are full snapshots; the catalogue API is bounded for interactive use.

## Extended editorial and discovery contract

- `GET /api/v1/products`: canonical root products by default; `editions=all` includes genuine editions. Format/market rows live in each product's `variants`. Cards include edition links, history/source and licensed image provenance.
- `GET /api/v1/products/{slug}`: recipes, compounds/studies, mechanisms, critic summaries, price observations and moderated community notes. Archived merged aliases redirect to their canonical API resource.
- `GET /api/v1/ingredients/{slug}`: plant identity, source-linked compound associations and limits on beverage exposure.
- `GET|POST /api/v1/products/{slug}/observations`: authenticated private observations and empirical transition matrix, with null on unobserved rows. POST takes `from_state`, `to_state`, optional `notes`.
- `POST /api/v1/jobs`: editors with job permission may request `json`, `jsonl`, `sql`, `discover` or `research`. Import jobs are created through validated imports. Downloads and manifests require editorial authorization.
- Admin duplicate preview/confirmation is under `/admin/catalog/product/{uuid}/merge/`; candidates can be resolved to an existing product before acceptance. This is an authenticated HTML workflow, not an unprotected bulk-merge API.

Community ratings accept integers 0 through 5. All write calls retain CSRF/session protection. Public dumps include curated price observations but exclude candidate staging, private states, users, collection and review data.
