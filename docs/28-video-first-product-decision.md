# Owner product decision: video-first Home (2026-11-10)

**Decision:** The mobile app opens directly into a short-form, portrait, vertically swiped animal video feed. This is the product's entry point, not a secondary social tab. It is a TikTok-style *interaction pattern*, not a copy of another product's artwork, name, trademarks or proprietary recommendation system.

## Approved information architecture

1. **Home:** immersive For You video feed for guests and registered users. The first session lands here automatically.
2. **Market:** browse/search approved animal listings; video-linked products open a specific, permission-checked listing detail.
3. **Create:** social uploads for eligible creators and verified sellers' approved animal-listing workflows. Video upload remains gated until processing/moderation is implemented.
4. **Chats:** contextual seller/buyer messages and structured offers once M2 is operational.
5. **Profile:** account/security, seller dashboard and creator content.

Content is for animals **in general**, including lawful pets, farm animals, birds, fish, rescue, welfare, care and education. Posting useful animal content need not imply an animal is for sale. Commerce must remain independent of posting and forbidden categories must never become sellable through a video CTA.

## Player behavior and performance gates

- Native HLS player in Flutter using the maintained `video_player` package; portrait full-bleed content, vertical PageView, creator/caption overlay, optional **View animal** action.
- Autoplay only the visible clip; pause/dispose player when swiped away, app backgrounds or user changes primary tab. Pause/play and sound controls must work without implying fake likes/comments.
- Handle loading, buffering, failed CDN playback, empty moderation queue, no network and pagination. Avoid auto-loading several video streams on mobile data. Real device audits must evaluate data-saver / reduced-motion and accessibility settings before launch.
- The on-video animal CTA is displayed only if its linked listing remains active, the seller remains approved and the species' commerce policy remains enabled. Opening it performs a fresh backend authorization check.
- Feed is read-only in this slice. **No demo footage masquerades as posted user content.** Not-yet-implemented likes, comments, following, upload, report, block and share are not claimed to work.

## Backend contract (first vertical slice)

`GET /api/v1/feed/videos/?page=1` returns paginated public `VideoPost` entries:
`id`, `creator_name`, `caption`, `playback_url`, `poster_url`, nullable `listing`, `created_at`.

The database tracks video processing and human moderation independently. The public endpoint only includes active creators, processed videos, explicitly approved records with reviewer and timestamp, and a configured trusted delivery hostname. Never expose the full Stream API token to mobile. Only HTTPS Cloudflare Stream domains are accepted. No user-accessible video write route or staff override is opened until a signed provider callback, direct upload quotas, source ownership checks, takedown, copyright and moderation workflow exists.

Stream HLS URL contract: https://developers.cloudflare.com/stream/viewing-videos/using-own-player/
Flutter player: https://pub.dev/packages/video_player

## Status and acceptance

**Source delivered in this development PR:** video-first shell; reviewed feed read API and model/migration; player; paginated client; listing deep link; deterministic test fixtures. **Not delivered yet:** live Stream account/video ingestion, creator uploader, provider webhook verification, feed moderation UI, likes, following, comments, reporting, recommendation ranking, personalization, push, messaging/commerce and public launch.

**Acceptance still required:** PostgreSQL & Flutter CI, Android build, macOS/Xcode iOS build, actual HLS playback on Android and iOS, adaptive playback on poor connections, screen reader, battery and memory checks, legal welfare/community moderation, and cost alerts before public release.

Do not assume Cloudflare Stream can be used at no cost; pricing and retention/encoding choices require owner approval.
