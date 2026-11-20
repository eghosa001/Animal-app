# M4 foundation: unfunded order requests

## Purpose and scope

After a buyer and seller agree to a specific animal's price using the private Offers workflow, **only the buyer** can explicitly save an order request for future checkout. This is **not** an animal reservation, completed purchase, payment, escrow, payment guarantee, confirmation of availability or proof of ownership transfer. No customer money is accepted or moved.

A separate licensed/approved checkout partner must be contracted, independently integrated and tested before live animal purchases can be enabled. Until then, do **not** collect bank account numbers, pickup street addresses, identity documents or payment cards in ordinary messages or order requests.

## Backend state and invariants

- An OrderIntent is possible only when its corresponding AnimalOffer is accepted; the buyer and seller must remain eligible, the seller-approved listing must be active, the species approved for trade, both users unblocked, the seller still the registered animal owner and the agreed currency/amount still valid.
- The buyer acknowledges in the POST body that the request does not collect payment, escrow funds, reserve inventory or schedule delivery. Server enforces this, not only Flutter.
- PostgreSQL row locks serialize creation for a particular listing, and database OneToOne uniqueness enforces **one intent per accepted offer and one per animal listing**. Repeated requests with the same buyer nonce and offer return the same receipt; a different nonce cannot create a second request.
- Snapshot: exact animal UUID and declared name, public listing title and region, agreed minor-unit price, currency, buyer and seller. A later listing edit cannot mutate these persisted values. No precise addresses or private health/identity attachments.
- Initial status: `awaiting_partner`; only another permitted prepayment state is `cancelled`. No request changes the listing's sale status or sends money. Both buyer and seller can cancel with a 20–240-character reason. The audit trail records initial creation and one cancellation, and repeat cancellation is idempotent.
- Existing private order receipts remain readable by both parties even if the listing later becomes unavailable or the participants block each other; strangers receive no details.
- JSON responses always have `checkout_available=false`, `funds_secured=false` and `animal_reserved=false`; the client **must not** present those as true. No payment, payout, refund, delivery-confirmation or protected-handover API is exposed.
- Transporting live animals, scheduling a handover and collecting addresses are explicitly excluded until a reviewed logistics and species-specific welfare workflow exists. The `pickup_planned` field is an unconfirmed future preference, not a booking.

## API

- `GET /api/v1/orders/intents/` — paginated receipt history for the signed-in buyer or seller.
- `POST /api/v1/orders/intents/` — buyer-only, with `accepted_offer_id`, `request_nonce` and required `no_payment_acknowledged=true`.
- `GET /api/v1/orders/intents/{uuid}/` — participant-only receipt.
- `POST /api/v1/orders/intents/{uuid}/cancel/` — participant-only, documented reason.

Write APIs are rate-limited. User-visible backend outputs contain no invented checkout links, processor confirmation, amounts charged, delivery success or refund promise. The Flutter Profile page shows "My order requests", and an accepted price in the buyer's offer screen allows a guarded request-creation flow after an explicit no-payment dialog.

## Automated acceptance

Regression tests cover unverified accounts, guests, seller vs buyer permissions, stranger access, explicit consent, UUID request idempotency, duplicate listing/offer constraint, price/currency and animal-owner safety, blocked users, sold or restricted inventory, immutable snapshots, proper cancellation auditing and non-existent payment/delivery endpoints. Flutter tests cover major/minor money display, buyer-only creation, consent/cancel, and cancellation receipt.

**Staging/production not delivered.** Real-device Android and iOS tests, live protected checkout provider approval and sandbox contract tests, legitimate commission model, licensed funds holding, transport arrangements, welfare papers, handover/inspection proof, disputes/refunds and reconciliation remain mandatory P0 work. The platform must not market this prototype as an operational animal escrow or order delivery service.
