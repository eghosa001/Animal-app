# Private animal-video upload ticket and signed processing webhook

**Scope: backend-only secure development slice; not an operational video publishing service.**
Source: PR #31, after video-first Home PR #29. No production Cloudflare account, paid video storage, signed provider webhook or creator mobile upload is configured.

## Why this exists

Public animal content must be vetted. Allowing users to upload directly into a public Stream UID would risk exposing unreviewed animal abuse, prohibited wildlife trading, spam, copyright-infringing footage or illegal ads. The initial feed intentionally remains empty unless reviewed content exists.

## API workflow

1. A logged-in, active, email-verified person requests `POST /api/v1/feed/videos/upload-ticket/` with a 4–400-character `caption`, `rights_attested: true`, `animal_topic_attested: true`, and optional *owned, approved, legally permitted* `listing_id`.
2. Backend limits the account to 4 ticket requests/hour and 8 records in a rolling 24 hours; permissions and quota are server-side. Staff bearer tokens are not accepted.
3. When explicitly enabled, the backend contacts Cloudflare Stream using its private server-only API token and requests a 15-minute, one-time direct upload URL limited to 60 seconds. Critically, `requireSignedURLs: true` keeps the clip private to anyone who learns the video UID.
4. Provider returns a trusted `https://upload.videodelivery.net/...` upload URL and UID. Backend validates URL host, persists a **pending** `VideoPost` and returns the URL to the client. Neither API token nor webhook secret reaches Flutter.
5. App can upload the binary directly to the one-time provider URL (mobile implementation next; multipart upload limit 200 MB). Django does not proxy large video files.
6. A Cloudflare processing webhook calls `POST /api/v1/feed/stream/webhook/`, with `Webhook-Signature: time=...,sig1=...`. Backend rejects stale, invalid or unsigned payloads, checks the Stream video UID and processing outcome, and records readiness or rejection.
7. **No webhook can publish content.** Human content-rights and safety approval is a separate future workflow. Publishing must atomically coordinate visibility and provider `requireSignedURLs` policies, with takedown and appeals; those are not implemented.

## Environment (disabled by default)

- `STREAM_UPLOADS_ENABLED=false` until provider setup and operator review.
- `STREAM_ACCOUNT_ID`: account ID, server-only (32 hex characters).
- `STREAM_API_TOKEN`: scoped Stream Write bearer token; server secret, never exposed in mobile configuration.
- `STREAM_WEBHOOK_SECRET`: hex signing secret from Stream webhook setup; do not confuse with API token.
- `VIDEO_DELIVERY_HOST`: approved Cloudflare Stream playback host, configured for the public feed separately.

Real webhook subscription needs an HTTPS URL reachable by Cloudflare; registration applies once per account. After provisioning, create or retrieve the webhook secret through the Cloudflare API and place it in secrets management. Do not enable this module on a public server without reviewing allowed content, consent, retention, rights, takedown, reporting and operational support.

## Current provider limits and costs

Cloudflare documents multipart direct creator upload URLs for up to 200 MB per video and recommends TUS for larger files. We deliberately cap clips at 60 seconds. Stream bills approximately **US$5 per 1,000 stored video minutes per month** plus **US$1 per 1,000 delivered minutes**; viewer preloading counts as billable delivery, so preloading must be restrained. Verify prices at procurement.

Official sources:
- https://developers.cloudflare.com/stream/uploading-videos/direct-creator-uploads/
- https://developers.cloudflare.com/stream/manage-video-library/using-webhooks/
- https://developers.cloudflare.com/stream/pricing/

## Remaining gates

- Flutter creator video picker/direct upload/queue, upload progress, network retries and accessibility.
- Staff MFA-gated video moderation, content evidence/rights checks, immutable audit, warning/report/takedown workflows, appeal, and playback signing policy transition.
- Real webhook registration, spoof/replay testing, private playback check and actual Android/iOS physical-device HLS tests.
- Provider cost budget and signed legal/welfare/content safety operational approval.

**Never claim that a successful ticket or processing webhook makes a video public.**
