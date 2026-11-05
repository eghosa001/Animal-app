# Social feed, animal content, media safety and moderation
Version 0.1 — 2026-11-05.

## Content model
The app is **animal-topic only**, not dog-only or only sale videos. Allowed examples: lawful pets, livestock care, rescue stories, fishkeeping, wildlife education, vet education, grooming and training, animal humour. Publishing does not require animal ownership. Prohibit unrelated general videos, harassment, violent animal abuse promotion, scams, sexual content, trafficking in protected species, illegal wildlife sales, unsafe instruction encouraging harm, fake breeder ads and misleading medical guarantees. Legitimate documentary evidence of abuse for reporting is reviewed contextually, not treated as promotional content.

Post types: photo album, short video, text with relevant image/context, share/repost (with rights). Video may link to a separately approved active listing; a post does not bypass species trade restrictions.

## Upload pipeline
1. Authenticate, rate-limit and issue single-use scoped, expiring upload ticket; cap duration, size, mime and number of parallel uploads.
2. Client uploads directly to provider with resumable support; never proxy large files through Django.
3. Provider notifies authenticated webhook; verify event; store metadata and processing status.
4. Generate thumbnails/poster, adaptive playback; strip location metadata, validate rights and sound/footage ownership disclosures.
5. Run automated screening when feasible (animal-topic classifiers, policy checks, duplicate perceptual hashes, spam) followed by human review for ambiguous/high-risk cases.
6. Publish only when processing complete AND policy approved. Removed content invalidates public playback authorization and feed/search indexes.
7. Expiring signed playback for private or sensitive assets; public playback only for approved content.
Cloudflare Stream pricing and direct-upload docs: https://developers.cloudflare.com/stream/pricing/ and https://developers.cloudflare.com/stream/uploading-videos/direct-creator-uploads/.

## Feed recommendation V1
Candidate sources: followed authors, recent high-quality animal posts, topic interest, local relevance where disclosed, under-exposed creators. Ranking: weighted interest match + watch-completion + meaningful engagement + freshness - reports/spam - repeated exposure. Hard-filter banned or under-review assets and blocked creators. Capture deliberate event definitions; do not optimize solely for addictive watch time. Allow feed “Following” and sensible reset of interests.

## Engagement
Follow, like, comment, reply, save, share, report, block, mute and privacy settings. Limit comments/mentions and detect link spam, scam phrases, impersonation, excessive outbound referrals, harassment. A block prevents messaging, follows, mentions and content discovery subject to policy. Report route accessible on every post/listing/message/profile. Users can appeal removals.

## Moderation operations
Case has severity, target, reporter, evidence, automated signals, reviewer assignment, action, time, rationale, appeals. Prioritize immediate harm, illegal wildlife commerce, threats, doxxing and payment scams. Distinguish informational animal welfare footage from content glorifying abuse. Protected species taxonomy updated by legal/compliance owners, never inferred from model confidence alone. Review identity/health documents with strict need-to-know permissions and audit.

Human-in-loop tools: Django Admin first; queues for false-positives, reviewer notes, appeals and repeat offenders. For third-party automated moderation, evaluate consent, cost and privacy. Do not blindly block all videos containing injuries that might document a rescue/veterinary procedure.

## UGC store requirements and evidence
App needs published community standards, in-app reporting, block/mute mechanisms, objectionable-content handling, accessible contact/support, moderation response procedures and review test account. Confirm current requirements:
- https://developer.apple.com/app-store/review/guidelines/
- https://support.google.com/googleplay/android-developer/answer/9876937
Moderation is an ongoing operational cost; not solved entirely by automation.

## Media/cost protection
Target pilot video <=60 seconds, max resolution/duration subject to product decision; hard size limits; signed upload initiation; limit abusive accounts; avoid auto-downloading every feed item; preload next video only and cancel unused segments. Stream charges delivered minutes including preload; alert at 25/50/80/100% monthly budget.
Retention and data export/deletion for posts, originals, reports and evidence must be documented by category.
