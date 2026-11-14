# Anima — audited staff video moderation and Cloudflare visibility transitions

**Scope:** Backend and Django Admin moderation for the owner-approved video-first animal app. Production Cloudflare Stream integration and physical-device acceptance are still outstanding.

## Publication policy

- Every uploaded video starts **private** at Cloudflare (`requireSignedURLs=true`) and `pending` in Anima.
- A processing webhook cannot publish a video. A reviewer must sign into Django Admin with a verified TOTP session and the specific `social.review_videopost` permission, then inspect the actual private video in the Cloudflare dashboard. They must affirm both visual inspection and animal welfare/rights/policy review with a detailed reason.
- The reviewer must be different from the video creator. Only completed, eligible, active-creator, rights-attested videos may be approved, and only when `STREAM_PUBLICATION_ENABLED=true`. This gate defaults **off**.
- An approved decision is written to an append-only `VideoReviewEvent`. The video goes to `publishing` and remains absent from the feed until the provider confirms `requireSignedURLs=false`. An unsuccessful provider update leaves `visibility_sync_needed=true`; a reviewer can retry.
- Provider video detail modification is **POST /accounts/{account_id}/stream/{identifier}**, not PATCH. Response must confirm the requested visibility and identifier. See <https://developers.cloudflare.com/api/resources/stream/methods/edit/>.
- A takedown switches the Anima state to `removed` **before** attempting provider revocation. The public feed hides it immediately. Provider `requireSignedURLs=true` is required to block further direct playback by UID. If Cloudflare is unavailable, the audit log records the takedown and leaves `visibility_sync_needed=true`, but the original direct Cloudflare URL may temporarily remain accessible — **urgent provider escalation is mandatory**. Do not describe local feed removal as confirmed global revocation until provider sync succeeds.

## Operator procedure

1. Configure `STREAM_PUBLICATION_ENABLED=false` while provisioning credentials, staff MFA and retention/appeal support.
2. Ensure all creators' footage was originally uploaded with signed URLs required and the Cloudflare webhook secret configured.
3. Provision narrow `social.review_videopost` permission to vetted staff with confirmed TOTP only.
4. Open Django Admin → Video posts → Review / privacy sync. Inspect the actual clip privately in Cloudflare's own authenticated dashboard; the Anima Admin page deliberately does **not** expose a signed preview URL.
5. Record a reason of 20–800 characters and confirm both checks for approval. Reject clips that fail welfare, content, rights, commerce or regional policy checks.
6. If publication or takedown says synchronization is incomplete, investigate Cloudflare, select `retry_sync` on the affected record and verify the result. For takedown emergencies, directly revoke playback in Cloudflare before completing reconciliation.
7. Do not place any Cloudflare secret, private stream token or identifying personal information in the review reason or logs.

## Automated regression coverage

- Password-only Admin sessions denied, TOTP and permission required, self-review blocked.
- Visual/policy checks and processing required; rejected video cannot become public.
- Provider must explicitly confirm a successful **POST** with correct video UID and `requireSignedURLs` value.
- Provider failure leaves reviewed publishing records out of public feed; retry brings them online only after provider confirmation.
- Emergency takedown removes feed presence before external revocation and preserves a retry flag when Stream is down.
- Immutable decision audit history.

## Missing before public launch

- Actual paid Stream account, configured webhook secret, real device and provider end-to-end test.
- Production content-review policy, moderators trained in animal welfare/protected species law, copyright reporting, uploader identity/appeal handling, and on-call takedown.
- Automated periodic reconciliation and cost-control alerts, crash/exception telemetry and alerting.
- In-app user reporting and blocking, comments/follows, persistent messaging, compliant protected checkout, Android/iOS store acceptance.

**Do not enable video publishing for real users before those operational gates are satisfied.**
