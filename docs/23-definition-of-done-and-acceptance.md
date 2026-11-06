# High-standard definition of done and release acceptance

**Version:** 0.1 — 2026-11-06. Designed to enforce the user's instruction: finish and verify one task before beginning the next. A repository document, mock screenshot, or CI green icon is never equivalent to real production readiness.

## 1. One-task-at-a-time engineering contract

For every task or pull request, create a bounded scope, name its owner and requirement IDs, and define the expected user-visible outcome before implementation. A task can close only if every applicable item below is complete:

- [ ] Exact requirements and user states understood; unknown legal or vendor conditions represented as explicit blockers.
- [ ] Public APIs, backend services, schema constraints, permissions, and any migrations documented.
- [ ] Mobile or admin interface includes loading, empty, retry, validation, permission denied and offline states wherever relevant.
- [ ] User-input validation happens **server-side**; object authorization prevents ID enumeration.
- [ ] Affected events/actions are audited without leaking secrets, chat contents or private documents.
- [ ] Normal cases, adverse cases and regressions have repeatable automated tests.
- [ ] Database migrations checked and applied against PostgreSQL in CI; compatibility/rollback plan reviewed.
- [ ] Python lint/format/type gates and Dart analyzer/widget/integration tests applicable to affected code pass.
- [ ] If mobile feature changes, test Android and iOS device/platform behaviour, or label the untested platform a blocker.
- [ ] Financial operations, media permission boundaries, animal welfare and moderation receive dedicated negative/security tests.
- [ ] Accessibility, responsiveness and low-bandwidth performance checked where relevant.
- [ ] Error logging and incident/cost metrics prepared for new service dependencies.
- [ ] Secrets handled only via secure environment; no shared production credentials or exposed identity files.
- [ ] Documentation, requirements/status matrix and API examples updated to match actual delivered code.
- [ ] Pull request reviewed, all required CI jobs **green on the actual commit being merged**, and no unresolved critical/high findings.
- [ ] Merge to protected main and verify **post-merge** checks, affected deployment/staging and smoke flow.
- [ ] Any external vendor integration proven in sandbox, and regulatory/business approval recorded before live enablement.
- [ ] If a check is unavailable, mark the task **blocked/partial**, do not call it complete.

A logical subtask may be merged if it independently satisfies its own agreed acceptance criteria; the larger milestone remains open until all required subparts have passed.

## 2. Evidence matrix by business pillar

| Pillar | Must demonstrate | Automated verification | Manual/platform verification |
|---|---|---|---|
| Registration/security | Registration, verify, recover, logout, profile deletion | Expiry, throttles, token reuse, sessions, duplicate email, permission tests | Android/iOS keyboard/error UX, email deliverability |
| Seller verification | Submission, controlled reviewer decision, appeal/suspend, private docs | Role escalation, self-approval, audit, leak, forged docs, suspended listing removal | Real review case in staging, staff usability and privacy access |
| Animal/catalogue | Valid species and jurisdiction-specific data | Default-deny policy, disabled category, stale listing, health tier | Qualified policy review and representative listings |
| Listings/search | Publish/edit/photo/view/search/favourite | Concurrency, private attributes, filtering, image spoofing, pagination | Buyers and sellers complete flows on phones |
| Chat/offers | Authorized, durable, realtime and reconnecting negotiation | Membership, resend, duplicate IDs, block, offer price snapshot | Two phones with unstable network and offline recipient |
| Social | Post/video/feedback/report/playback | Moderation gate, media authorization, bandwidth quota, ban | Android/iOS swipes, poor network, accessibility, real moderation |
| Payments/orders | Exactly one buyer, correct money, clear fees and provider custody | Ledger balance, race, idempotency, webhooks, chargebacks | Approved sandbox + partner/legal signoff |
| Handover/disputes | Lawful transport, animal ID, buyer acceptance or dispute | Wrong animal, failed delivery, payout hold, refund race | Welfare/transport support case simulation |
| Admin/operations | Reviewer boundaries, fraud queues, financial controls | Staff RBAC and audit, no payout overrides | Incident drill, recovery, finance reconciliation |
| Mobile release | Safe native Android and iOS | CI builds, analyzer, tests, secrets and dependency scan | Real-device tests, TestFlight/Play beta/store review |

## 3. Release-blocking requirements

Before *public animal-commerce launch*, all applicable P0 IDs from docs/01 and docs/21 must have:
1. Approved owner and client signoff.
2. An implemented backend and, where relevant, Android+iOS UI.
3. At least one passing positive and one negative/abuse test.
4. A reproducible evidence link (test run, staging demo, report or contract).
5. No production unapproved default enabled.

Never enable commerce if any of these are absent:
- Written financial partner approval of marketplace and actual fund custody/release mechanism.
- Approved animal trading species/jurisdiction; transport and animal welfare policy.
- Verified checkout/refund/reconciliation that does not let staff/sellers bypass controls.
- Customer support, privacy/compliance, dispute and moderation operations.
- Durable staging/production with tested backups and escalation contacts.
- Real Android/iOS device QA and store policy requirements.

## 4. Performance and reliability benchmarks

These are **targets to prove**, not achieved results:
- Backend read API p95 ≤400 ms at a documented, representative load and DB volume; report slow uncached search separately.
- Real-time chat messages normally delivered <1 second when online and stable; no lost messages after offline reconnect.
- Mobile crash-free sessions ≥99.5% in agreed closed beta; critical payment flows crash-free at acceptance.
- No successful duplicate sale or payout across concurrency, retries and out-of-order events.
- No posted unbalanced financial journal, and daily provider reconciliation identifies every mismatch.
- Media loading adapts to data saver, no uncontrolled autoplay/preload cost, video can recover after disconnect.
- Private evidence inaccessible to unauthorized account or via expired/stale URL.
- Recovery point/time objectives and accessible moderation response windows approved and measured.
- Battery/CPU/memory app impact and tap responsiveness measured on real midrange Android and iPhone devices.

Maintain performance budgets for API latency, media watch-minute costs, app bundle size, memory and error rate with owner and test load before declaring pass/fail.

## 5. Definitions of readiness

- **Architecture ready:** Docs/decisions reviewed, contracts and data boundaries agreed.
- **Feature developed:** Code and UI exist; tests may still be pending.
- **Feature verified:** Automated CI, relevant device/staging and security tests pass.
- **Milestone complete:** All mandatory features and negative tests for that milestone are verified.
- **Release candidate:** User journeys tested end-to-end, no unresolved criticals, legal/financial gates approved, support staffed.
- **Production live:** App accessible in approved stores and live production, monitored with actionable alerting and safe rollback.

Do not use the word "finished" when only development or code review is complete.

## 6. Current result at audit date

**Verified code:** Django baseline and restricted seller review; Flutter shell and Android debug CI. **Now partially verified in M1:** private JPEG/PNG animal-photo and seller-evidence uploads with PostgreSQL tests and Android debug build. **Not verified/live:** production R2/real-device image workflow, social video upload/feed, rich listings, messaging, offers, paid checkout, delivery, disputes, full moderation, iOS signing and production services. Version 1 cannot be released under this definition yet.

## 7. Required pre-next-step review

Before beginning the next production feature, the team should confirm the client accepts this P0/P1/P2 scope split; the upcoming secure photo/evidence-upload task has an explicit storage and privacy architecture with test criteria; and domain approvals that cannot yet be obtained are represented as disabled features, not assumed legal permissions.
