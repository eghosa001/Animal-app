# Environment design, infrastructure, delivery and observability
Version 0.1 — 2026-11-05. No production resources are currently configured by this plan.

## Environments
| Environment | Infrastructure | Data | Payments |
|---|---|---|---|
| Local | Docker Postgres+Redis, Django ASGI/worker, Flutter emulator/device | Fixtures and synthetic animals | Mock provider only |
| CI | Ephemeral Postgres/Redis in isolated runner | Generated test data | Fake/sandbox adapter |
| Staging | Separate hosted API/worker/database, R2 private test bucket, test Stream quota | Fake/sanitized data | Sandbox partner if approved |
| Production | Independently billed managed compute/DB/Redis, backups, object storage/CDN and monitoring | Real protected data | Approved live partner, signed webhooks |

## Starter implementation sequence
1. Create Flutter app and Django project with pinned runtime/tool versions and lockfiles.
2. Configure Docker Compose for local PostgreSQL, Redis and optionally MinIO as an object-store emulator.
3. Implement /health/live, /health/ready and metrics for DB/Redis/worker status. Never expose sensitive status through public debug pages.
4. CI: database migration check, lint, unit tests, contract snapshot, build check, secret and dependency scan.
5. Deploy staging using provider environment variables/secrets, HTTPS, private database networking and least-privilege service identity.
6. Configure domains api.example, admin.example and media endpoints after the brand is approved. Separate callback paths; enforce HSTS and TLS.
7. Create production only after client business ownership, payment/legal gates and verified stage performance.

## Recommended deployment simplification
For the initial live pilot choose a single managed host such as Railway/Render with separate web (ASGI), worker, Redis and PostgreSQL services, **or** a dedicated isolated VPS with containers + managed database and backups. VPS can lower predictable dollars but increases security, patching, recovery and on-call workload. Do not run payment jobs on sleeping free web services or free databases prone to pausing.

## Network and data security
API behind TLS + appropriate WAF, zero direct public Postgres/Redis access, internal service credentials scoped per environment, object buckets private by default, client upload signed URLs, service account least privilege. Delivery proof, ID documents and health records isolated with explicit access.
Protect administrative endpoints with MFA, IP/access policy where feasible, and full audit. Short-lived staging credentials; secrets rotated with documented downtime-free procedure.

## Observability
Emit structured metrics: request count/latency, DB connection pool/exceptions, Redis backlog, background job age, WebSocket connected users, content moderation queue, video error/usage, signed webhook failures, payment reconciliation discrepancies, order transition rejects, payout request states.
Set external uptime checks and mobile crash reports. No chat content, full phone, bank/account IDs or health document contents in logs. Separate analytics and security audit datasets.

## Disaster recovery
Define RPO/RTO with owner. Start with at least daily encrypted backups; stronger frequency for protected financial orders depending on risk. Test restore into isolated environment; verify relational consistency, journal balancing, media access and background job recovery. Store backups in a different failure domain where possible and track expiration/legal hold. Automated backup success is NOT proof of recoverability.

## Release strategy
- Change-scope CI -> staging migration/test -> manual production approval -> deploy immutable image/commit -> smoke -> monitor.
- Use additive schema migrations first, backfill and verify, then remove fields only after old mobile clients are compatible.
- Maintain mobile API backward compatibility because store users update gradually.
- For failed rollout, rollback code and feature flags; do not rollback financial database to stale state casually.
- Maintain changelog, API version deprecations, release provenance and security incident contacts.

## Secrets, service permissions and ownership
All cloud/payment/store projects should be under the client-controlled organization. No long-lived personal Gmail credentials or old Cane Corso service accounts. App installation signing keys must be protected and recoverable. Define who can see production logs, execute database migrations, adjust commission policy or approve refunds and payouts.
