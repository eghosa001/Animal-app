# Architecture decision records and risk register
Version 0.1 — 2026-11-05. Status: proposal unless noted as repository planning decisions.

## Recorded technical decisions
| ID | Decision | Why | Status |
|---|---|---|---|
| ADR-001 | Independent Animal-app monorepo | Avoid breaking Cane Corso Ancestry production | Accepted for planning |
| ADR-002 | Flutter shared mobile codebase | Android/iOS delivery with one app team | Proposed |
| ADR-003 | Django modular monolith, not microservices | Coherent order+finance transactions, lower complexity | Proposed |
| ADR-004 | PostgreSQL canonical DB, Redis transient | Relational safety and cheap realtime | Proposed |
| ADR-005 | Cloudflare R2 for images/documents; Stream for video | Adaptative video and predictable duration-based cost | Proposed, cost gate |
| ADR-006 | Partner-held protected checkout only with written approval | Financial regulatory risk and escrow semantics | Mandatory gating principle |
| ADR-007 | Admin starts with Django Admin | Faster robust moderation workflows | Proposed |
| ADR-008 | No general-purpose media outside animal topic | Product position and safety | Accepted as product requirement |
| ADR-009 | Nigeria-first, approved domestic-animal listing categories | Manageable legal and shipping scope | Assumption, client approval needed |
| ADR-010 | No direct access to existing Cane Corso database | Privacy, uptime, independent ownership | Mandatory |

## Decision template
ID; title; date; owner; background; options; chosen option; tradeoffs; security/legal impact; rollback; linked GitHub issue; approval. Never rewrite historical ADR; supersede with new record.

## Risk register (rank based on impact/likelihood, review with client)
| Risk | Impact | Mitigation | Gate/owner |
|---|---|---|---|
| No financial partner supports actual hold/release | Critical | Mock integration, written underwriting, alternate legal model only with informed product redesign | Client legal/finance before payments |
| Unauthorized animal categories/wildlife trade | Critical | Species policy engine, geo controls, staff review, counsel | Trust/safety before commerce |
| Counterfeit breeders/animal health claims | High | KYC, verification tiers, evidence provenance, post-sale reporting | Seller verification |
| Live animal injured or dies in transport | Critical | Approved transport, welfare policy, emergency escalation, insurance | Operations/legal |
| Chargeback/negative seller balance | High | Provider dispute policy, reserves and reconciliation | Finance |
| Viral video hosting cost blowout | High | Hard media limits, client prefetch limits, budgets/alerts | Engineering/finance |
| Store rejection due to UGC/payment policy | High | In-app report/block, data deletion, approval letters, demo account | Release |
| Unauthorized staff access or account takeover | Critical | MFA, RBAC, audit, least privilege, response runbooks | Security |
| User private messages/IDs leaked | Critical | Object-level ACL, encrypted evidence, privacy review | Security |
| Deployment corrupts financial DB | Critical | Backups, staged migrations, restore drill, immutable ledger | Backend/operations |
| Overengineering stalls launch | Medium | Focused vertical slices, P0 gates, modular monolith | Engineering |
| Client-owned account not ready | Medium/High | Account checklist and lead times; no personal password reuse | Product owner |
| Premature global launch | High | Nigeria pilot with local compliance first | Product/legal |

## Open questions for client signoff
1. Confirm legal entity, product name and owner of developer accounts.
2. Nigeria pilot or other countries; available jurisdictions/currencies.
3. Explicitly permitted animal types at launch; vaccination/transport requirements.
4. 5% commission or other rate; who absorbs processing/chargeback costs.
5. What constitutes delivery and acceptable inspection window, including vet evidence and welfare.
6. Must rescues/adoptions transact through paid flow or separate?
7. Age/guardian policy, creator rights, licensed veterinarians, platform insurance.
8. Seller verification types and who pays KYC checks.
9. Content duration/upload volume/free creator quotas and moderation staffing.
10. Available launch/recurring budget; return/refund reserves.
11. Brand theme, language and localization; admin staff roles.
12. Contracted ownership of code, assets, designs and ability to reuse existing site concepts.

## Additional high-impact risks identified in the completeness audit (2026-11-06)

| Risk | Impact | Required control |
|---|---|---|
| Individual animal, litter or livestock lot sold twice | Critical | Explicit inventory modes, unique allocation, transactional reservations, expiry and refund/manual reconciliation |
| Animal health/pedigree claims mistaken for independent verification | High | Provenance tiers and expiry; truthfully labelled seller-supplied vs document-reviewed vs independently verified |
| Malicious uploads expose documents or location metadata | Critical | Private evidence store, media validation, authorized time-limited access, EXIF redaction and retention |
| Seller loses approval while order/listing remains accessible | Critical | Server-side eligibility recheck, immediate listing removal, held-order exception handling and audit |
| Missing password recovery/account deletion or staff MFA blocks store/privacy readiness | High | Dedicated requirements AUTH-03/AUTH-04/PRIV-02 and app-store compliance tests |
| Chat/reviews used to deceive buyers or circumvent payment protection | High | Clear non-waivable-rights notice, fraud reports, verified-transaction reviews and moderated appeals |
| Developing every P2 feature stalls a safe launch | High | P0/P0-conditional gate, disable unapproved sales modes, postpone P2 until core reliability proven |

See [feature completeness audit](21-feature-completeness-audit.md), [animal identity/inventory](22-animal-identity-and-inventory.md) and [definition of done](23-definition-of-done-and-acceptance.md). These are planning controls, not substitutes for qualified legal, financial or veterinary review.

## Planning rule
If a decision impacts money custody, animal legality, user safety, store policy or data protection, it is a written launch gate, not an unchecked implementation assumption.
