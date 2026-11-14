# User blocking and reporting — safety controls

Scope: Anima's video-first animal platform, with approved animal listings and private buyer–seller messages. This milestone implements user-initiated blocking and report intake; operational escalation, appeals, automated abuse screening and law-enforcement processes remain additional launch gates.

## User controls

- **Block account:** only an authenticated person may add/remove their own block. Once one participant blocks another, neither can send new messages or open a new conversation through the supported listing API. Historical messages remain readable privately for evidence and dispute records. Approved videos and active animal listings from a blocked account disappear from the signed-in user's public API feed and marketplace; the blocked seller's own private listing workspace remains available.
- **Report:** an active, email-verified account can report an approved video, accessible animal listing, a private message only when already a conversation participant, or another active account. Reporter chooses scam, harassment, welfare, prohibited animal trade, copyright or other. A minimum 20-character contextual explanation is required. Reports are private to their submitter and authorized staff; public receipts omit report detail, affected account contact information and private content.
- **Reporting does not auto-remove media, suspend sellers, cancel orders, transfer money or establish liability.** Staff must inspect evidence and carry out the separate, correctly authorized enforcement action.
- **Your blocked accounts:** available from the signed-in Profile; the user may review their own blocklist and explicitly unblock accounts. There is no administrator browsing page for individual block lists.

## APIs

POST/GET /api/v1/safety/blocks/, DELETE /api/v1/safety/blocks/{uuid}/, POST/GET /api/v1/safety/reports/.

The backend enforces owner/participant restrictions and client-side validation is solely a convenience. Repeated blocks are idempotent. Unique (blocker, blocked) and no-self-block database constraints apply. Reports are limited to exactly one target by a database check constraint. Separate Redis-backed API throttles are required in production.

The private staff review flow is in Django Admin with staff session MFA plus the safety.review_safetyreport permission. Decisions are append-only, require a documented 20–800-character reason and cannot overwrite terminal decisions without a separate appeal process. Other admin roles cannot browse user blocks.

## Test matrix

Backend automated tests cover unauthenticated denial, owner-scoped block/unblock, no self-block, two-way chat prevention, blocked video and listing removal for signed-in users, continued private listing management, all report types, cross-user chat message isolation, hidden video and self-report rejection, database constraints, staff MFA and review permissions.

Flutter tests cover report explanation validation, success/error UI, block confirmation/cancel, and unblocking with confirmation.

## Remaining before unrestricted launch

- Escalation operations for urgent animal welfare and illegal wildlife cases; on-call response with measurable service levels.
- Staff evidence access controls, retention, appeals, audit export and disclosure handling, anti-impersonation and account abuse risk signals.
- Real notification delivery, automated link/payment-scam detection in messages, ban evasion prevention and community policy/copyright enforcement.
- Real physical-device Android/iOS acceptance, live Cloudflare account, Play/App Store compliance and supported complaints email/contact details.
- A regulated protected checkout provider; no live escrow is currently available. Off-platform arrangements are not protected.

Do not confuse a successful API request or a test fixture with a production-ready content safety program.
