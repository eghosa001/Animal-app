# M0 implementation status
Updated 2026-11-05. Tracks actual implemented code, not aspirations.

## Implemented on main (merged via PR #2)
- Django app project and versioned /api/v1 routing.
- PostgreSQL-first runtime with local SQLite fallback only when DEBUG; Docker Compose Postgres/Redis.
- Custom email-first account model, password validators, JWT access/rotating refresh tokens, refresh-token logout.
- Verification code sent via Django mail backend (local console in debug); hashed token stored, 24-hour expiration.
- Seller application creates PENDING; staff checks and approves manually in admin. No KYC integrations yet.
- Species catalog model and safe seed command; trading OFF by default for every species.
- Animal + Listing models; seller drafts, seller-only listing view, guarded submission, staff-only publication, public active listing API.
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

## Next milestone M1
Complete secure email delivery service, KYC workflow and staff evidence storage, animal health/photo uploads, seller listing management UI, species approval signoff and real-device end-to-end testing. Do not represent the app as launch-ready.
