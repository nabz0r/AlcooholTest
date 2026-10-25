# Contributing

Use English for code, UI, documentation and curated records. Preserve unknowns explicitly. Add a source for every new ingredient assertion, variant specification or scientific finding. A botanical count is not a full formula; a source describing one market does not establish all markets.

For data, propose through the UI or edit the versioned seed with stable UUIDs. Keep independent scientific evidence separate from user tasting notes. Never add unsourced product-effect claims. Link publications rather than copying full text. Photographs need an explicit credit/license and permission; procedural illustrations are the default.

For code: install the locked dependencies, add a migration for model changes, update the public schema when its contract changes, and run the integration tests and frontend build. New imports must preserve transactional rollback, foreign references and access controls. Never fetch arbitrary contributor URLs server-side or execute uploaded models/scripts. Do not commit secrets or private databases/exports.

Open an issue with concrete reproduction steps or a focused PR. Security reporting is described in SECURITY.md. Existing GPL-2.0 licensing remains in effect; new source contributions must be compatible.

## Track every work session

Before changing scope, record the requested outcome and pending work in PLAN.md / PROGRESS.md. Append evidence as milestones pass; distinguish implemented, tested and published states. Update the affected API, data, operations and experience docs with each feature. For a UI change, capture the running result, inspect it and update SCREENSHOTS.md / README where it changes the showcased behavior. Record failed checks and their fixes honestly. Never commit secrets, private SQL backups, real member data or stale screenshots presented as current evidence.
