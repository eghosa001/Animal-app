# Creator video workflow — development acceptance and operator gate

Updated 2026-11-10. The owner confirmed a video-first animal app. See [decision](28-video-first-product-decision.md).

The **Create** tab must offer two options without changing the established seller workflow: **Post an animal video** for social creation, and **List or manage an animal** for seller drafts. They are separate entities: a video need not advertise an animal for sale, and a video must not bypass the catalog's default-deny trade policy.

## Mobile video authoring

- Client reads `GET /api/v1/feed/videos/upload-capabilities/` before allowing selection. The operator flag defaults to false; the UI states why posting is unavailable instead of starting an impossible upload.
- When enabled, creator chooses MP4/MOV from device gallery, up to 200MB, with 60-second server-side maximum. Minimum 4-character, maximum 400-character caption. Creator explicitly attests that they own/have rights to the footage and that it is animal-related.
- Client requests an authenticated private upload ticket, validates HTTPS destination is exactly `upload.videodelivery.net` (never a lookalike hostname), then posts multipart bytes **directly** to Cloudflare Stream with **no Anima bearer token**.
- On upload success, app says *transferred, still awaiting processing and human moderation*. It never claims that a video was published. Users can fetch their private statuses from `GET /api/v1/feed/videos/mine/`; other creators' draft videos are not exposed.
- Failed transfer leaves the user informed that provider processing may still be underway; avoid duplicate submissions and publishing promises. Upload progress percentages are not shown until byte-level streaming is implemented.
- A live Cloudflare account, provider webhook, staff media moderation and public/signed playback transition are not configured by this PR. Any video on pending status remains private.

## Verification

Backend negative tests assert unauthenticated status denial, private owner-only list, provider UID absence and honest feature flag. Flutter widget/API tests assert two creation paths, disabled UI, malformed status and blocked forged provider upload URLs.

Remaining acceptance gates: real Android/iOS gallery upload with permissions, weak-network stress/abort and retry, signed URL lifecycle and public feed integration after a human moderation decision, content takedown, copyright dispute, abuse reporting, and video billing alerts. Production access remains disabled by default.
