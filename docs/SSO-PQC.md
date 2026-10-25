# Identity and cryptographic roadmap

## Implemented boundary

Django server-side sessions, CSRF, Argon2 password hashing, least-privilege editorial permissions, loopback binding, private PostgreSQL/Redis networking, rate limits, raster validation, parameterized ORM queries and audited editorial operations are implemented. This is not an independently audited or formally certified system. Local HTTP on loopback is not encrypted transport.

## SSO proposal — not shipped

Prefer an open-source OIDC provider such as Keycloak or authentik. Use authorization code with PKCE, exact redirect allowlists, state/nonce validation and server-held client credentials. Identify accounts by issuer + subject, never auto-link by an unverified email. Map groups to explicit Django permissions, require MFA for editors at the provider, prevent member-driven privilege escalation and retain a local break-glass administrator. Test logout, expired tokens, key rotation, account linking and provider downtime before enabling it. SAML is an optional later adapter, not a requirement for the catalogue.

## Post-quantum readiness — not a 2030 certification

“2030 compliant” is not a defined product standard. NIST FIPS 203/204/205 specify ML-KEM, ML-DSA and SLH-DSA respectively; implementation, protocol support and deployment policy still matter. The app does not implement its own cryptography. Before public hosting, terminate HTTPS at a maintained proxy/runtime that supports an appropriately reviewed hybrid classical/PQ TLS exchange with the chosen browser fleet; verify actual negotiated handshakes. Upgrade TLS libraries, preserve algorithm agility, review long-lived backup encryption and signing, and maintain an inventory of cryptographic dependencies. Do not advertise PQ protection merely because a future TLS option is planned. The present Nginx deployment has no configured TLS/PQ handshake.

Primary references: https://csrc.nist.gov/pubs/fips/203/final , https://csrc.nist.gov/pubs/fips/204/final , https://csrc.nist.gov/pubs/fips/205/final .
