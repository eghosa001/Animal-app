# UX specifications and visual quality system
Version 0.1 — 2026-11-05. Brand direction is pending client approval. This defines interactions, not final visual assets.

## Design goals
Feel like a first-class mobile product, not a classifieds page inside a webview. Fast discovery, clear buyer protection, accessible controls, and species-aware listing presentation. One unified Flutter app for enthusiasts, buyers and sellers. Avoid giant admin-style forms on mobile.

## Navigation and page families
Five primary tabs: Home (video-first), Marketplace, Create, Chats, Profile. **Owner decision 2026-11-10:** cold launch opens directly into the vertically swipeable short-video feed, with no text-first splash/home page; see [video-first ADR](28-video-first-product-decision.md). A seller hub exists under Profile and via contextual sale CTAs. Home: For You, Following, safe recommendations. Marketplace: category chips, text search, filter bottom sheet, recent/saved searches. Create: choose social post or approved animal listing (seller eligibility checked). Chats: buyer/seller conversations with listing context and offer states. Profile: content, favourites, orders, verification and settings.

## Screen-by-screen functional states
### Onboarding
- Welcome -> sign up/login -> verified email/phone -> pick animal interests -> privacy notice -> Home.
- Guest browsing may be allowed for approved public listings/content; buying/selling and messaging require authenticated user.
- Age/legal eligibility checked before commerce.
### Feed
- Full-screen portrait video or photo card with visible creator, species/topic tag and optional listing link.
- Gestures: swipe to next, pause/mute, report, comment, save, share, follow. No hidden payment interactions on scroll.
- Skeleton, buffering, no-connection retry, removed-content, block, upload-under-review states.
- Video can be paused; obey reduced-motion preference; next-item preload budget controlled.
### Marketplace
- Listing card: truthful photograph, animal type/breed when known, region, age, price, availability and verification status; badge never promises health.
- Listing detail: gallery, characteristics, provenance of medical records, seller reviews and credibility, care/transport constraints, clear message/offer CTAs.
- Filter by permitted species, location, price, age, verified seller and available status; filters persisted.
- For sold/restricted entries, disable checkout and explain why.
### Seller profile and listings
- Trust tiers show what was verified, when and by whom; avoid visually indistinguishable claimed vs independently validated documents.
- Create listing wizard: basic animal -> health/species fields -> media -> price/location -> preview -> submit for moderation; autosave drafts.
- Seller dashboard: inquiries, order states, payout status, disputes, notifications and earnings. Distinguish pending from available income.
### Messaging and offers
- Sticky listing context card, timestamps and delivery/read state, attachment preview, typing indicator.
- Offer CTA opens exact price/currency, expiry and terms. Seller may accept/decline/counter.
- Off-platform warning appears contextually near potential payment-detail exchange, with report action and concise legal disclaimer.
### Checkout and protected handover
- Summary of individual animal, seller, total, commission/fees and who pays transport. Display actual approved payment provider, hold/custody terms and refund window before consent.
- A paid order shows provider-verified status, not optimistic “success” on redirect. Never display protected funds as being held by us unless legally true.
- Delivery timeline: scheduled -> transport/pickup -> handover evidence -> inspect -> confirm OR dispute; visible support and deadlines.
### Reporting/disputes
- One-tap report from post/listing/message/profile with context-aware categories.
- Evidence upload and timeline with status, privacy assurance, right to appeal and urgent welfare pathway.
### Settings
- Sessions/devices, notifications, languages, blocklist, privacy, export/delete account, terms, help, support.

## Component primitives
Button (primary/secondary/destructive/disabled/loading), input (help/errors), accessible cards, chips, modal sheet, banners, video player, media picker/progress, avatar verified status, listing gallery, trust source tags, price/fee breakdown, status timeline, upload progress, chat composer, report sheet, skeleton/empty/error/offline patterns.
Maintain design tokens for colours, typography, radius, spacing, elevation, semantic states and motion; avoid hard-coded inconsistency. Support light and dark modes; avoid confusing green “verified” with green “paid”.

## Device and accessibility matrix
- Android midrange phones (including Samsung S25 FE), low-memory Android, small screens, Android TalkBack.
- iPhone with notch/safe areas, dynamic type, iOS VoiceOver, keyboard and photo permissions.
- 44+ point touch targets on iOS and equivalent Android guidance, clear focus rings, sufficient contrast, captions for informational videos, alternative text where practical, large text without clipping.
- Slow 3G/unstable connection: retries, upload resume, cached thumbnails, no auto-play when user requests data saving.
- Feature tests with right-to-left/localization readiness and Nigeria-friendly date/currency formatting; avoid assuming single currency in schema.

## Professional design QA
Every key screen requires: Figma/Penpot source, states for loading/empty/failed/offline/restricted, Android/iOS sample, accessibility review, screenshot regression, and feedback from representative buyers/sellers. Build a reusable UI kit before duplicating screens.
