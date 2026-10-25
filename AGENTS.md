# Repository working agreement

Keep public UI, code comments and documentation in English. Preserve canonical product identity: size, market and seller are not automatically new products. Never infer secret formulas, finished-drink exposure, real rear-label artwork or verified purchases.

For every work session:

1. Record the requested scope and pending checks in PLAN.md / PROGRESS.md before substantial changes.
2. Update PROGRESS.md when implementation, verification and publication milestones pass. Distinguish those states; retain material failures and their resolution.
3. Update affected docs alongside code, including data/API changes and operator migrations.
4. Build the frontend and run relevant PostgreSQL integration tests. For visible changes, inspect the actual running UI and save useful real screenshots; update SCREENSHOTS.md and README.
5. Verify the remote main tree after publication. Do not describe an unpushed change or queued CI as published/passing.

Never commit .env, credentials, member data, private SQL backups, local authentication state or screenshots exposing them. Keep licenses/provenance with every asset. Preserve honest limits for artistic 3D/audio, science and SEO. Use Docker for the reproducible stack; do not weaken isolation to make a test pass.
