# Testing, QA, performance and app-store release
Version 0.1 — 2026-11-05.

## Enforced acceptance criteria (2026-11-06)

All feature implementation must satisfy the [definition of done](23-definition-of-done-and-acceptance.md). The [coverage audit](21-feature-completeness-audit.md) lists additional P0 requirements not previously tracked explicitly, while the [inventory specification](22-animal-identity-and-inventory.md) provides concurrency, welfare, media privacy and health provenance failure tests. An approved Android debug CI build alone does not prove an iOS release or full end-to-end commerce.

## Testing pyramid
- Pure unit: money allocation/rounding, permissions, species policy, order transitions, feed ranking.
- Database/integration: Django ORM, row locks, uniqueness, migrations, transaction journals, idempotent outbox.
- API contract: OpenAPI snapshot, schemas, auth scopes, rate limits, paginated responses, errors.
- WebSocket: reconnect, missed messages, duplicate client IDs, blocked users, offline delivery.
- Mobile: Flutter unit/widget/integration, navigation, keyboard, file picker, video reuse, accessibility.
- Browser admin: Playwright on staff operations.
- Provider sandbox: webhook signature/replay, checkout failure, release denial, refund, settlement, chargeback.
- Security: OWASP ASVS/MASVS checklist, dependency and secret scan, authorization IDOR and broken-role tests.
- Operational: backups, isolated restores, payment reconciliation, queues and retries, latency/load.

## Mandatory high-risk cases
A. Two buyers race to purchase same animal -> one winning reservation.
B. 20 duplicate payment webhooks -> single journal and no double credit.
C. Fraudulent unsigned “paid” callback -> rejected.
D. Out-of-order payout/refund webhook -> no impossible transition.
E. Buyer reports disputed welfare incident -> payout held and reviewer alerted.
F. Seller edits listing after offer accepted -> no change to order price.
G. Forbidden species or region -> selling blocked in API and admin.
H. Stolen chat/media link -> object-level authorization enforced.
I. Repeated upload under fake mime -> rejected before publication.
J. Moderator mistaken removal -> appeal restores content with audit, no leak.
K. New database migration with old app version -> compatible deployment or explicit blocking plan.
L. Backup restore against isolated environment -> valid restored data and bounded RPO/RTO.

## Performance targets to test, not assert
- Backend p95 simple read under 400 ms at an agreed concurrent load/realistic DB size.
- Chat latency <1 s in stable connectivity, graceful fallback after disconnect.
- Video smooth at reasonable midrange Android, playback not blocking navigation.
- Crash-free sessions >=99.5% during pilot; no unresolved P0 crash.
- No unbalanced posted ledger journals and no duplicate successful payouts.
- Feed avoids wasteful video preloading/billed delivery.
Benchmark with simulated low-end network and representative phones, not emulator only.

## CI on each PR
1. Ruff/format/type validation + Django system checks.
2. Django pytest and migration consistency + security lint.
3. flutter analyze, flutter test and formatting.
4. Generated API client and contract diff checks.
5. Static secret/dependency audit.
6. Integration smoke in ephemeral Postgres/Redis on changed module paths.
For releases: full integration, mobile device tests, security, finance and load staging runs. Use selective CI paths to avoid expensive irrelevant builds.

## Android release
- Create client-owned Google Play Console (one-time $25 current fee).
- Prepare package id, keystore and Play App Signing process, privacy policy URL, data safety form, content rating, screenshots, store description, contact/support, account deletion website.
- Build signed .aab under release process, upload internal track first.
- For **new personal developer accounts created after Nov 13 2023**, Google currently requires at least **12 testers opted into closed testing continuously for 14 days** before applying for production access. See https://support.google.com/googleplay/android-developer/answer/14151465 ; exact rules may change.
- Apply for production access, staged rollout, crash/ANR monitoring, emergency rollback plan.

## iOS release
- Client-owned Apple Developer Program membership ($99/year current).
- Mac/Xcode or hosted macOS runner, App Store Connect record, signing certificates/profiles managed securely, bundle ID, push certificate/config, privacy manifest/disclosures and privacy policy.
- Archive using Xcode/Flutter on macOS; TestFlight internal/external testers; App Review demo credentials and notes for marketplace/physical animals, seller verification and moderation.
- Store review might request proof of legal commerce or welfare. Monitor crash logs and stage deployment.

## Store billing distinction
Physical animal sales: appropriate external payment provider (and legal eligibility) per Apple physical-goods exception. Digital post boosts or app subscriptions must be separately evaluated for required app-store billing. Do not enable digital purchase monetization until reviewed.
Apple guideline: https://developer.apple.com/app-store/review/guidelines/

## Go/no-go signoff
Product owner + technical lead + finance/legal + trust/safety jointly sign:
- P0 acceptance criteria demonstrated;
- payment partner and legal approval documented;
- unauthorized payment/payout pathways impossible;
- backup/restore exercised;
- content safety moderators staffed and trained;
- critical/high issues triaged and zero unresolved criticals;
- budget/monitoring alerts configured;
- clear rollback and incident contacts;
- accessible support and store disclosures;
- final real-device smoke and crash monitoring live.
