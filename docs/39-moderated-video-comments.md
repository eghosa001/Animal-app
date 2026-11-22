# Animal-video comments: manual review, private submissions and rollback

Video comments are a controlled social feature, not a free-for-all public text wall. A logged-in, email-verified active account may submit up to 500 characters against an approved, processed, moderated video. The API validates ownership and blocks in both directions and throttles creation. User-supplied UUID nonces make retries idempotent across devices; conflicting reuse fails closed.

- GET /api/v1/feed/videos/{video_id}/comments/ is paginated, guest readable and returns **approved only** (authors are active and not blocked by the viewer).
- POST to the same URL accepts `{"body":"...","client_nonce":"UUIDv4"}` and returns a private ID and `pending` status. **Submission is never publication.** A future review may reject it without exposing the text.
- DELETE /api/v1/feed/videos/{video_id}/comments/{comment_id}/ allows the author to withdraw their own pending or published comment. No other account can delete it.
- Staff may approve, reject or remove from a dedicated Django Admin review page. MFA and `social.review_videocomment` permission are mandatory. Every moderator decision is audited with before/after state and reason; direct Admin edit/delete is prohibited.
- Anonymous users cannot write; inactive or unverified users are denied; blocked relationships, removed videos and unreviewed videos do not expose or accept comment text.
- A public feed aggregate is calculated from approved comments by active authors. Combining likes with comment counts must use distinct aggregation to avoid a SQL join fanout.
- Comment text must be rendered as plain text (no rich HTML interpretation), and the mobile editor must clearly say comments require review.
- Approved individual comments can be reported directly by ID via `POST /api/v1/safety/reports/` with `target_type=comment`. Such reports use the existing private, MFA-only safety case queue. Pending, removed, blocked or hidden comment IDs cannot be reported through public discovery. Appeals/retention automation and moderation staffing remain release gates.

## Rollout and rollback

1. Run Django migrations and existing backend regression suite in PostgreSQL, then validate comment API and admin OTP tests. Run Flutter analysis/widget suite and Android build after mobile wiring.
2. Do not enable public production video delivery until moderation operations are staffed and abuse/reporting acceptance is complete. New comment submissions are pending by default.
3. To pause use, restrict API routes or video delivery; never bulk-approve pending comments. Preserve comment and review records under the approved data-retention policy.
4. No new payment, Cloudflare Stream credentials, or provider costs are introduced.
