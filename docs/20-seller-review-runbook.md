# Seller review and suspension runbook (M1 subtask)
Updated 2026-11-06. Built for manual staff review; **not** an automated KYC provider.

## Why this exists
Before this change the generic Django admin could edit seller status without a case reference or immutable review event. That is unsuitable for production seller trust and creates a bypass around listing approval. A suspended seller's already-active listings also remained discoverable. This workflow closes those gaps.

## Roles
- Applicant: after verifying email, applies with business name and adulthood attestation. Result is `pending`.
- Authorized seller reviewer: staff with explicit `accounts.review_sellerprofile` permission and secure staff session. Cannot review their own seller profile.
- Superuser: may assign reviewer permission, but cannot self-review.
- Regular moderator or seller: may not decide cases without permission.

## Staff review procedure
1. Validate the seller's identity/business evidence **outside the public app in a separately authorized, private process**. The app does not yet provide secure identity-document upload or automated KYC.
2. Create an internal, non-sensitive case reference (example `CASE-2026-001`) and privately store evidence in an approved system. Never put identity numbers, documents, addresses or secrets in GitHub or the review form.
3. Open Django admin `Seller profiles` → `Review case`. Choose decision, describe rationale (minimum 20 characters), include opaque case reference and tick evidence-reviewed confirmation for approvals.
4. Decisions are constrained: `pending → approved/rejected`, `approved → suspended`, `rejected/suspended → pending` only by reopening for review. Each decision creates a `SellerReviewEvent` including reviewer, time, from/to state and reason.
5. Suspension atomically moves all active seller listings to `removed`, with a `ListingEvent` per listing. Reopening and reapproving a seller does **not** automatically republish removed inventory; each listing needs a future individual re-review. Public marketplace queries also require currently approved/active sellers and trade-enabled species.

## Acceptance tests
- Approval rejected without verified email, active account, adult attestation or evidence case ID.
- Unauthorized staff/seller and self-review forbidden.
- No direct status edit in generic Django admin; review events cannot be edited/deleted there.
- Invalid transitions rejected; repeated approvals do not create duplicate events.
- Concurrent decisions serialized in Postgres via `select_for_update`.
- Suspended seller's active listings disappear immediately, with listing events and no automatic resurrection.
- No private review history or evidence case reference appears in public listing or account API.

## Remaining gates
This is a **manual pre-production workflow**. Do not claim a third-party KYC check or identity-document verification is integrated. Before real sales, implement private evidence storage with authorized signed URLs, define verification criteria and retention, vendor processor contract if used, support appeals, species/jurisdiction signoff, and approved payment partner. Never use a claimed seller badge as a health/pedigree guarantee.
