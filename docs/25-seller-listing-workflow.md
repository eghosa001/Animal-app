# M1 seller listing workflow — implementation and release checks

**Implementation:** Backend draft API PR #17; gallery removal PR #18; Flutter listing UI PR to follow. All public trade remains default-denied.

## Seller journey

1. Register and verify email; apply to become an adult-eligible seller. Approval is a human staff action with an audit case.
2. Open the app **Create** tab or **Profile → Manage animal listings**.
3. Choose one animal category from the server catalogue. The form deliberately supports one identified animal (INDIVIDUAL), not litters, flocks, aquarium lots or wholesale inventory.
4. Enter title, individual animal name, optional breed/variety, sex (unknown is permitted), estimated age (optional), coarse city/state location, price in NGN and truthful animal description. Currency parses to integer kobo, not floating point.
5. Save private draft; it never becomes public by saving. Existing drafts may be edited until submission; animal species cannot be changed while gallery photos remain attached. All changes are reauthorized on the server and stored in one PostgreSQL transaction.
6. Add up to eight JPEG/PNG photos from a device. Every uploaded photo is private pending moderation. Photos can be removed from drafts only; removing a photo hides it and creates an event record, while the retained object awaits approved erasure policy.
7. Seller must be approved, animal species enabled for commerce under reviewed policy, and at least one photo uploaded to request moderation. The server—not mobile state—enforces this.
8. Staff must independently approve an animal photo before the submitted listing can become public. After submission, seller title/animal/price changes are blocked in this version; more complex re-review/edit workflows require a separate feature.
9. A public listing appears only when its status is ACTIVE, seller currently APPROVED/active, species trade-enabled and photo moderated. Suspension hides the listing and media.

## API

| Operation | Endpoint | Permissions |
|---|---|---|
| All current species candidates | `GET /api/v1/catalog/species` | Public; `trade_enabled` defaults false |
| List my drafts and other statuses | `GET /api/v1/listings/mine/` | Signed-in owner |
| Create private individual animal draft | `POST /api/v1/listings/` | Verified, pending/approved seller |
| Edit own private draft | `PATCH /api/v1/listings/{id}/` | Verified, pending/approved seller; DRAFT only |
| Add photo | `POST /api/v1/media/listing-photos/` | Signed-in seller, own DRAFT |
| List my uploaded files and review status | `GET /api/v1/media/mine/` | Signed-in owner |
| View private draft photo | `GET /api/v1/media/{id}/file/` | Owner or designated staff; public only if moderated and active |
| Remove draft photo from gallery | `DELETE /api/v1/media/{id}/` | Signed-in owner, DRAFT photo only |
| Submit | `POST /api/v1/listings/{id}/submit/` | Approved seller, trade-enabled species, pending/approved photo |
| Publish | Django staff review action | Authorized moderator, eligible seller/species and approved photo |

### Supported attributes and caveats

- Species-specific **guidance** varies by category, but the current form fields are limited to individual animal identity and general description. Rich health/orthopedic/vaccination records, breeding disclosures, regulatory documents, litter and livestock group quantities are separately specified, **not yet implemented**. Species trading is disabled until proper regional rules are approved.
- Public street addresses and private identity reports must never be included in listing text or published photographs.
- The UI identifies disabled categories and pending sellers. The API checks permissions again regardless of app state.
- There is no wallet, order, checkout, delivery claim, escrow, or phone-based public release yet.
- The mobile gallery can read authorized images but is not a CDN or large-scale image optimizer. R2 real-credential integration, retention/erasure, evidence scanning and iOS device acceptance remain pending.
- Owner-listed uploads are currently capped at 100 most recent files; the next media-metadata pagination task must remove that cap before scaling seller accounts.
- Draft photos are *soft-removed*, not instantly physically erased; do not use "permanently deleted" in the app.

## Verification and completion criteria

- Owner creates and edits draft from mobile without manual API calls; save handles server validation errors and network failures.
- Listing payload cannot set `seller` or `status`, and only DRAFT can change. No cross-owner access.
- Invalid prices cannot be saved; 0.01 NGN correctly maps to one minor unit; large amounts are bounded by backend.
- Seller and species permission transitions override stale mobile actions.
- Submission requires at least one uploaded photo; publishing requires an APPROVED photo.
- Gallery limit is eight active photos and removing one frees exactly one slot; reviewer and owner events stay auditable.
- Backend lint/migration/PostgreSQL tests, Flutter analyzer/widget tests, and Android debug build green on the PR commit. Actual device upload/HTTP staging and iOS Xcode checks are **still unverified** until separately performed.

**Do not call all M1 complete:** account recovery, health schema, approved species/legal rules, real R2, media lifecycle cleanup, real-device tests and KYC verification remain outstanding.
