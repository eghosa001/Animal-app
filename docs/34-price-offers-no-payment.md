# Animal price negotiations — proposal and acceptance only

**Milestone:** buyers and approved sellers can negotiate a price for one specific approved animal in their private conversation. This does not enable payments, funds custody, an order, a deposit, transport coordination, or escrow.

## State machine

- A verified buyer or seller in an eligible, unblocked conversation may propose a quote in integer minor units of the listing's authoritative currency. The server rejects prices greater than the current listed amount and stores a snapshot for later audit. Default proposal validity is 72 hours.
- One pending quote may exist per conversation. A second proposal by the original proposer is rejected until the recipient responds or the quote expires. A recipient's counterproposal *supersedes* the prior pending quote and records a linked replaces reference and append-only audit events.
- Only the counterparty (never the original proposer) can accept or decline. Already accepted offers are idempotently returned only when the legitimate recipient retries acceptance.
- Acceptance acquires a row lock on the individual animal listing and checks other conversations for an existing accepted agreement. Thus **at most one negotiated price can be accepted for a particular listing**, even if multiple potential buyers have open conversations. Acceptance does not mark the listing sold, does not collect money, and does not guarantee purchase.
- If a seller is suspended, a species becomes trade-restricted, the listing is sold, a user is blocked, or an account becomes inactive, no new offer or decision is allowed. Historical proposals remain visible only to the original two participants.
- The no-payment warning must be visible before a price is accepted. **No payment link or wallet transfer exists in this milestone.**

## Endpoints

- GET /api/v1/offers/conversations/{conversation_uuid}/: private paginated history.
- POST /api/v1/offers/conversations/{conversation_uuid}/: amount_minor integer and client_nonce UUID. Repeat request with identical body returns the same offer.
- POST /api/v1/offers/{offer_uuid}/decision/: decision accept or decline. The server checks identity and the current listing state.

Flutter uses the existing NairaMoney integer parser and UUID nonce helper, with a stable retry nonce if the request outcome is uncertain. Never send client-provided currency or listing state as authoritative values.

## Required validation and next steps

Backend tests cover participant privacy, idempotency, money precision, counter/decline/accept transitions, expiry, restrictions after sale, blocking, price changes and cross-conversation acceptance prevention. Flutter tests validate amount parsing and explicit no-payment confirmation.

**Still required:** a compliant payment provider with actual licensed custody/split settlement features, clear fees and refunds, webhook signature verification, duplicate payment idempotency, financial reconciliation, transport/handover/welfare evidence, seller payout eligibility, admin disputes/appeals, store acceptance, and real-device QA. Paystack-style transaction splitting must not be described as licensed escrow unless that is what the actual signed contract and applicable regulation provide.

Payments remain disabled in backend settings; an offer is not an order or a charge.
