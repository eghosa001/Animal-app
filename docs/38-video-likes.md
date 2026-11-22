# Moderated animal video likes

Authenticated, email-verified animal-platform users can like and unlike approved, processed videos from the vertical Home feed. Likes are not available for drafts, pending review, rejected or removed media, inactive creators, blocked accounts, or when the trusted Stream delivery host is unconfigured.

## API and privacy

- GET /api/v1/feed/videos/: safe public aggregate likes_count and the authenticated viewer's own is_liked boolean. Anonymous viewers see the count but no user-specific details.
- PUT /api/v1/feed/videos/{uuid}/like/: like this video idempotently.
- DELETE /api/v1/feed/videos/{uuid}/like/: remove your like idempotently.
- Only counts and the caller's boolean leave the server. No API to enumerate individual likers, emails, follower graphs, or personal reaction history.
- A PostgreSQL unique constraint (video, user) prevents duplicate likes across simultaneous devices; a separate scoped throttle protects write endpoints. Counts exclude reactions from inactive user accounts.
- Feed queries annotate aggregate counts and own liked state efficiently; hidden videos remain inaccessible using the same approved-media and blocking requirements as the feed.

## Flutter

A heart button with accessible Like video / Unlike video labels appears within the vertical full-screen Home video rail. The button waits for server confirmation and then updates the authoritative count and the cached feed post state. Network errors, expired login, or refused actions do not change the local count or visual heart state. Errors appear as a Snackbar rather than a false success.

## Validation and release

Backend tests: guest/nonverified denial, idempotent repeated likes, multi-user count, unlike twice, muted reaction after blocked seller, disabled Stream domain, removed/unprocessed/unmoderated video rejection, unknown UUID and inactive creator, inactive liker excluded.

Flutter tests: parsing, immutable model copy, successful like/unlike and failed-request UI invariants.

Not included: comments, follows, recommendations, creator analytics, re-shares, live pushes, account deletion, real Cloudflare Stream staging, iOS physical-device acceptance or approved financial custody. The app is still a development build and public availability must remain gated by moderation and infrastructure readiness.
