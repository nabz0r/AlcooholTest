# Alcooltest — implementation analysis

Date: 2026-10-25. Target: an English, self-hosted, open-source spirits knowledge catalogue.

## Product boundaries

A brand contains products; products have market/volume/strength editions; recipes are versioned per product and carry ingredient-level sources. A disclosed botanical count is not a fully disclosed formula. Ingredients and compounds are separate entities. A compound studied in an animal or concentrated extract is not proof of exposure, intoxication, or therapeutic activity in a drink. Unknown concentrations remain null. Community tasting notes and ratings are moderated observations, never scientific evidence.

## Decisions before implementation

- Django 5.2 LTS for transactions, migrations, CSRF/session authentication, Argon2 password hashing, permissions and a complete editorial admin. PostgreSQL 17 is the production store. Vite/TypeScript and Three.js deliver a small static application, served behind an unprivileged Nginx reverse proxy.
- PostgreSQL holds normalized relational entities, evidence and queue state. JSON is the portable interchange, not the primary database. Unique constraints, relationship indexes and trigram GIN indexes support bounded catalogue searches. Cursor pagination prevents unbounded result retrieval. No additional search cluster or cache until measured workloads justify it.
- Background export/import jobs use PostgreSQL row locks with SKIP LOCKED; jobs persist across API restarts. JSON/JSONL exports stream and publish atomically with SHA-256 manifests. SQL backups use pg_dump; restore is a documented operator recovery procedure rather than a destructive browser button.
- Same-origin cookies, CSRF, role checks and server-side validation. No remote URL fetching by the server. Upload only raster images, re-encode them, reject oversized/decompression-bomb images. No external executable models, HTML, SVG or scraping code from contributors.
- A procedural SVG and a real interactive WebGL model exist for each product. These are explicitly illustrative models, not manufacturer photographs or dimensionally accurate scans. Editors may add licensed photographs through the admin.
- Public account creation is configurable. Members propose additions and write tasting notes; staff review before publication. Staff operate all entities through Django admin and jobs through the application. First installation uses a one-time setup token supplied by an ignored local environment file; no default account/password.
- All application source, documentation and UI in English. Existing GPL-2.0 license preserved. Original data compilation CC0; source documents and trademarks retain their owners' rights.

## Initial acceptance scope

1. Browse/search/filter and compare products, view ingredient provenance, recipe versions, market variants, scientific evidence and disclosure limits.
2. View every seeded bottle in 2D and rotatable/zoomable 3D, with fallback when WebGL is unavailable.
3. Register/sign in, maintain a collection and submit products/notes; staff approve or reject from UI.
4. Admin CRUD for brands, products, editions, recipes, ingredients, compounds, sources, links, studies and measurements; audited edits.
5. UI-triggered versioned JSON, JSONL and SQL exports, downloadable manifests; validate/preview/import the published JSON interchange via queued jobs.
6. One-command Docker bootstrap; persist data; database and application not exposed separately. CI covers integration, security, import rollback, export round-trip and frontend build.

## Known limits to report honestly

A curated starter catalogue is not exhaustive coverage of all alcohol brands. Proprietary recipe proportions cannot be reconstructed from marketing. Illustrative bottle geometry is not an authentic scan. Security hardening is not a penetration-test certification. Scale targets require reproducible measurements: publish dataset size, concurrency and timings; do not claim million-item validation from a small seed.

## References consulted

- https://github.com/nabz0r/zamzam-water — source-linked measurements, exports and explicit dataset inventories; no code copied.
- https://www.postgresql.org/docs/current/pgtrgm.html — indexed text search.
- https://docs.djangoproject.com/en/5.2/topics/security/ — same-origin sessions, CSRF and deployment controls.
- https://monkey47.com/blog/water and /blog/the-botanicals-part-iv-spicy — partial botanical disclosures.
- https://us.hendricksgin.com/hendricks-original/ — botanical and infusion distinction.
- https://www.suntory.co.jp/wnb/rokugin/lineup.html — market-specific strengths.

## Threat model

Assets: credentials, contributor records, editorial integrity, backups. Threats: privilege escalation, CSRF, injection, forged evidence, unbounded import/upload, SSRF, stored XSS, export path traversal and job duplication. Controls and residual risks are detailed in SECURITY.md. TLS, host patching, backup encryption and perimeter protection remain deployment responsibilities.
