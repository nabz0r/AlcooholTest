# Operations runbook

## First start

`./scripts/bootstrap.sh` creates random local secrets if `.env` does not exist, builds images, starts PostgreSQL, runs migrations, collects admin static assets and seeds only an empty catalogue. Re-running does not replace secrets or catalogue edits. Retrieve the one-time setup token with `./scripts/setup-token.sh`; create the first administrator in the UI. After setup, the token is unusable. Keep `.env` private and backed up separately.

## Routine UI workflows

- **Catalogue**: search brand, name or botanical; filter origin/disclosure; compare selected bottles.
- **Bottle page**: market editions, recipe provenance, unknown quantities, evidence, 2D/3D, save to collection, tasting note.
- **Suggest a bottle**: authenticated contributor proposal. Accepting creates a draft; publishing is a separate editorial decision.
- **Editorial studio**: CRUD across every catalogue entity. Create sources before asserting ingredients. Open a recipe to edit its ingredient inline table. Products have variant and recipe inline tables. Edit existing rows in place; add recipe versions rather than erasing historical context when appropriate.
- **Photographs**: edit Product; upload JPEG/PNG/WebP under 5 MiB and 16 megapixels, add credit and license/permission. Image bytes are re-encoded to JPEG. Do not upload copyrighted packshots without permission.
- **Operations**: generate JSON/JSONL/SQL; refresh status; download output and SHA-256 manifest. Validate JSON before committing a queued import.
- **User administration**: superuser creates groups and staff accounts using Django Users/Groups. Catalogue editing uses normal model permissions. Operations additionally requires `catalog.add_job`; grant it only to trusted operators because SQL backups contain private records.

## Health and restart

```sh
docker compose ps
curl --fail http://localhost:8088/api/v1/health
docker compose logs --tail=100 api worker
docker compose restart api worker web
```

All persistent data uses named volumes. `docker compose down` stops services without removing volumes. **Do not use `down -v` unless intentionally deleting this instance.** The API is non-root and read-only except named media/export volumes and temporary memory files.

## Job failure

Check Operations status and worker logs. Errors shown to the browser do not expose database credentials. A worker-interrupted running job is marked failed after 15 minutes. JSON/JSONL exports are atomic and can be regenerated. An import transaction rolls back on validation or database failure; there is no partial catalogue update. A job waiting for its input file briefly remains queued. There is no arbitrary code execution, URL scraper or shell-command field in the UI.

## Backups and recovery

SQL backups are PostgreSQL custom format. Generate via Operations, download privately and verify against the SHA-256 manifest. They include users, password hashes, private collections, proposals and sessions. Encrypt offsite copies. Catalogue JSON is **not** a full application backup. Preserve `.env` and separately back up `alcooltest_media`.

Perform recovery on a new empty database/instance, not blindly over a working database. Example operator procedure after choosing a recovery window and taking a safety backup:

```sh
# Replace the example archive path with your verified backup.
# This restores into an empty database created by your operator.
docker compose exec -T db createdb -U alcooltest alcooltest_restore
docker compose exec -T db pg_restore -U alcooltest -d alcooltest_restore --no-owner --no-acl < /secure/path/verified.dump
# Validate counts and application access before changing POSTGRES_DB in .env.
```

The bootstrap Compose DB defaults to `alcooltest`; set `POSTGRES_DB` to the recovered database in `.env` for API/worker and recreate them. The database container initialization value does not rename existing databases. Invalidate sessions after recovery where appropriate. Backups of media should preserve the same relative upload paths. Restore testing is part of the validation record when performed, not assumed from pg_dump exit status.

## Retention

Exports live in a private volume and currently have no automatic expiry. Operators can inspect and remove old completed-job outputs with normal host/container file tooling after confirming retention policy; do not delete active `.tmp` or `.input` files. Delete matching Job rows only through a planned maintenance procedure (the read-only Job admin deliberately prevents accidental deletion). Configure volume quotas and a scheduled retention implementation before a high-volume public deployment.

## Public deployment

The default is loopback HTTP. Choose a domain, install TLS at a trusted edge proxy, redirect HTTP, and set:

```dotenv
ALLOWED_HOSTS=spirits.example.org
CSRF_TRUSTED_ORIGINS=https://spirits.example.org
SECURE_COOKIES=1
REGISTRATION_OPEN=0
```

Adapt the Compose host binding only as part of that reviewed deployment. Forward the original Host header. If enabling Django HTTPS redirect behind a proxy, configure trusted forwarded-proto handling at that boundary rather than accepting arbitrary client headers. Add MFA/SSO at the edge for administrators, login throttling on `/admin/login/`, restricted runtime DB credentials, monitoring and encrypted offsite backups. These are required operational choices, not a claim that the default local configuration is internet-ready.

## Dependency updates

Python application dependencies are exactly pinned in `backend/requirements.txt`; Node has `package-lock.json`. Update deliberately, run tests/build/audits and rebuild containers. Base images are version-tagged rather than digest-pinned, so rebuilds pick up upstream patches and are not byte-identical. CI records an inventory of the Python dependencies and runs npm audit. Do not commit `.env`, `.secrets`, uploads, private exports or session databases.

## Extended UI operations

Use Studio for discovery, research metadata harvest, export/import and job downloads. Use the editorial admin for prices, source attribution, historical text, edition relationships, candidate identity resolution and duplicate preview/confirmation. Duplicates are archived with audit mappings; conflicting rows remain available for manual reconciliation. See IDENTITY.md for exact steps.

Redis can be restarted without losing catalogue or jobs. Worker media access requires the shared media volume (included in compose.yaml). Back up both `media` and `exports` separately from the database; curated frontend photographs can be reproduced from the pinned asset manifest. Redis has no persistence by design. A failed provider/category appears in its dump summary; do not infer complete internet coverage from a successful job status.

To reproduce schema generation locally, use the project's Python environment with `SECRET_KEY` set and `DB_ENGINE=sqlite`, then `python backend/manage.py build_schema`; this only writes the schema. Runtime deployments use PostgreSQL. Rebuild distribution checksums after changing the schema or seed.
