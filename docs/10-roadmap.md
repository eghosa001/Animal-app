# Implementation roadmap and execution backlog
Version 0.1 — 2026-11-05. Estimates are planning ranges for a small experienced team; solo implementation may take longer.

## Added dependency and completion gates (2026-11-06)

This roadmap must be read alongside the [feature coverage audit](21-feature-completeness-audit.md) and the [definition of done](23-definition-of-done-and-acceptance.md). All tasks are closed **one verified scope at a time**, with reviewed PR, PostgreSQL migration/negative tests, Android/iOS checks where applicable and post-merge evidence. The entire M1 milestone remains open despite the audited seller-review subtask having been merged.

Requirements newly made explicit:
- **M1 before messaging:** complete private seller evidence/media and verification, species/region approval, individual animal identity and provenance, complete listing author/edit/search/photo UX. Litter/lot inventory is disabled unless a separately tested conditional P0 scope is approved.
- **M2 before checkout:** object-authorized chat, attachments, blocking/reporting, reconnect, structured offers and immutable agreed price.
- **M3 before scaling media:** upload quotas, rights, safety review, accessible adaptive playback, creator moderation, billable minutes alerts.
- **M4 before live commerce:** lawful custody partner contract, fee and refunds policy, inventory reservations, traceable handover, disputes, ledger balance and daily reconciliation.
- **M5 before public stores:** account recovery/deletion, audit roles and staff MFA, customer support, disaster recovery rehearsal, independent Android/iOS device testing, in-app abuse controls.
- **M6 final release:** client/legal/financial signoff and measured quality gates; no blocked P0 feature silently turned on.

Projected dates remain illustrative and require rescoping after client confirms animal categories and the payment partner.

## Guiding schedule
Target approximately 18–26 weeks for a high-quality first release if payment underwriting, legal review, test devices, and product decisions are not blocked. Develop incremental, testable vertical slices. Payment/legal and account setup run in parallel, but production commerce has a hard launch gate.

## Milestone M0 (weeks 1–3): foundation and discovery
Deliverables: signed scope; legal regions/species allowlist draft; service account owners; client terms for protected checkout; architecture decision records; private repository permissions; product design map and test acceptance standards; local containers; Django/Flutter project scaffolds; GitHub Actions lint/tests; baseline API docs.
Exit: Flutter emulator and physical Android open a shell app; backend /health authenticated/test routes work; stage pipeline, no real credentials in git.

## M1 (weeks 4–8): identity and marketplace vertical slice
Epics:
- AUTH: signup/login/verify/recovery/permissions, session security, deletion entry.
- SELLER: application and staff verification workflow, risk status.
- CATALOG: species taxonomy and legal gates.
- LISTING: create/edit/draft/review/publish, images, filters/search/sold.
- ADMIN: moderate sellers/listings.
Exit: buyer finds a verified seller listing and seller manages inventory; forbidden species cannot sell; no checkout on unverified seller.

## M2 (weeks 7–11): conversation and negotiation
Epics: persistent WebSocket chat; notifications; read receipts/offline replay; listing-linked inquiries; offers/counteroffers/accept; blocking; spam controls; test failure/reconnect.
Exit: two actual devices exchange messages and negotiate with correct authorization.

## M3 (weeks 9–15): social content
Epics: direct upload, video processing, thumbnails, animal-topic moderation, posts, follows, comments, basic interests and ranked feeds, feed telemetry and cache.
Exit: safe animal content uploads and plays smoothly under pilot network; report/removal works and media limits are enforced.

## M4 (weeks 11–19): commerce and delivery
Epics: immutable order snapshots; double-sale protection; mock approved-payment adapter; ledger; signed webhook handling; finance admin; fulfillment/pickup; dispute and refund state machines; price/fee disclosure; partner sandbox integration after written approval.
Exit: 100% financial integrity test matrix and signed partner go-live approval. If unavailable, do not launch monetary checkout.

## M5 (weeks 17–23): trust, reliability and polish
Epics: advanced staff queues; monitoring; backups/restores; security scan; accessibility; low-bandwidth tests; legal/help pages; privacy and deletion; store listing assets; pilot reports; performance/load test; incident exercises.
Exit: release checklist in docs/11 passes, zero unresolved critical security or money defects.

## M6 (weeks 23–26): pilots and distribution
Controlled beta with verified sellers and a diverse tester cohort. Gather crash/support/moderation and transaction insights. Google Play closed test and application for production access if personal-account criteria apply; TestFlight and App Store review; staged production rollout and rollback plan.
Exit: owner signs launch approval including payment, welfare, support and cost budgets.

## Suggested PR groups (merge small reviews, not huge code dumps)
1. chore/repo-bootstrap; 2. feat/auth-and-permissions; 3. feat/seller-verification; 4. feat/catalog-and-listings; 5. feat/search-and-storefronts; 6. feat/chat-and-offers; 7. feat/media-upload; 8. feat/social-feed; 9. feat/orders; 10. feat/finance-adapter-and-ledger; 11. feat/fulfillment-and-disputes; 12. feat/moderation-and-admin; 13. chore/security-and-observability; 14. release/android-ios-beta. Split by vertical slices with tests and migrations, never force fixed PR count.

## GitHub Project columns
Backlog -> Spec ready -> Design ready -> In progress -> Code review -> QA/staging -> Approved -> Released; a separate Blocked state with reason/owner/deadline. Issue template: story, rationale, requirements IDs, UX, API/data changes, failure cases, security/privacy impact, tests, rollout/rollback, acceptance evidence.

## Required business decisions
Name, logo and brand; legal operator; Nigeria-only or other jurisdiction; categories of permitted animals; sellers' verification standard; minimum/maximum listing price; commission; who pays fees/delivery; buyer protection/inspection rules; age and adoption; risk and dispute staff; privacy retention; budget; store accounts. Record owner and decision date in docs/13.

## Gate: do not confuse prototype and production
Prototype may run free-tier backend, mocked payment and hand-entered data. Production requires approved financial partner, robust uptime, durable backups, moderated content, usable support, owner-controlled credentials, store policies and real-device QA.
