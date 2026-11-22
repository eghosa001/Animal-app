# Per-conversation unread counts and verified read cursors

This milestone adds durable recipient-specific unread indicators to the existing private listing conversations. It does **not** claim WebSocket delivery, push alerts, background polling or guaranteed read receipts when offline.

## Privacy and read semantics

Each Conversation has two independent nullable cursor fields: buyer_last_read_message and seller_last_read_message. A user can advance only their own cursor using the UUID of a real ChatMessage belonging to that conversation. Both the conversation and message are checked against the authenticated user before modification. The database row is locked and cursors only advance by the message's server-issued (created_at, UUID) ordering; an older retransmitted request cannot roll the cursor backwards.

The inbox returns unread_count based only on the **other participant's** messages newer than the current user's cursor. Your own messages never increase your unread count. The message list GET and inbox GET do not automatically acknowledge anything. Sale, block or seller suspension can prevent new messages, but legitimate participants retain access to historical messages and their read cursors.

## API

- GET /api/v1/chats/conversations/ — adds unread_count to each participant-scoped conversation.
- POST /api/v1/chats/conversations/{uuid}/read/ — body: message_id (UUID), returns last_read_message. This endpoint is authenticated and separately rate-limited. A guessed, malformed, cross-conversation or unauthorized message fails without advancing the cursor.

The Flutter inbox displays unread count badges and refreshes them on return from a conversation or manual pull-to-refresh. The conversation screen sends an acknowledgement only after the newest fetched page has been placed into the widget tree and a frame callback runs. If the read request fails, no client-side optimistic clearing occurs; the next visit can retry.

## Checks and remaining work

Backend tests verify independent buyer/seller counters, self-sent messages excluded, no side effects from GET, monotonically increasing cursors, replay idempotency, participant isolation and cross-conversation UUID rejection. Flutter tests verify badge visibility and read API invocation after opening a thread.

Remaining for high-standard chat: authenticated WebSockets and reconnect replay, mobile foreground/background notification routing, unread counts in tab navigation, notification preferences, push token lifecycle, delivery/read receipt UI, scam-link protection, attachment review and user privacy controls. These are not implied by adding the unread-count field. Performance and query plans must be measured on large inboxes before scaling.
