# Listing-linked private chat — M2 implementation and remaining controls

The Anima animal platform's **video-first Home** is unchanged. Buyers can open an approved animal from the feed or marketplace, tap **Message seller**, and enter a persistent conversation. The Chats tab shows only conversations in which the signed-in account is the buyer or seller.

## Backend contract

- `GET /api/v1/chats/conversations/`: authenticated and paginated buyer/seller inbox.
- `POST /api/v1/chats/conversations/`: creates or reuses the unique thread for `listing_id`, for an active email-verified buyer and an active approved seller with a permitted, active animal listing. Seller cannot create a buyer conversation with themselves. Repeat starts return the same ID.
- `GET /api/v1/chats/conversations/{uuid}/messages/`: paginated newest-first message history, restricted to the two participants. Old history remains readable when an animal is sold or removed.
- `POST /api/v1/chats/conversations/{uuid}/messages/`: text-only `body` (1–2000 chars) and client-generated UUID `client_nonce`. Participants only; no new messages after a listing is sold, species becomes unpermitted or seller is suspended. Retries with the same nonce return the same stored message; a different body with the same nonce is rejected.
- Separate POST throttles restrict starting threads and sending messages. All sensitive message content is excluded from generic Django Admin. No payment credentials, verification documents, attachments or delivery guarantees are exposed.

The Flutter client stores authentication tokens in Flutter Secure Storage, generates RFC4122 v4 nonces from `Random.secure()`, preserves the nonce when repeating a pending message, and uses HTTP refresh (not an imaginary WebSocket implementation). API calls refresh access tokens under the existing rotation policy. The chat screen displays a clear warning: **off-platform payments/deals are not protected by Anima**, and no escrow functionality is currently enabled.

## Explicitly not delivered

- Real-time WebSockets, typing/presence, read receipts, notifications, attachments and media sharing.
- In-chat offer/negotiation records, payment processing, delivery states, refunds or escrow.
- Report/block/mute actions and operational message moderation. Those are mandatory UGC/abuse-safety gates before unrestricted rollout.
- Production server deployment, actual Android/iOS device acceptance and end-to-end identity/network testing.

## Verification

Automated API tests cover participant isolation, unauthorized/stranger access, self-contact rejection, disabled species, seller suspension, idempotent sends, two-way chat, after-sale read-only history and DB-level distinct-participant constraint. Flutter tests cover the inbox, text composer, signed-out call to action, listing-to-chat navigation and cryptographically generated UUID shape.

**Production recommendation:** ship only to controlled QA accounts until report/block/mute, content-safety operations and device testing are completed; do not advertise protection for off-platform transactions.
