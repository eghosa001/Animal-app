# Engineering agent guidance — Animal-app

Read README.md and all docs that apply to the change. The project is **in planning**; no live infrastructure/payment authority exists yet.

## Constraints
- Keep the new monorepo independent of the existing Cane Corso Ancestry project. Never use its production database, buckets, credentials or release workflows.
- No live protected-payment processing until client payment provider underwriting, contracts and legal signoff; start with mock and sandbox adapters.
- Use server-side authorization for every resource; animal trade categories configured by jurisdiction; owner of media and private documents checked on access.
- Preserve ledger double-entry and payout idempotency; test concurrent order acquisition; no direct payout-from-admin shortcuts.
- Make mobile UX fast, accessible, responsive, low-bandwidth tolerant and separately tested on Android and iOS.
- Do not upload secrets to version control, tests, logs or messages; use environment and secret manager.
- Prefer focused, proven open-source components; avoid premature microservices and expensive SaaS without quantified need.
- Prepare tests and migration/release notes for every functionality change. Enforce required checks before production release.
- Cite official vendor docs when changing price, compliance or platform requirements; mark estimates as assumptions.

## Proposed development order
M0: specs + scaffolding + CI -> M1: users/listings -> M2: chat/offers -> M3: social/video -> M4: partner-approved payments/delivery -> M5: safety/performance -> M6: beta/stores.

## PR expectations
PR description must specify requirement ID(s), user value, change summary, security and legal impact, schema/API changes, tests executed, deployment/rollback plan and any unresolved decision. Use concise, verified status; never claim simulated functionality is live.

## Decision gates
Money custody, animal welfare/trade eligibility, app-store billing, identity retention, and client ownership require documented owner approval. If unclear, implement safe mock/stub and track blocking decision; do not silently pick a provider or legal interpretation.
