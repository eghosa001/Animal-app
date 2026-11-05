# Product requirements document (PRD)
Version: 0.1 — 2026-11-05. **Planning, not approved commercial or legal terms.**

## Vision and outcome
A mobile-first, animal-only community and marketplace for lawful domestic animals. An adult may watch or post animal-related videos without buying/selling. Verified sellers list animals, negotiate in contextual chat, arrange lawful transportation/pickup, and accept **provider-controlled protected checkout**, subject to the payment partner's express approval. Buyers have clear delivery/dispute procedures. The marketplace charges a disclosed commission. Build Android and iOS on a shared Flutter codebase with a responsive web admin.

**Boundaries:** This is not a general-purpose video app, veterinary diagnosis provider, animal registry, shipping company, broker holding money in its own account, or a promise of guaranteed animal health. No sales of protected wildlife or prohibited animals. No direct DB access to existing pedigree projects.

## Personas and roles
- Enthusiast: animal-only feed, follow, react, comment, post, report, block.
- Buyer: search/filter/save listings, open seller profile, negotiate, make order, checkout, receipt, handover, dispute, review.
- Seller/breeder: apply for verification, publish listings, post videos, answer inquiries, accept offers, see earnings and order history.
- Rescue organization: separate verified adoption pathway and screening; never disguise adoption fees as sales.
- Moderator: review suspicious posts, animals, sellers, reports, appeals.
- Finance/operations: reconcile payments, investigate disputes, authorize eligible payouts, maintain audit trail.
- Super-admin: configuration, role assignment, exceptional approval (must not override ledger controls).

Accounts have capabilities, not mutually exclusive labels. Adult-only commerce and seller enrollment initially. Determine legal age/guardian arrangements before any public minors' account onboarding.

## Feature priority and acceptance
| ID | Priority | Capability | Acceptance evidence |
|---|---|---|---|
| AUTH-01 | P0 | Signup/login/email confirmation, recovery, sessions | Duplicate emails rejected; reset token expires; brute-force throttled |
| AUTH-02 | P0 | Sellers reviewed before selling | No unapproved seller can activate checkout |
| ANI-01 | P0 | Species/breed schema, allowed-trade policy | Prohibited species cannot be published as listings |
| LST-01 | P0 | Animal listings and photo gallery | Fields validated by species; draft/review/active/sold |
| LST-02 | P0 | Search, location, filters, favourites | Pagination and authorization; no exact private addresses |
| CHAT-01 | P0 | Persistent 1:1 inquiry chat | Receipts, reconnects, offline continuity |
| OFFER-01 | P0 | Binding structured offer negotiation | Accepted offer snapshots price/currency/seller/listing |
| ORD-01 | P0 | Exclusive reservation + order state | Two buyers cannot pay for same individual animal |
| PAY-01 | P0, gated | Approved external hold/release mechanism | Contract, sandbox tests, verified webhooks, reconciliation |
| DEL-01 | P0 | Pickup/approved transport and handover record | Buyer confirmation or independent evidence and disputes |
| SOC-01 | P0 | Animal photo/video posts and follows | Upload/processing/publish states, player and feed |
| SOC-02 | P0 | Reactions/comments/report/block | Moderator review and removals; user blocking effective |
| ADM-01 | P0 | Staff verification/report/order/dispute queues | RBAC; full audit for high-risk actions |
| NOT-01 | P0 | In-app and mobile push notifications | Offline notifications and opt-out choices |
| LEG-01 | P0 | Privacy, terms, rules, help, account deletion | Store-review and legal acceptance checks |
| SELL-01 | P1 | Storefront analytics and reviews | Reviews only after qualifying completed transactions |
| DISC-01 | P1 | Saved searches, notification alerts, recommendation ranking | Opt-in alerts; explainable baseline |
| ADOPT-01 | P1 | Verified rescue/adoption listings | Separate terms, no protected-sale checkout by default |
| LIVE-01 | P2 | Live streaming and video calls | Separate moderation and cost gates |
| VET-01 | P2 | Vet services and pedigree integration | Explicit consent, credential checks and integration contract |
| BOOST-01 | P2 | Promoted listings and subscriptions | Separate mobile-store digital-purchase compliance |

P0 = launch-critical; P1 = post-beta improvements; P2 = later. If payment partner is unavailable, a **non-transactional private beta** may demonstrate listings, video, chat, and offers only; production commerce is blocked.

## User journeys
### Buyer
Onboard -> select animal interests -> feed/market search -> listing -> verified seller profile -> listing-linked chat -> make offer -> accepted offer -> signed terms and exact order amount -> partner checkout -> payment verified -> pickup/transport -> inspection & handover -> confirm OR dispute -> payout eligibility -> review. Every step has a clear next action, receipt, and support route.

### Seller
Signup -> identity/business submission -> verified/denied -> create animal profile -> upload evidence -> create listing -> content/moderation review -> activate -> receive inquiry -> accept/decline/counter -> fulfillment milestones -> payout eligibility after policy gates -> earnings and dispute history.

### Creator
Post animal-only media -> moderation processing -> published feed -> discoverable by relevant animal interests -> engagement/reporting; optional attach active animal listing.

### Admin
Verify documents with least privilege -> inspect reporting queue -> remove/restore content -> review delivery dispute and evidence -> separate finance approval -> audit and escalation.

## Mobile information architecture
Five tabs: Home (For You/Following), Marketplace, Create (+), Chats, Profile. Seller Hub and Orders are accessible from Profile, order CTAs, and notification deep links. Search accessible from Home/Marketplace; reported content reachable from every relevant view.

## Product rules
- The platform shows an off-platform warning before or near contact/payment exchanges. Off-platform payments receive **no platform payment protection**, without unlawfully waiving statutory rights.
- Health and pedigree evidence must be labeled **seller-submitted**, **document-reviewed**, or **independently verified**. Never conflate them.
- Only approved species in configured jurisdictions can be listed. Animal content may be educational but never facilitate prohibited trade/abuse.
- Prices and currencies are immutable snapshots on accepted orders. Commission is disclosed before payment.
- Delivery of living animals is not ordinary package shipping; transport suitability, region, season and welfare may prohibit a method.
- Every public post/listing has reporting and appeal routes. Reviews cannot be purchased.
- Do not enable minors to conduct commerce without approved legal design.
- No user content used to train external AI without appropriate notices, permission and lawful basis.

## Nonfunctional requirements (initial targets, validate on load tests)
- API p95 <400 ms for cached/simple reads at an agreed benchmark; complex searches documented separately.
- Chat active-session delivery usually <1 s on stable network; persistent offline retries.
- Crash-free mobile sessions target >=99.5% during beta.
- 100% duplicate payout prevention and balanced financial ledger.
- Every high-risk financial/identity action produces tamper-evident audit metadata.
- Designed for intermittent Nigerian mobile connectivity, dark/light themes, accessibility, and low-end Android devices.

## Product analytics and success
Track qualified buyer-to-seller inquiries; active verified sellers; active listings; listing-to-inquiry conversion; completed protected orders; time-to-handover; dispute rate; payout failures; repeat creators; moderated unsafe-content response time; video watch minutes/storage cost; buyer retention. Avoid vanity downloads as sole KPI.

## Launch boundaries and unknowns
Nigeria-first **assumption**, not yet client-approved. Initial species eligibility, commission % (illustrative 5%), holding window, delivery responsibility, age policy, refunds, marketplace legal entity, and hosting budgets need written signoff. All must be recorded in decisions log before enabling production orders.
