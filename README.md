# Animal Platform

**Status:** Architecture and implementation planning. No production application, payment processor, escrow service, or live infrastructure has been provisioned.

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

## First milestone

Approve product requirements, jurisdiction/species rules, user-flow designs, payment partner requirements, and the client-owned service accounts. Then scaffold the Flutter app, Django backend, Docker Compose, OpenAPI schema, and CI on feature branches.
