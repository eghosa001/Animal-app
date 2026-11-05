# Protected commerce, payment partner, delivery and disputes
**Launch blocker: provider's written approval required.** Updated 2026-11-05.

## Regulatory/commercial boundary
The business requests a buyer payment to be held until an animal is delivered, less platform commission. Do not assume any ordinary gateway provides legal escrow. Paystack currently lists escrow services as ineligible (https://support.paystack.com/en/articles/2127042). Flutterwave terms require marketplace pre-approval; split payouts do not automatically constitute an escrow hold. Obtain written underwriting and legal opinion identifying money custodian, permitted animal categories, hold durations, payout controls, chargeback policy, operating countries and insurance needs. Platform must not represent funds as being held by Anima without appropriate legal authority.

Build against **MockProtectedPaymentProvider** in development. Production payment feature flag OFF by default. Provider-specific adapter only after signed approval, sandbox credentials and contract review. Never put merchant secret keys in the mobile client or commit them.

## Commercial terms requiring approval
Commission rate (5% is only an example), processing/chargeback fee responsibility, who pays delivery, taxes, cancellation charges, payout minimum, acceptance window, qualified veterinary evidence, dispute and appeal window, payout hold period and jurisdiction. Buyer sees full breakdown before authorizing payment. No implicit fees.

## State machine
Offer accepted -> ORDER_CREATED -> PAYMENT_PENDING -> PAYMENT_CONFIRMED_BY_PROVIDER -> FUNDS_SECURED_BY_PARTNER -> FULFILLMENT_READY -> IN_TRANSIT / PICKUP_SCHEDULED -> HANDED_OVER -> INSPECTION_WINDOW -> RELEASE_ELIGIBLE -> RELEASE_AUTHORIZED -> PROVIDER_PAID_OUT -> CLOSED.
Branches: PAYMENT_FAILED, EXPIRED, CANCEL_REQUESTED, CANCELLED, DISPUTED, REFUND_AUTHORIZED, REFUNDED, CHARGEBACK_REVIEW, ESCALATED.
No jumps around verified payment, delivery, or dispute gates. A seller's own “delivered” click cannot authorize release. Buyer confirmation alone may also be insufficient for a disputed welfare case.
Transitions occur atomically in PostgreSQL with actor, source event and state change recorded.

## Provider adapter interface
- create_checkout(order_id, immutable amount, currency, idempotency_key)
- verify_and_ingest_webhook(raw_body, headers) -> signed unique provider event
- get_payment_status(provider_reference)
- verify_funds_segregated_or_held(provider_reference) where provider supports
- request_hold_release(provider_reference, payout_instruction, authorization)
- request_refund(provider_reference, amount, rationale, authorization)
- get_settlement_and_reconciliation_report(date_range)
If a candidate provider cannot offer the required hold/release semantics, reject it or redesign the product **with explicit buyer notice**, not a silent ordinary split payment.

## Double-entry accounting
Post balanced journals for payment confirmation, partner-held liability, platform commission receivable, seller payable, provider fees, refunds and authorized settlements. Currency and amount in integer minor units; commission represented in basis points or decimal-backed immutable snapshot. A journal must balance before becoming posted. Partner bank balance is not assumed from the internal ledger: daily reconciliation compares provider reports, webhook events, and ledger. Unmatched funds block payouts and alert finance.

## Idempotency and anti-fraud
Unique partner reference, event ID, checkout key, refund key, payout key; verified timestamps/signatures; delayed/out-of-order webhook handling; database row-level locks on sale and payment state. Never fulfill solely from a redirect success page. No full card numbers stored. Manual payout override needs multi-person authorization and audit.

## Delivery and animal welfare
Support (A) scheduled buyer pickup, (B) approved live-animal transporter. Record the agreed animal identity, fulfillment address privately, transport region, suitable species-specific conditions, responsible parties, welfare/health paperwork and completion evidence. Prohibit unsupported shipping methods. International movements disabled until permits, transport partner and veterinary/regulatory workflows exist.

Handover: identity match + two-party confirmation or independent transport proof + optional one-time code + time-based inspection policy. Evidence uploads are private, retention-limited and signed.
Delay, injury, death, lost animal, or medical emergency -> immediate welfare/support escalation and payout hold as policy permits.

## Disputes
Categories: non-delivery, wrong animal, documented material misrepresentation, serious disclosed health discrepancy, unlawful sale, buyer pickup default, transporter incident. Submission -> triage -> request evidence -> independent review as appropriate -> decision -> refund/payout instructions -> appeal -> closure. Payment provider makes/executes regulated fund movements under contract; internal admin never transfers held buyer funds manually. Preserve records under legal hold.

## Off-platform notice
“Purchases and direct transfers arranged outside the platform are not covered by the platform's payment protection or transaction dispute process. Report suspicious requests. This notice does not restrict rights that cannot legally be excluded.” Show beside messaging payment/contact cues and checkout.
Do not advertise an absolute exclusion of liability.

## Finance acceptance before live launch
- Signed provider approval and lawful custody model.
- Verified webhook signature and replay handling.
- Sandbox duplicate/out-of-order/refund/dispute/chargeback tests.
- Journal balances; independent daily reconciliation; exception queue.
- Per-order fee breakdown and buyer consent receipts.
- Unauthorized payouts impossible, including staff impersonation cases.
- Reviewed refund, dispute, welfare and transport contracts.
- Refund and payout runbooks exercised with test cases.

## Official reading
- https://support.paystack.com/en/articles/2127042
- https://www.flutterwave.com/ng/terms (verify exact regional policy and current wording before contracting)
- https://developer.apple.com/app-store/review/guidelines/ (physical goods vs digital boost purchases)
- https://support.google.com/googleplay/android-developer/answer/9858738
