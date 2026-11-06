# Logical data model, constraints and migrations
Version 0.1 — 2026-11-05. Table names conceptual; migrations will define final fields.

## Species and inventory modelling note (2026-11-06)

The original one-Animal/one-Listing model is an initial **individual animal** scaffold, not the complete marketplace schema. The authoritative specification for individually identified animals, separately allocated litter members, legally permitted inventory lots, species-specific fields, health evidence provenance and reservation concurrency is [animal identity and inventory](22-animal-identity-and-inventory.md). Future schema migrations must follow that design after client confirms sales modes. Until then, litter/lot sales cannot be simulated by modifying individual-animal quantity and must remain disabled.

## Identity
- User(id UUID, email unique case-insensitive, phone optional unique after verification, password hash, email_verified_at, state, created_at).
- Profile(user FK unique, display_name, region, bio, avatar_asset, preferences).
- SellerProfile(user FK unique, seller_type, legal_region, approval_status, approved_at, risk_level).
- VerificationCase(seller FK, type, provider_reference, submission_status, reviewer FK nullable, reason, timestamps).
- RoleGrant(user FK, permission_scope, granted_by, expires_at), Session/Device, Block(actor, target, timestamps).

## Catalog and commerce
- Species(id, scientific_name, common_name, trade_policy_code, allowed_regions, category).
- Breed(id, species FK, label, aliases, optional); avoid requiring breed for mixed/unclassified animals.
- Animal(id, seller FK, species FK, breed FK nullable, sex, birth_date_or_estimate, welfare_status, stable_public_id).
- AnimalAttribute(animal FK, key from species schema, value typed) validated against species schema.
- AnimalHealthDocument(animal FK, private_asset FK, kind, self_reported_vs_reviewed, verification_status, expires_at).
- Listing(id, animal FK, seller FK, title, description, region_general, price_minor BIGINT, currency, moderation_status, availability, reserve_expires_at, published_at, archived_at).
- ListingMedia(listing FK, asset FK, position, alt_text).
- Favourite(user, listing UNIQUE), ListingView aggregated for analytics, Report(target_type/id, reporter FK).

### Core listing invariants
One active sellable listing per individual Animal unless explicit business case approved. Disallow animal sale if species/region policy prohibits. Seller must be verified for checkout. Hide sold/unavailable inventory from buy CTAs. Do not expose exact private addresses to listing search.

## Social and media
Post(id, owner FK, visibility, caption, status, optional listing FK, published_at); MediaAsset(id, owner FK, provider, provider_asset_id, type, processing_status, moderation_status, duration_sec, dimensions, private flag); PostMedia(post FK, asset FK, order); Comment(post FK, author FK, parent FK nullable, state); Reaction(actor, target UNIQUE); Follow(follower, followed UNIQUE); ViewEvent(sampled/idempotent analytics, duration).
Store external playback IDs not sensitive media signing secrets. Strip EXIF GPS from public images.

## Messaging and offers
Conversation(id, listing FK nullable, kind, created_at); Participant(conversation FK, user FK UNIQUE per pair, last_read_message, muted_at); Message(id, conversation FK, sender FK, client_message_id UUID, body, kind, created_at, redacted_at, moderation_flag); UNIQUE(sender, client_message_id) for safe retries.
MessageAttachment(message FK, asset FK, permission).
Offer(id, listing FK, buyer FK, seller FK, current_amount_minor, currency, state, expires_at, accepted_at, parent_offer nullable), OfferEvent append-only state changes. Never trust client-submitted seller ID or price on checkout.

## Protected order and finance
Order(id, listing FK, animal FK, buyer FK, seller FK, offer FK nullable, listing_snapshot JSON, amount_minor, currency, commission_rate_basis_points, provider, order_state, payment_deadline, created_at).
OrderTransition(order FK, from, to, actor_type/id, reason, metadata, timestamp); idempotency key unique.
PaymentAttempt(order FK, provider_reference UNIQUE, state, amount_minor, currency, confirmed_at).
ProviderWebhookEvent(provider, external_event_id UNIQUE, payload_hash, verified, received_at, processed_at).
LedgerAccount(id, account_type, currency); LedgerEntry(id, journal_id, account FK, signed_amount_minor, timestamp); CHECK journal per currency balances to zero at posting.
PayoutInstruction(order FK, partner_reference UNIQUE, status, release_authorization, processed_at), RefundInstruction, ReconciliationRun.
**A ledger reflects financial claims and payment provider confirmations; it does NOT mean Anima holds regulated customer money.**

## Delivery, safety, operations
Fulfillment(id, order FK unique, method, transport_partner FK nullable, region, state, scheduled_at, delivered_at); HandoverProof(id, fulfillment FK, kind, evidence_asset, party, timestamp); Confirmation(order FK, signed_by, confirmation_method); Dispute(order FK, complainant FK, category, state, hold_requested_at, resolution); DisputeEvidence, DisputeDecision, Appeal.
ModerationCase(target, reporter, priority, state); ModerationAction(actor, action, previous_status, new_status, reason, timestamp); AuditLog(actor, action, object_ref, request_id, before/after safe diff, timestamp).
Notification(user FK, type, payload, read_at, delivered_at).

## Indexes and retention
- Index listing(active status, species, region, published_at DESC); price and full-text search; explain/query test with realistic volume.
- Index post(published_at DESC, visibility); comment(post, created_at); conversation participants by user; message(conversation, created_at, id).
- Unique idempotency keys and provider reference, partial unique constraints on active orders/reservations where applicable.
- FK policies: restrict deleting financially relevant records; soft-delete public content; anonymize PII only under approved retention rules.
- For GDPR/NDPA compliance, delete/retire private documents after a documented retention period; legal holds override deletion where lawful.
- Migration strategy: additive and backward-compatible changes; rollback code before destructive schema migration; snapshot/restore tests.

## Concurrency and consistency acceptance tests
1. Two simultaneous checkout attempts on same animal -> exactly one active reservation/order.
2. Webhook delivered 20 times -> one credited payment event and one balanced journal.
3. Buyer cancellation vs handover event race -> only allowed transition; manual case if ambiguous.
4. Seller changes listing price after order -> order amount unchanged.
5. Blocked user cannot view private chat/attachments through direct URL.
6. Moderation removal makes listing unbuyable immediately even if cached.
