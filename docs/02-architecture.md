# System architecture and repository boundaries
Version 0.1 — 2026-11-05.

## Architecture decision
**New independent monorepo; modular Django monolith** for the transactionally coupled business domain; Flutter for Android and iOS; lean server-rendered Django Admin initially, custom operations UI only for demanding flows. Do not put this inside Cane Corso Ancestry or use its Oracle production database. Do not introduce Kubernetes, Kafka, or microservices at MVP.

## Proposed tree
- apps/mobile/: Flutter app; feature folders auth, feed, market, seller, chat, orders, profile, settings.
- apps/admin/: optional TypeScript operations frontend when Django Admin becomes inadequate.
- backend/config/: settings, routing, ASGI and WSGI, background worker config.
- backend/modules/: accounts, verification, animal_catalog, listings, social, media, messaging, offers, orders, finance, fulfillment, disputes, safety, notifications, analytics.
- backend/tests/: cross-module integration and financial concurrency cases.
- packages/api_contracts/: generated OpenAPI schema and Flutter client artifacts.
- infrastructure/: Docker Compose local dev, Terraform or provider deployment definitions, Cloudflare config, monitoring.
- docs/: contracts, decisions, runbooks and costs.
- .github/workflows/: path-scoped lint, static checks, tests, deploy.

## Component pathways
1. Flutter HTTPS -> edge TLS/WAF -> Django REST API -> PostgreSQL.
2. Flutter wss:// -> ASGI/Django Channels -> Redis channel layer -> PostgreSQL messages.
3. Client requests short-lived direct-upload ticket -> media provider -> provider event webhook -> backend processing/moderation -> published post.
4. Checkout -> internal immutable order -> partner checkout session -> signed partner webhook -> payment ledger/reconciliation -> fulfillment -> authorized partner release/payout.
5. Celery + Redis for retriable notifications, media event ingestion, searches/recommendation recompute, reconciliations and timeout evaluation.
6. Admin API/backoffice reads bounded, audited operational data; never calls payment API straight from browser.

## Backend boundaries
- Accounts owns identities and permissions; Verification owns KYB/KYC outcomes and verified credential references.
- Catalog owns species/breed and legal-trade configuration; Listings owns publication and inventory.
- Social owns posts, comments, reactions, follows; Media owns assets, uploads, transcode state and access.
- Messaging owns conversations and messages; Offers owns negotiations; Orders owns order snapshots and state.
- Finance owns provider adapters, payment attempts, internal ledgers and payout authority; cannot be modified by moderation UI.
- Fulfillment owns transport/handover; Disputes owns evidence and cases; Safety owns reporting, blocking and moderation decisions.
- Modules communicate through explicit service methods and **transactional outbox events**; direct cross-app model use only with documented contract.

## Reliability choices
- Postgres is system of record. Redis is ephemeral/cache/channel broker, never canonical transaction state.
- Atomic write + outbox event for cross-module side effects. Consumers are idempotent, retries bounded with dead-letter handling.
- Durable order states; database row locks and uniqueness constraints to prevent double sales.
- Do not store media blobs in Postgres. Use private buckets and short-lived signed object access, with sensitive evidence segregated.
- Separate DB credentials, storage buckets, app signing keys, and service accounts for dev/stage/prod.
- Webhooks must verify signatures, event IDs, timestamps/replay policy and provider origin where supported.
- Store currency as ISO currency code and integer minor units; no floats in finance.
- Standardized error envelope, correlation IDs and structured logs, excluding PII/secrets/payment credentials.
- Feature flags gate payment/checkout, species rollout, beta users, and risky functionality.

## Mobile standards
Flutter stable SDK pinned via FVM or CI version and lockfile; clean feature-folder structure, typed API, Riverpod or equivalent single state-management choice, go_router for navigation, secure token storage, image caching, adaptive media player, localization-ready formats, accessibility and offline states.
Do not create business-critical rules only in Dart. Server is authoritative.

## Deployment topology, pilot
Production: one durable application service for Django ASGI, one Celery worker, PostgreSQL with backups, Redis, object storage, hosted video delivery, edge firewall, monitoring. Do not host public business payments on a free sleeping service or a database that automatically pauses. Managed services are preferred where operations budget allows.
Staging: separate lower-cost stack with synthetic test data and payment sandbox. Local: Docker Compose Postgres/Redis, Django, Flutter emulator/device.

## Evolution gates
- Add a search engine only when indexed PostgreSQL queries miss measured latency/feature targets.
- Separate recommendation service only with sufficient training signals and measurable gain.
- Separate chat infrastructure only after WebSocket concurrency and cost evidence.
- Add replicas, worker partitioning, read replicas, or queues when proven by load/observability.
- No direct integration into the existing Cane Corso service unless explicit owner permission, API versioning and scope-approved data mapping.

## Architecture decisions
ADR-001: Dedicated monorepo.
ADR-002: Modular Django monolith rather than microservices.
ADR-003: Flutter mobile.
ADR-004: PostgreSQL canonical state; Redis noncanonical.
ADR-005: No self-operated escrow without regulatory approval.
ADR-006: Hosted video provider vs own FFmpeg transcoding at MVP.
Track design changes in docs/13-decisions-and-risks.md.
