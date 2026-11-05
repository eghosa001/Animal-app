# API, WebSockets, contracts and permission matrix
Version 0.1 — 2026-11-05.

## Transport and standards
- HTTPS REST JSON at /api/v1/; OpenAPI 3.1 generated from backend, typed Flutter client generated in CI.
- WSS under /ws/v1/; authenticated short-lived connection token, connection-level and message-level rate limits, heartbeats and reconnect.
- Offset/cursor pagination on large feeds and messages; ISO-8601 UTC timestamps; UUID object identifiers; ISO-4217 currencies.
- Error format: {code, message, details?, request_id}; no internal exception/PII leakage.
- Public/private endpoints explicitly documented; production OpenAPI strips sensitive staff endpoints.

## Representative routes
| Resource | Verb / path | Caller | Contract |
|---|---|---|---|
| signup | POST /auth/register | guest | creates unverified user |
| login | POST /auth/login | guest | secure token/session |
| me | GET/PATCH /users/me | current user | profile and privacy |
| delete request | POST /users/me/deletion-requests | current user | initiate deletion and export |
| seller enroll | POST /seller/verification | adult user | private documents via secure upload |
| species | GET /catalog/species | all | returns permitted browsing taxonomy |
| listings | GET /listings | all | searchable, indexed, approved |
| create listing | POST /listings | verified seller | draft only |
| publish | POST /listings/{id}/submit | owner | moderation queue |
| create upload | POST /media/upload-sessions | authenticated | scoped direct-upload ticket |
| feeds | GET /feed?cursor= | authenticated/public policy | safe ranked content |
| posts | POST /posts | authenticated | create draft |
| comments | POST /posts/{id}/comments | authenticated | abuse-limited |
| conversations | POST /conversations | authenticated | listing context, permissions |
| messages | GET /conversations/{id}/messages | participant | cursor pagination |
| offers | POST /offers | participant | signed exact amount/currency |
| accept offer | POST /offers/{id}/accept | seller | locks price snapshot |
| checkout | POST /orders/{id}/checkout | buyer | provider-approved; idempotency |
| order | GET /orders/{id} | buyer/seller/authorized staff | sanitized read |
| delivery proof | POST /orders/{id}/handover | authorized party | evidence + status |
| dispute | POST /orders/{id}/disputes | buyer/seller | time-bounded case |
| report | POST /reports | authenticated | safety triage |
| notifications | GET /notifications | current user | pagination and read cursor |

Admin endpoints under /admin-api/v1/ require staff permission + MFA + audited access.

## WebSocket envelope
Each event has id, type, version, server_timestamp, conversation_id, and payload. Event types: message.created, message.read, conversation.typing, offer.updated, order.updated, notification.created. Typing status is ephemeral; messages are stored before broadcast.
Client sends client_message_id so retries are idempotent. The server validates membership on every message; reconnect uses last received cursor and replays missing persisted messages. Do not send identity documents, payment tokens or full medical files in socket payloads.

## Role authorization
- Anonymous: view permitted public approved posts and listings (policy-dependent).
- User: own profile, own messages, report/block, post subject to moderation.
- Verified seller: own listing mutations, receive listing inquiries, view own orders.
- Buyer: pay own order, see own order and delivery status, open dispute.
- Moderator: designated moderation queues only, not payout approvals.
- Finance: authorized reconciliation and payout workflow, not unrestricted private chats.
- Superadmin: manage policies/roles with separate approval for high-risk actions.
Each object lookup must enforce ownership even if UUID guessed. Sensitive attachments use authorization checks and expiring signed URLs.

## Compatibility and quality gates
- Pin API major version /v1; publish changelog and deprecation window.
- Schema diff fails CI for unapproved breaking change.
- Contract tests cover permissions, paging, validation, error bodies, content-type and idempotency.
- Rate limit auth, comments, chat, uploads, search, and checkout separately with abuse reporting.
- CORS only for permitted web origins; CSRF for cookie web sessions; rotate JWT/refresh tokens if used and revoke on logout.
- Correlation ID in every response/log; mask user identifiers where exported.
