# Anima implementation status
Updated 2026-11-10 for video-first development PR #29; previous baseline 2026-11-06. Distinguishes working development code from unbuilt production capabilities. Full release gates: [definition of done](23-definition-of-done-and-acceptance.md).

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

### M1 recovery and authentication protection — PR #23

- [PR #23](https://github.com/eghosa001/Animal-app/pull/23) **merged**: one-time 20-minute email recovery codes, hashed database storage, account/IP throttles, non-enumerating responses, password-validation rules, verification resend controls and audit events without secrets.
- After successful reset, all previous access and refresh tokens are rejected, and outstanding refresh tokens are blacklisted. At the time of PR #23, staff MFA and all-device logout were not implemented. They have since been added by PRs #25 and #26; device-specific controls remain outstanding.
- Flutter has a Forgot password? journey with code/new-password validation and verification resend action.
- [Backend CI](https://github.com/eghosa001/Animal-app/actions/runs/42276351500): Django checks/migrations, **57 tests + 4 subtests** passed. [Flutter & Android CI](https://github.com/eghosa001/Animal-app/actions/runs/42276351577): Flutter analysis, **11 widget tests**, Android debug APK compiled and uploaded.
- [Account recovery operations guide](26-account-recovery.md) documents Redis/SMTP prerequisites. Real outbound SMTP, user-device testing and iOS Xcode validation remain unverified.

### M1 session revocation — PR #25, merged and CI-tested

- Password-confirmed `/api/v1/auth/logout-all` endpoint and Flutter profile action provide immediate all-device JWT invalidation and audit, plus refresh-token ownership checks for ordinary logout.
- Existing password remains unchanged for the user; its stored salted hash is rotated, so previously issued JWT password-revocation claims no longer match.
- [PR #25](https://github.com/eghosa001/Animal-app/pull/25) merged. [Backend CI](https://github.com/eghosa001/Animal-app/actions/runs/42596845818): **63 tests and 4 subtests**, no migration drift; [Flutter CI](https://github.com/eghosa001/Animal-app/actions/runs/42596845794): **15 widget tests**, analyzer and Android APK successful. See [account-security runbook](26-account-recovery.md).
- Device-by-device inventory/selective revocation remains unimplemented. Staff MFA code is merged under PR #26, but real administrator enrollment and cross-device acceptance still require configuration and testing.

### Staff MFA enforcement — PR #26 (CI-verified; staging acceptance pending)

- Django Admin requires an OTP-verified session; seller, listing and media reviewer actions are permissioned behind this check.
- Staff consumer JWT issuance, refresh and acceptance are blocked, including older bearer tokens. Private evidence requires staff OTP or object ownership.
- First-device TOTP enrollment is a private interactive server command; see [staff MFA runbook](27-staff-mfa.md).
- [PR #26](https://github.com/eghosa001/Animal-app/pull/26) **merged**. [Combined-branch CI](https://github.com/eghosa001/Animal-app/actions/runs/42598245974) and [post-merge main CI](https://github.com/eghosa001/Animal-app/actions/runs/42598475720) each passed Django system/migration checks, **74 tests + 4 subtests** on PostgreSQL.
- Real operator enrollment, time-drift testing, account recovery drill and production monitoring remain outstanding.

### Video-first Home — PR #29 merged; CI verified, device acceptance pending

The owner confirmed a TikTok-style **video-first entry point** for the entire animal platform. [PR #29](https://github.com/eghosa001/Animal-app/pull/29) **merged** a vertical HLS player in place of the text-first Flutter Home, a read-only paginated moderated video endpoint and safe eligible-animal links. [Backend CI](https://github.com/eghosa001/Animal-app/actions/runs/42887364050) passed **78 tests plus 4 subtests**; [Flutter CI and Android debug APK](https://github.com/eghosa001/Animal-app/actions/runs/42887363955) passed analysis, **19 tests** and debug APK compilation. No actual Stream upload, live video ingestion, real-device playback or iOS verification is delivered; do not describe any of those as available. Full [decision and remaining gates](28-video-first-product-decision.md). This does **not** close M3.

### Private creator uploads — video posting slice under CI review

PR #31 **merged** the default-off Stream private direct upload ticket and signed processing webhook, with [backend CI](https://github.com/eghosa001/Animal-app/actions/runs/42889742919) passing **88 tests + 4 subtests**. The subsequent Flutter creator UI and read-only private status endpoints are in a separate review branch; do not treat them as deployed until tests and merge complete. No upload/publish service is live; no staff video publication moderation, takedown controls, payout integration or actual video in Home has been verified. See [provider setup](29-private-video-upload-runbook.md) and [creator UX](30-creator-video-ux.md).

## M1 remains open — critical blockers

1. Cloudflare R2 real-account, private-bucket staging integration and authorized staff access audit on live infrastructure.
2. Private evidence legal basis, retention/deletion, malware scanning/PDF support and identity verification policies/provider choice.
3. Species-specific health, welfare, age, region and trading restrictions approved by responsible professionals, with verifiable records and source provenance.
4. Real-device Android and iOS end-to-end tests with production-like HTTPS backend and actual customer flows.
5. Account recovery is now implemented and CI-tested; production transactional SMTP, staff MFA operator enrollment, selective device/session management, live device tests, marketplace search, listing lifecycle and customer support remain outstanding.

**Not yet implemented:** social videos/feed, contextual chat, structured negotiation, order/ledger/regulated protected payments, animal delivery, refunds/disputes, production moderation/support dashboard, push notifications, production hosting, native iOS release and app store publication.

**Financial controls:** No live payment, escrow, payout, or animal delivery has been activated. No paid production infrastructure has been provisioned. M1 individual-animal draft editing is verified at code/CI level only; **the full platform is not release-ready**.
