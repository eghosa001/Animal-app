# Species, animal identity, welfare and inventory specification

**Version:** 0.1, 2026-11-06. **Launch policy:** All commercial trade remains disabled until legal/species review; this document is a proposed domain design, not a veterinary or legal certification.

## Why the current animal and listing models are insufficient

The present models handle a single Animal with one Listing, basic species/breed labels, a seller and a price. That is acceptable for foundation tests, but cannot safely handle a breeder's litter, multiple fish, livestock groups, staged vaccination records, multiple animals offered within one media post, country-specific restrictions or a proper transfer history.

Avoid simply adding a "quantity" field to individual animals: two buyers might then acquire the same identifiable animal or receive an animal that did not match advertised health records.

## Explicit inventory modes

| Mode | Representation | Buyer selection and evidence | Availability invariant |
|---|---|---|---|
| INDIVIDUAL | Animal has permanent public ID; one active sale/listing | Exact animal with seller-provided source and declared health records | A single animal has at most one confirmed sale and one active reservation |
| LITTER | Parent Litter and separately identified offspring Animals | Buyer chooses/reserves specific offspring; each has own age/sex/health where known | One offspring cannot be allocated twice; litter listing's available count is computed from eligible offspring |
| GROUP_OR_LOT | InventoryLot records allowed quantity/unit/species/grade/condition | Quantity and per-unit price in approved category; actual delivered count confirmed | Atomic reservation decreases remaining availability; partial fulfillment/refunds are separately modeled |
| ADOPTION | Separate rescue/rehoming flow with screening and fee rules | Explicit adoption obligations and legitimate organization | Not treated as a commercial protected purchase unless separately approved |
| SERVICE | Vet/grooming/boarding | Separate future service module | Never misrepresented as an animal listing |

**First commercial launch:** Implement INDIVIDUAL well. LITTER or GROUP_OR_LOT must remain feature-flagged off until its allocation, pricing, cancellation and welfare handling passes its own tests.

## Proposed entities and ownership

- SpeciesPolicy: species, country/subdivision, allowed_for_sale, permitted inventory modes, minimum sale age if applicable, licenses/permits, document requirements, transport restrictions and effective dates. Default deny; changes audited and approved by designated policy owners.
- Breed: canonical breed, species, aliases, unregistered/mixed option, no "purebred" claim inferred from a label.
- Animal: stable UUID, seller-declared name/type, sex, birthdate or estimated-age marker, identification method, source/ownership declaration, wellbeing status and private supporting evidence.
- Litter: seller, species, eligible parent references when known, birth/age group, provenance; members modeled as separate Animals; may not force a pedigree claim.
- InventoryLot: species and lawful commodity subtype, defined unit (head/fish/etc), total/available quantity, conditions and evidence; only supported species.
- Listing: independent published marketing object with state and immutable publication snapshots; exact item(s) or lot allocation model; prices in minor units and ISO currencies.
- Reservation: buyer, order, exact individual-animal IDs or lot allocation, expiry and conflict constraint.
- AnimalDocument: species-specific type, subject, issuer declared, issued/expiry dates, private original, verification state, reviewer case, consent/retention. Health documents are not public by default.
- Ownership/transfer event: historical provenance and fulfillment reference, visible only where legally appropriate; ownership changes only after valid handover according to policy.

## Species-specific information (config-driven, not 20 hardcoded forms)

| Category | Example conditional attributes | Safety/welfare questions |
|---|---|---|
| Dogs and cats | breed/mix, sex, date of birth, microchip if applicable, vaccinations, medical declarations, lineage proof if claimed | Minimum lawful rehoming age, disease/disclosure rules, transport fitness, responsible breeding |
| Rabbits and small pets | species/breed, weaning status, age, sex, health, housing needs | Heat stress, transport method, sourcing and welfare |
| Domestic birds | species, age, sex if known, leg band/ID if available, source and health certificates | Protected-species restrictions, disease/biosecurity and lawful movement |
| Aquarium fish | species, approximate size, freshwater/marine, count, breeding/captive origin, quarantine notes | Packaging, oxygen/temperature, transport duration and invasive/prohibited species |
| Livestock | species/breed, age, quantity/mode, sex, ownership/source, vaccinations or movement documents where required | Movement permits, disease control, livestock welfare and validated group allocation |

This table does NOT assert any species is legal to sell or any specific vaccination is legally mandatory. A qualified jurisdiction-specific reviewer decides and records such rules.

## Health/identity provenance: distinct levels

1. **Seller declared:** owner has entered information; not independently verified.
2. **Document submitted:** a private report has been uploaded, not necessarily authenticated.
3. **Document reviewed:** authorized reviewer checked the submitted document for visible completeness/consistency.
4. **Issuer independently verified:** issuing veterinary/laboratory authority has been independently checked with permission, timestamp and documented scope.

UI must show exactly what was verified, by whom (role/provider), when, and any expiry. “Verified seller” is not “healthy animal”, “purebred”, “vaccinated”, or “disease free”. Lab/health documents require consent and may be hidden, summarized, or shared only with authorized buyer, depending on policy. The platform must not manufacture veterinary diagnosis.

## Listing lifecycle

Draft -> submitted -> under review -> active -> reserved -> sold/closed. Alternate: rejected (editable, resubmit), paused, expired, removed for risk/policy breach, disputed. Reopening a suspended seller cannot automatically republish a prior removed listing. Listing/media consistency must be recalculated after policy, breeder verification, animal welfare or order status changes.

Seller can edit a **draft**; modifying identity, legal category, health disclosures, price or critical claims on an approved listing may require re-review and must never change an accepted offer or order snapshot. Provide meaningful seller and moderator audit trails.

## Concurrent purchase protection

- Use database uniqueness, transactional row locking and precise item allocation at reservation creation; expiry has a single authoritative clock.
- Payment attempts always reference an immutable order and reservation; if a payment arrives after expiry, quarantine for provider-approved refund/manual resolution, never silently sell inventory again.
- No double-sale even with delayed webhook, client retry, cancelled delivery or two app devices.
- Lot purchases reserve exact quantity atomically and support valid partial outcomes.
- Sold animal cannot become available merely because social post still links to old listing.
- Refund of a completed order does not automatically return a living animal to available inventory; legal/welfare and ownership review first.

## Uploads, document access and PII

- Public listing images: scanned/validated content, remove precise EXIF geolocation, optimize variants, moderated before sharing.
- Sensitive identity, license, health and transport evidence: separate private storage; short-lived signed URLs authorized server-side; retention and audit, no direct public R2 URL, no media processing provider that leaks content to public feed.
- Do not attach personal documents to regular chat or logs. Animal identification numbers may be redacted in public view.
- Test file spoofing, oversize, reused signed URLs, deleted-account access, deleted/expired links, mixed seller/buyer permissions.

## Quality acceptance tests

1. Two simultaneous reservations on same animal -> only one succeeds.
2. Seller with suspended status -> zero purchasable active inventory, including stale deep links.
3. Species disabled while listing active -> order creation blocked and public listing hidden.
4. Litter member reserved twice -> second fails; total available recomputed.
5. Batch quantity over-reserved -> atomic rejection without partial corruption.
6. Accepted offer amount and animal identity cannot be changed by later edit.
7. Health claims rendered with correct verification tier and expiry.
8. Buyer without authorization cannot download sensitive reports or precise pickup address.
9. Reviewer rejection/suspension blocks relevant media CTA and checkout.
10. Refund or delivery dispute does not automatically recreate available animal inventory.

## Decision requirements

Client must approve launch species, exact sales modes, minimum required document sets, health verification vocabulary, vet/issuer permissions, supported territories, animal delivery responsibilities, allocation policy for litters, order cancellation and welfare incident handling. The default is conservative: disable a mode rather than guess.
