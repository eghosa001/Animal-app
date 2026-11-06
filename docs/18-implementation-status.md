# M0 implementation status
Updated 2026-11-05. Tracks actual implemented code, not aspirations.

## Implemented on main (merged via PR #2)
- Django app project and versioned /api/v1 routing.
- PostgreSQL-first runtime with local SQLite fallback only when DEBUG; Docker Compose Postgres/Redis.
- Custom email-first account model, password validators, JWT access/rotating refresh tokens, refresh-token logout.
- Verification code sent via Django mail backend (local console in debug); hashed token stored, 24-hour expiration.
- Seller application creates PENDING; audited staff seller-review screen requires dedicated permission, reason, case reference and evidence-review confirmation. Invalid/self reviews blocked; no KYC integrations yet.
- Species catalog model and safe seed command; trading OFF by default for every species.
- Animal + Listing models; seller drafts, seller-only listing view, guarded submission, staff-only publication, public active listing API. Seller suspension removes active listings with audit and public queries dynamically exclude unapproved/inactive sellers and restricted species.
- Readiness/liveness checks, backend API tests and GitHub Actions.
- Flutter mobile source with navigation and API-connected basic marketplace/account flows, explicit adult seller attestation, email verification for signed-in users; native Android/iOS runner templates generated via flutter create bootstrap, not committed platform runners.
- CI compiles a debug Android APK and offers a 7-day workflow artifact for device smoke testing.
- Payment flag disabled unconditionally. No live cards, fund custody, payout or buyer protection yet.

## NOT implemented / not live
- Media uploading, video feeds and transcoding.
- Realtime chat/WebSockets, offers and push notifications.
- Orders, payment partner adapter, settlement, ledger, delivery, refund/disputes.
- External KYC, species law verification, legal documents, production moderation queues.
- Cloud hosting, DNS, monitoring accounts, store registration, native release signing.

## Verification evidence
- Backend CI passed against PostgreSQL with lint, migration check, migration run and API tests on 2026-11-05.
- Flutter CI generated Android/iOS runner scaffolds and passed analysis/widget tests. Android debug APK build passed and uploaded a seven-day workflow artifact on 2026-11-05; see https://github.com/eghosa001/Animal-app/actions/runs/42107300025. An actual iOS archive still requires macOS/Xcode and credentials.
- Financial go-live requires written partner/legal signoff and a separately implemented audit-tested commerce module.
- Documentation is planning source of truth; feature status is this file and GitHub PR/CI results.

## Verified incremental M1 progress (2026-11-06)
- [PR #8](https://github.com/eghosa001/Animal-app/pull/8): pinned Flutter/NDK and robust NDK-install retry. Android debug build and uploaded APK verified on [CI run](https://github.com/eghosa001/Animal-app/actions/runs/42163692011).
- [PR #9](https://github.com/eghosa001/Animal-app/pull/9): manual audited seller approval, explicit permission, locked transitions, suspended-listing removal and staff UI. Backend PostgreSQL CI passed **19 tests + 4 subtests**, Django migration checks, and lint on [CI run](https://github.com/eghosa001/Animal-app/actions/runs/42164908370).
- Manual evidence review requires secure **external** case reference, not raw ID documents. This is NOT third-party automated KYC or completed M1.
- Seller media uploads, identity-evidence storage, detailed verification requirements, listing editing UI and Android/iOS real-device end-to-end checks remain pending.

## Requirements coverage audit (2026-11-06)

The [completeness audit](21-feature-completeness-audit.md) distinguishes planned P0/P1/P2 features from implementation, adds missing account-recovery, health/animal provenance, multi-animal inventory, buyer trust and operational acceptance requirements. No additional user-facing product functionality is implied by this documentation audit. [Definition of done](23-definition-of-done-and-acceptance.md) must be met for each separately verified task. Secure seller evidence uploads and animal listing media remain next on the implementation path.

## M1 backend photo/evidence implementation (2026-11-06)

- [PR #14](https://github.com/eghosa001/Animal-app/pull/14): private image upload/preview backend for draft animal listings and seller evidence, safe JPEG/PNG re-encoding, server-side permission checks, owner audit and moderator review. Separate private R2 bucket adapter and debug-local storage are coded; no real Cloudflare credentials connected.
- Backend API and PostgreSQL tests cover sensitive evidence isolation, MIME/content spoofing, size/quantity limits, listing state changes, approved photo publication and unauthorized staff/buyer access.
- [Media setup guide](24-media-upload-runbook.md) distinguishes verified local/CI work from staging integration, consent/legal, file cleanup and Flutter upload UI still outstanding. **Does not mean M1 or KYC is complete.**

## Next milestone M1
Complete secure email delivery service, KYC workflow and staff evidence storage, animal health/photo uploads, seller listing management UI, species approval signoff and real-device end-to-end testing. Do not represent the app as launch-ready.
