# Animal Platform

**Status:** Active development. M0 and selected M1 modules (audited seller review, private media, Flutter animal draft listings, email account recovery and all-device session revocation) have merged with automated tests. No production deployment, payment processor, escrow service, or live cloud infrastructure has been provisioned.

Cross-platform (Android + iOS) animal-only social and marketplace platform with verified seller profiles, animal listings, short video and photo posts, messaging, structured offers, and delivery-aware **partner-managed** protected payments.

> **Payments:** This project must NOT hold customer funds in a developer-controlled bank account or claim escrow protection without written authorization from an appropriate financial provider. All live payment flows remain disabled until compliance and partner approvals.

## Documentation

| Guide | Purpose |
|---|---|
| [Product requirements](docs/01-product-requirements.md) | Personas, user journeys, features, scope and acceptance |
| [Architecture](docs/02-architecture.md) | Modular monolith, mobile, integrations, events, tenancy |
| [Data model](docs/03-data-model.md) | PostgreSQL entities, invariants and indexes |
| [API and realtime](docs/04-api-and-realtime.md) | API routes, WebSockets, versioning, security |
| [Payments and delivery](docs/05-payments-and-delivery.md) | Partner gate, orders, financial integrity, disputes |
| [Social media and moderation](docs/06-social-and-moderation.md) | Video, feed, abuse control, welfare |
| [Security and compliance](docs/07-security-compliance.md) | Threat model, privacy, legal/animal controls |
| [Tooling and setup](docs/08-tooling-setup.md) | Free tools, registration sequence, credentials |
| [Costs and capacity](docs/09-costs-and-capacity.md) | Verified vendor prices, usage models, budgets |
| [Roadmap and delivery](docs/10-roadmap.md) | Implementation phases, milestones, exit gates |
| [Testing and release](docs/11-testing-and-release.md) | Automated QA, CI/CD, Android/iOS distribution |
| [Operations runbook](docs/12-operations.md) | Backup, monitoring, incidents, finance reconciliation |
| [Decisions and risks](docs/13-decisions-and-risks.md) | ADRs, open decisions, risk register |
| [Client setup checklist](docs/14-owner-checklist.md) | Self-service accounts and access delegation |
| [UX and design system](docs/15-ux-and-design-system.md) | Screens, interactions, accessibility and mobile quality |
| [Open-source evaluation](docs/16-open-source-evaluation.md) | Public GitHub libraries, build-vs-buy, licensing |
| [Infrastructure and deployment](docs/17-infrastructure-and-deployment.md) | Environments, release, secrets, recovery |
| [Android CI reliability](docs/19-android-ci-reliability.md) | Pinned Flutter/NDK, retry and failure runbook |
| [Seller review runbook](docs/20-seller-review-runbook.md) | Staff permissions, evidence case IDs, audit and suspension controls |
| [Feature completeness audit](docs/21-feature-completeness-audit.md) | Current implemented vs planned features, P0/P1/P2 gaps, journey acceptance |
| [Animal identity and inventory](docs/22-animal-identity-and-inventory.md) | Individual animals, litters, lots, welfare, health evidence and reservation safety |
| [Definition of done](docs/23-definition-of-done-and-acceptance.md) | Per-task completion, regression testing and launch gates |
| [Private media setup and threat controls](docs/24-media-upload-runbook.md) | Tested backend private photos/evidence API, staff review, local/R2 configuration |
| [Seller listing workflow](docs/25-seller-listing-workflow.md) | Private draft create/edit, photo gallery, eligibility and moderation gates |
| [Account recovery and throttling](docs/26-account-recovery.md) | Single-use recovery codes, JWT revocation, anti-abuse, SMTP/Redis setup and remaining gates |
| [Staff authenticator MFA](docs/27-staff-mfa.md) | OTP-gated Admin, review permissions, private device enrollment and recovery procedures |

## Feature-readiness notice

The platform is **not feature-complete or production-ready**. The [feature completeness audit](docs/21-feature-completeness-audit.md) lists the unbuilt P0 requirements, and the [definition of done](docs/23-definition-of-done-and-acceptance.md) requires evidence before a feature is described as finished. The Django/Flutter code now supports private seller animal-draft creation/editing, image uploads and photo galleries in a development Android build, but no live animal checkout, escrow, social video feed, real Cloudflare R2 integration, or tested iOS release is available. Critical business rules still require client, legal and payment-provider approval.

## Intended repository layout

```text
apps/mobile/          Flutter Android and iOS application
apps/admin/           Operations frontend (later, after workflow validation)
backend/              Django API, Channels, Celery, PostgreSQL models
packages/api_contracts/   OpenAPI specification and generated client
infrastructure/       IaC, Docker, edge/storage, deployment
docs/                 Product, engineering, operations, business documentation
.github/workflows/    Tests, scans, build/release
```

**No direct sharing of the Cane Corso Ancestry production database or secrets.** Approved reuse is limited to generic, licensed code/patterns and a future permissioned integration API.

## Core engineering rules

1. Start with a modular Django monolith and Flutter application; avoid premature microservices.
2. Keep **development/staging/production isolated** with independent credentials and database instances.
3. Store prices in integer minor units, use server-side access control, and maintain a balanced auditable ledger.
4. Keep physical-animal commerce separate from digital-feature purchases and comply with each app store.
5. Restrict commercial listings to permitted species and regions; provide welfare and report/appeal flows.
6. No public secrets, private identity documents, animal health evidence, or financial details in Git.
7. Require documented test evidence for financial, delivery, privacy, and moderation release gates.
8. Recheck provider policies and prices before contracts; planning figures are not vendor quotes.

## Working foundation (M0)

M0 Django and Flutter foundation is merged to main via [PR #2](https://github.com/eghosa001/Animal-app/pull/2). Backend tests, Flutter analysis/widget tests and a debug Android APK build passed on 2026-11-05; see [the successful Actions run](https://github.com/eghosa001/Animal-app/actions/runs/42107300025). The APK artifact is a temporary development build, not a production release. [Implementation status](docs/18-implementation-status.md) distinguishes implemented features from planned modules.

### Local API

```sh
docker compose up -d postgres redis
python -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements-dev.txt
export DJANGO_DEBUG=true
export DJANGO_SECRET_KEY=local-only-test-secret-not-production
export DATABASE_URL=postgresql://anima:dev_only_not_for_production@127.0.0.1:5432/anima_dev
python backend/manage.py migrate
python backend/manage.py seed_catalog
python backend/manage.py runserver
```

Or run the local containerized API with `docker compose --profile app up --build -d` (the `app` profile starts backend plus database/Redis). See `apps/mobile/README.md` for Android/iOS development. API: `/health/live`, `/health/ready`, `/api/v1/auth/`, `/api/v1/catalog/species`, `/api/v1/listings/`.

For local verification emails, check the Django console output; **never use console email in production**. Currency amounts are integer minor units, e.g. NGN 250,000 = `25000000`. New species are **not approved for trade** automatically. Production payments remain disabled.

## Next implementation gate

Account password recovery is now implemented in Django and Flutter (PR #23), including session revocation and verification resend limits. However a real SMTP service and physical Android/iOS testing remain pending, and staff MFA code is added in PR #26; real operator enrollment and staging acceptance are still pending.

The Flutter individual-animal draft creation/editing and photo gallery workflow is now implemented and CI-tested. **Next:** validate real R2 private-bucket staging, evidence retention/deletion, species and welfare policy, health provenance requirements, and physical Android/iOS end-to-end behaviour before considering public release. No live payments are enabled or assumed.
