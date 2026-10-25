# Security policy and threat model

## Reporting

Do not publish credentials or a live exploit against a deployed instance in a public issue. For this self-hosted project, report non-sensitive reproduction steps through the repository and use GitHub private vulnerability reporting if enabled. The owner has not published a dedicated security contact or response SLA.

## Implemented controls

- Random per-installation secrets; no default administrator. One-time setup locks the installation row in a transaction. Password validation and Argon2 hashing. Session rotation on sign-in and HttpOnly, SameSite cookies. Sign-out is POST with CSRF protection.
- Same-origin API and Django CSRF middleware on writes, including login. No permissive CORS or browser-stored API tokens. Members cannot invoke operations; staff need the `catalog.add_job` permission in addition to staff status. Superusers have it automatically. SQL backups and imports never have anonymous download URLs.
- Database-backed write/login rate buckets work across API workers. The proxy overwrites X-Real-IP; API is not published on the host. A trusted reverse proxy must be the only way to reach it in production. Admin login additionally needs perimeter rate limiting for a public deployment.
- ORM parameters, typed model validation, strict JSON schema, bounded request/page sizes, allowed job types, UUID filenames and no shell interpolation. Uploads accept JPEG/PNG/WebP only, enforce pixel and byte limits and are re-encoded to JPEG. Imported photo paths and arbitrary executable models are rejected. Source URLs are stored as references; the server never fetches contributor URLs, limiting SSRF exposure.
- User strings are escaped in UI HTML, SVG labels strip markup and 3D labels use canvas text. CSP blocks third-party script and framing; inline styles remain allowed for dynamic layout. Security headers and no external analytics/resources.
- Non-root API/worker/web, read-only root filesystems, dropped Linux capabilities, no Docker socket mounts, private DB network and no published DB/API ports. PostgreSQL data persists separately. Dependencies are locked in requirements.txt/package-lock.json.
- Audit rows for application operations and model admin create/update/delete. Django's own admin log also records editorial actions. Public exports exclude users, collections, submissions and tasting notes. Private SQL backups include all DB records, including password hashes.

## Residual risks and deployment work

This is hardened application code, **not an independently penetration-tested or certified system**. The local Compose default uses HTTP on loopback. Before remote use, terminate TLS at a trusted proxy, set SECURE_COOKIES=1, set exact ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS, redirect HTTP at the edge and rate-limit `/admin/login/`. Do not blindly trust forwarded-proto headers from arbitrary clients. Configure network controls, OS updates, monitoring, offsite encrypted backups and tested recovery. Authentication has no built-in MFA, SSO, email verification or password reset email workflow.

The initial deployment uses the PostgreSQL database owner for migrations and runtime. For public/multi-tenant hosting, use a separate migrator and a restricted runtime DB role. Application audit logs are not tamper-proof against database administrators. DB write rate limiting can itself consume database resources; the proxy provides the first layer. Account registration is open by default for the local community workflow and can be disabled with REGISTRATION_OPEN=0.

Export snapshots currently have no automatic retention or disk quota. Staff can fill disk by repeatedly exporting; prune old files using the documented maintenance procedure and enforce a volume quota in production. Shared UUID IDs do not provide access control. Browser imports are size bounded but not a general untrusted bulk-ingestion sandbox. Operators authorized to import can replace catalogue content intentionally.

User observations can contain personal information. Keep notes focused on tasting, moderate before publication, and establish your own privacy/retention policy before collecting public user accounts. A SQL backup is not anonymized. The CC0 catalogue license does not apply to private user data or third-party photographs.
