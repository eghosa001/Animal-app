# Anima implementation status
Updated 2026-11-06. Distinguishes working development code from unbuilt production capabilities. Full release gates: [definition of done](23-definition-of-done-and-acceptance.md).

## Verified and merged source

### M0 foundation — PR #2
- Django 5.2 API, PostgreSQL-first local services, Redis, versioned routes and health checks.
- Email-first account, JWT sessions, email verification, seller applications; manual staff seller-review controls added in PR #9.
- Species catalogue with commercial trading disabled by default; individual-animal records, listing drafts, pending and active moderation states.
- Flutter Android/iOS source, five-tab navigation, sign-in and account flows. Native platform runners are generated in CI; production app identities/signing not finalized.

### M1 audited seller and private media — PRs #9, #14 and #15
- Audited staff seller approval/rejection/suspension/reopening, explicit reviewer permission and anti-self-review.
- Private JPEG/PNG uploads with server re-encoding, metadata stripping, opaque storage keys, distinct R2 adapter buckets for evidence versus animal photos, read access audits, photo moderator decisions and seller suspension hiding public media.
- Flutter gallery picker, private evidence consent, review statuses and approved public photo thumbnails.
- **Cloud R2 is not configured**, and evidence upload is not independent identity/KYC verification.

### M1 individual animal listings — PRs #17, #18 and #19
- [PR #17](https://github.com/eghosa001/Animal-app/pull/17): create/edit draft APIs, per-object permission and state enforcement, atomic updates, cannot edit after submission; require uploaded photo to submit and staff-approved photo to publish.
- [PR #18](https://github.com/eghosa001/Animal-app/pull/18): auditable *soft removal* of draft photos, revoked reads and reusable draft gallery slots. Physical storage deletion is a future regulated retention/erasure process.
- [PR #19](https://github.com/eghosa001/Animal-app/pull/19): Flutter Create tab and Profile seller workspace, individual-animal create/edit with species-category guidance, price parsing using integer kobo, draft list, photo gallery previews/removal and submission confirmation, owner session and offline/error states.
- [PR #21](https://github.com/eghosa001/Animal-app/pull/21): changing an animal's identifying fields on a draft invalidates prior approved photos and creates an audit event; fresh photo review is required before public listing approval. [Backend CI](https://github.com/eghosa001/Animal-app/actions/runs/42213077913) passed **48 tests + 4 subtests**.
- Trading is still default-denied. A seller may prepare a private draft for a disabled category but cannot submit it.
- [Workflow and acceptance guide](25-seller-listing-workflow.md) describes the exact current scope and supported attributes.

## Automated verification

- [Backend PR CI](https://github.com/eghosa001/Animal-app/actions/runs/42211500550): lint, Django system check, migration consistency, PostgreSQL tests — **46 passed and 4 subtests passed**.
- [Flutter PR CI](https://github.com/eghosa001/Animal-app/actions/runs/42211500615): Flutter analyzer and widget tests, Android debug APK build and uploaded artifact — passed. The artifact is a **development** build requiring reachable API; it is not Play Store-ready.
- Post-merge `main` checks must also be inspected. Code CI does not prove live Cloudflare, physical device upload, iOS build, or client/legal acceptance.
- Earlier milestones: PR #8 fixed flaky Android NDK setup; PR #14 [backend verified](https://github.com/eghosa001/Animal-app/actions/runs/42204310107), PR #15 [Android verified](https://github.com/eghosa001/Animal-app/actions/runs/42205721985).

### M1 account recovery and verification controls — PR #23 (pending CI acceptance)

- Password-reset requests return generic responses and issue single-use, hash-stored emailed codes with expiry and repeat-request cooldown.
- Successful password recovery revokes all prior access/refresh JWT sessions; verification resend and auth endpoints are per-IP throttled.
- Flutter has a password recovery form and verification resend actions.
- [Operational and security controls](26-account-recovery.md) identify required SMTP/Redis setup and uncompleted physical-device verification; do not mark PR #23 as merged until CI/merge are confirmed.

## M1 remains open — critical blockers

1. Cloudflare R2 real-account, private-bucket staging integration and authorized staff access audit on live infrastructure.
2. Private evidence legal basis, retention/deletion, malware scanning/PDF support and identity verification policies/provider choice.
3. Species-specific health, welfare, age, region and trading restrictions approved by responsible professionals, with verifiable records and source provenance.
4. Real-device Android and iOS end-to-end tests with production-like HTTPS backend and actual customer flows.
5. Password recovery code/Flutter workflow needs PR #23 verification and live SMTP/device checks; staff MFA, complete session/device management, marketplace search, listing lifecycle and customer support remain outstanding.

**Not yet implemented:** social videos/feed, contextual chat, structured negotiation, order/ledger/regulated protected payments, animal delivery, refunds/disputes, production moderation/support dashboard, push notifications, production hosting, native iOS release and app store publication.

**Financial controls:** No live payment, escrow, payout, or animal delivery has been activated. No paid production infrastructure has been provisioned. M1 individual-animal draft editing is verified at code/CI level only; **the full platform is not release-ready**.
