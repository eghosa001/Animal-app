# Open-source and low-cost toolkit evaluation
Version 0.1 — 2026-11-05. Evaluate maintenance, security, documentation, license compatibility and integration complexity before adopting any package.

## Candidate public GitHub repositories
| Component | Repository | Planned use | Why |
|---|---|---|---|
| Flutter | https://github.com/flutter/flutter | Android/iOS app | Well-supported cross-platform foundation |
| Riverpod | https://github.com/rrousselGit/riverpod | Flutter state management | Testable predictable state and async dependencies |
| Flutter packages (go_router and others) | https://github.com/flutter/packages | Navigation and ecosystem packages | Well-maintained core routing package collection |
| FVM | https://github.com/leoafarias/fvm | Flutter SDK version pinning | Consistent local/CI builds |
| Django | https://github.com/django/django | Python backend | Security and admin foundations |
| Django REST Framework | https://github.com/encode/django-rest-framework | API | Mature API ecosystem |
| Django Channels | https://github.com/django/channels | WebSockets | Django-compatible real-time plumbing |
| Celery | https://github.com/celery/celery | Background jobs | Reliable task processing with retriable work |
| django-storages | https://github.com/jschneier/django-storages | Object storage integration | Supports S3-compatible object storage patterns |
| Ruff | https://github.com/astral-sh/ruff | Python lint and format | Fast CI gates |
| pytest | https://github.com/pytest-dev/pytest | Backend testing | Mature fixtures and focused tests |
| Playwright | https://github.com/microsoft/playwright | Admin UI tests | Browser automation in CI |
| k6 | https://github.com/grafana/k6 | Load tests | Reproducible performance thresholds |
| Gitleaks | https://github.com/gitleaks/gitleaks | Secret detection | Protect code reviews from leaked credentials |
| Trivy | https://github.com/aquasecurity/trivy | Dependency/container scanning | Simple vulnerability checks |
| Penpot | https://github.com/penpot/penpot | Optional design collaboration | Open-source alternative to hosted design tools |
| Uptime Kuma | https://github.com/louislam/uptime-kuma | Optional uptime checks | Simple self-hosted synthetic monitoring |

Open source does NOT mean free cloud hosting, zero licensing obligations, or that all packages are production ready. Review current versions, licenses, dependency vulnerabilities and project activity before adding them.

## What to avoid early
- Full self-hosted social media clone: hard to secure/maintain and may create inappropriate content assumptions.
- Self-built video transcoding fleet: expensive engineering, encoding and delivery operation.
- Full Kubernetes deployment or premature multi-service split: overhead for small team.
- Heavy recommendation/AI stack before engagement data exists.
- Unlicensed stock media/assets in example social posts.
- Copying Cane Corso proprietary code or database without explicit rights.
- A payment gateway that only supports instant split payouts when the product promises an escrow-style hold.
- Low-maintenance third-party authentication packages with broad privileges; prefer secure, audited framework primitives.

## Build-vs-buy choices
- **Build:** listings/animal schema, seller trust model, contextual offers, unique animal reservation, order state machine, ledger mirror and welfare policy.
- **Integrate:** payments/regulated custody, identity verification, video encoding/delivery, push messaging, analytics, crash monitoring, email delivery.
- **Use Django Admin first:** internal moderation/verification configuration; custom finance dashboards later as workflow needs are validated.
- **Build a simple recommendation rule engine:** no expensive ML serving until measured quality improvement.

## Evaluation checklist for each dependency
1. Last release and open security issues evaluated.
2. Compatible with pinned Python/Django/Flutter version and app-store requirements.
3. License permits intended commercial distribution; any obligations recorded.
4. Supports testing and controlled upgrades; no hidden SaaS lock-in.
5. Documented fallback/exit path and data portability.
6. Dependency scanning and mobile size/performance impact checked.
7. Data residency, NDPA privacy and subprocessors reviewed where hosted.

## Planned coding conventions
Django: service modules for workflows, type hints where feasible, domain validations, atomic transactions, centralized permissions and consistent API errors. Flutter: view/widgets separate from state/controller and API repositories, typed models, accessible UI components, no secret keys, instrumentation and cancellation-aware networking. CI: format/lint/test/security/contract gates. All changes connect to requirement IDs and test evidence.
