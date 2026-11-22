# Foreground real-time chat updates (WebSockets)

The app's private chat UI is still backed by the existing durable REST message API. WebSockets only signal that a committed message is available: the event includes a conversation UUID, message UUID and server timestamp, **never the private message body**. The client reloads and acknowledges messages through the established participant-only REST routes.

## Authentication and abuse boundaries

The authenticated POST /api/v1/chats/conversations/{uuid}/socket-ticket/ issues a conversation-scoped signed connection ticket with a 45-second establishment lifetime. Ticket requests are rate-limited, must come from verified active consumer accounts and require membership in that conversation. The ticket contains no bearer JWT, password hash, private email address or media. It is transmitted only through the WebSocket subprotocol list, not in the URL or query string; the server selects only the public protocol name anima.chat.v1 in its response.

The server rejects missing, invalid, mismatched, expired or tampered tickets. It reevaluates user activation, staff restrictions, membership and password-rotation revocation before each event. Each open socket is capped to 14 minutes, then the mobile client obtains a new short-lived ticket. The mobile client never sends chat bodies over this unthrottled connection; only a minimal ping/pong frame is supported. API writes continue using the existing authenticated, rate-limited, idempotent REST endpoint. An event is emitted only after transaction commit and only for a newly-created message; duplicating a client nonce never creates or broadcasts a second message.

Socket group names are derived only from server-validated conversation UUIDs. Only buyer and seller may join. On a Redis interruption or socket drop, REST messaging continues functioning and app reconnects with bounded exponential backoff. Event delivery is best effort: clients must refresh the authoritative REST history after reconnect.

## Environment

Development without REDIS_URL uses an in-memory Channels layer for single-process tests only. Production, already requiring REDIS_URL for shared API throttles, uses the official channels_redis backend across API/ASGI workers. ASGI must be served by Uvicorn/Daphne and WebSocket upgrades must be supported by the reverse proxy. Production WSS is required. This implementation is designed for Android/iOS native Flutter and uses dart:io WebSocket; web browser support would require a platform-specific client adapter.

WebSocket endpoint: /ws/v1/chats/conversations/{uuid}/, subprotocols [anima.chat.v1, anima.ticket.<signed-short-lived-ticket>].
Event: {type: message.created, conversation_id, message_id, server_timestamp}.

## Release gates and limitations

Backend tests cover ticket access, scope, tampering, session rotation, unverified and staff denial, actual WebSocket group receipt, minimal payload and idempotent post-commit fanout. Flutter tests still exercise REST chat, null-socket fallback, and client reconnect lifecycle. Device acceptance must establish real WSS behavior across Android/iOS, background/foreground, network handoff, sleeping devices and reverse-proxy timeouts before public use.

No background notifications, delivery guarantees, online status, typing indicators, message attachments or end-to-end encryption are delivered by this work. Push notifications require a separate opt-in/device-token retention and platform-permission workflow.
