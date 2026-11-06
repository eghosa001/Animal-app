# Private animal-photo and seller-evidence upload runbook

**Implemented code:** Backend PR #14 and Flutter PR #15, 2026-11-06. **Deployment:** automated local/CI verification; R2 real-account integration, device/iOS acceptance and production privacy/legal signoff pending.

## Purpose and explicit boundaries

- Authenticated sellers upload JPEG or PNG animal listing photos to a DRAFT listing.
- Sellers who submitted an eligible application can upload private JPEG/PNG identity, business, or license **image evidence** only after acknowledging the private verification purpose.
- Images are validated, decoded and re-encoded to **new** JPEG bytes to remove user-supplied EXIF and unsafe trailing content. Images exceeding declared/actual byte or pixel limits are rejected.
- No identity evidence becomes a public attachment or a field on a listing response.
- Listing photos remain PRIVATE until authorized review, seller approval, permitted species and an ACTIVE listing. Public reads always re-check current rules, so seller suspension immediately blocks the image.
- Staff with seller-review permission may download seller evidence through the authenticated API; access is logged. Photo moderators have a separate permission.
- File paths are server-generated UUID keys. Original filenames, EXIF location, untrusted extensions and object storage credentials are never exposed to users.

**Supported files at this stage:** JPEG/PNG only; normalized to JPEG. Evidence PDF, animated GIF, HEIC and video are rejected. PDF support needs malware scanning, safe PDF handling and a new documented policy; do not bypass this control. The platform's public social videos will be implemented separately via a dedicated video pipeline.

## Upload endpoints

All paths are relative to the backend host; never send object-store credentials to a phone.

| Endpoint | Method | Caller | Purpose |
|---|---|---|---|
| `/api/v1/media/listing-photos/` | POST multipart | Verified seller, own DRAFT listing | `file` + `listing_id` |
| `/api/v1/media/seller-evidence/` | POST multipart | Verified applicant with pending/approved seller profile | `file` + `evidence_type` + `consent=true` |
| `/api/v1/media/mine/` | GET | Authenticated owner | List own asset IDs/metadata, **never** storage keys |
| `/api/v1/media/{asset_id}/file/` | GET | Owner, entitled staff, or public only if approved active listing photo | Private authenticated image streaming |
| `/api/v1/media/{asset_id}/review/` | POST JSON | Staff with `animal_media.review_mediaasset` | Approve/reject photo with a 20–500-character reason |

All uploads are subject to an initial per-user API throttle. For production, enforce rate limits with Redis/shared cache and API gateway limits, not a local process-only cache.

### Example: listing photo

```sh
curl --fail-with-body -X POST "http://127.0.0.1:8000/api/v1/media/listing-photos/" \
  -H "Authorization: Bearer <your-test-access-token>" \
  -F "listing_id=<own-draft-listing-uuid>" \
  -F "file=@animal.jpg;type=image/jpeg"
```

Response: UUID, kind=`listing_photo`, state=`pending`, dimensions, normalized MIME `image/jpeg`, relative `file_url` and upload time. It contains no storage key. A moderator approves via the Media Admin review page or staff API, but the image remains unavailable publicly until the actual listing is active, seller approved and species permitted.

### Example: private seller evidence

```sh
curl --fail-with-body -X POST "http://127.0.0.1:8000/api/v1/media/seller-evidence/" \
  -H "Authorization: Bearer <test-applicant-token>" \
  -F "evidence_type=business" \
  -F "consent=true" \
  -F "file=@redacted-business-certificate.jpg;type=image/jpeg"
```

Evidence is **not** deemed legally valid or independently identity-verified merely because it was uploaded. Seller reviewer must explicitly inspect the case, document basis, record review, and follow legal retention policy. The Seller Admin review screen now lists the applicant's private evidence files through authenticated and audited backend URLs.

## Upload rules and media policy

| Rule | Current limit / behaviour |
|---|---|
| Listing photo format | Decoded JPEG or PNG; saved as clean JPEG |
| Evidence format | JPEG or PNG images only |
| Listing photo input bytes | 8 MiB max |
| Seller evidence input bytes | 5 MiB max |
| Image dimensions | Up to 18 megapixels input; output maximum dimension 2400px |
| Photos per listing | 8 |
| Evidence images per seller | 8 |
| Moderation | Pending by default; approved/rejected by explicit staff action and reason |
| Public evidence availability | Never |
| Stored original filenames | Never |
| Public signed R2 GET/PUT | Not used in this first secure implementation |

An expired/rejected listing, disabled species or suspended seller must not keep photos publicly accessible. Stored verified evidence should follow client-approved data retention, legal hold and erasure processes before production. This first slice does not implement the final retention job or malware scanning for PDF documents.

## Local development

No paid account is necessary. With `DJANGO_DEBUG=true`, `MEDIA_STORAGE_BACKEND=local`, and a writable `PRIVATE_MEDIA_ROOT`, the service stores normalized bytes under `.anima-private-media/` with randomized server keys and restrictive file permissions. Directory is ignored by git. Never store real seller identification images on a publicly accessible development machine or commit them to GitHub.

Run `python manage.py migrate`, then backend tests via `pytest`. Staff permissions are granted via Django Admin or documented role-management process:
- Seller reviewer: `accounts.review_sellerprofile`.
- Photo moderator: `animal_media.review_mediaasset`.

## Cloudflare R2 production setup (manual/client-owned)

**Do not activate any paid integration until client approves the service and billing.**

1. In a new client-owned Cloudflare account with MFA, navigate to R2.
2. Create **two private** R2 buckets: e.g. `anima-photos-prod` and `anima-evidence-prod`. Do not enable `r2.dev` public access or custom public domains for these buckets. Use separate stage buckets.
3. Create an R2 API token scoped to the two private buckets with minimum object permissions for put/get/delete. Never use root account keys or expose token to Flutter.
4. Store these values only as **secret environment variables** or in cloud secret manager:
   - `MEDIA_STORAGE_BACKEND=r2`
   - `R2_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com`
   - `R2_ACCESS_KEY_ID=<secret>`
   - `R2_SECRET_ACCESS_KEY=<secret>`
   - `R2_BUCKET_PHOTOS=anima-photos-prod`
   - `R2_BUCKET_EVIDENCE=anima-evidence-prod`
5. Put the backend behind HTTPS, restrict file/request body size at the reverse proxy to a little above 8 MiB multipart, add monitoring and rate limits, and verify process memory budget.
6. Run real R2 staging tests: upload/normalize/read owner access, authorized reviewer access, buyer denial, seller suspension, no public bucket link, credential rotation, failed upload recovery, cost monitoring and offsite backup before production.
7. Define an evidence retention/deletion schedule with a qualified data protection reviewer and add automatic cleanup + orphan-object reconciliation before accepting real identity records.

This API does not use client-side R2 presigned URLs, so **R2 browser CORS rules are unnecessary** for current Android/iOS uploads. The tradeoff is backend proxy bandwidth, bounded here by 5–8 MiB and strict quotas. At larger scale, direct-to-R2 presigned quarantine uploads may be considered only with a server-side sanitize/promotion process: R2 presigned PUT URLs are bearer credentials and can be reused until expiry, so signed `Content-Type` alone does not validate content or prove moderation.

Official docs:
- Cloudflare R2 private S3 API / temporary links: https://developers.cloudflare.com/r2/api/s3/presigned-urls/
- Cloudflare R2 pricing: https://developers.cloudflare.com/r2/pricing/
- Django upload security: https://docs.djangoproject.com/en/5.2/topics/security/
- OWASP upload protection: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html

## Test evidence and release blockers

PR #14 CI runs PostgreSQL tests for decoding and metadata removal, fake MIME, size limits, cross-seller rejection, seller evidence/private reviewer separation, per-object audit, moderator approval and public-status rechecks, local-storage production fail-closed and mock R2 bucket routing. This verifies code behaviours **without** asserting real R2 integration. See the PR and CI log for precise test counts.

**Not finished for production:** real R2 staging credentials; virus scanning and secure PDF support; per-country data processing legal approval; retention/erasure automation and evidence consent text; media deletion/replacement; Flutter creation/editing of new listing drafts, full photo gallery management, and end-to-end Android/iOS device testing; CDN-ready public image derivative strategy. These must be completed in separate, verified tasks before declaring M1 complete.

## Verified mobile integration (PR #15)

The Flutter **Profile → Upload animal photos or verification** screen supports choosing JPEG/PNG images from the gallery, specifying an existing draft listing or private evidence type, confirming consent for verification images, uploading via authenticated multipart HTTP, and refreshing moderation status. Marketplace listings use approved-only photo paths from the backend and show an image thumbnail if available. The widget tests and Android debug APK build passed in [CI run 42205721985](https://github.com/eghosa001/Animal-app/actions/runs/42205721985).

The old artifact display name `anima-m0-debug-apk` is inherited from the existing workflow; the referenced CI run includes the M1 seller upload interface. The artifact is a **development APK**, not a production-ready signed release.

**Important prerequisites for real end-to-end testing:** a running local/staging API, an email-verified seller who has submitted an application, and an existing draft listing for animal photos. The app does not create draft listings yet; that is the next separately testable M1 task. Identity-image uploads can be started from the applicant's profile without a draft. On real Android use a test API reachable by the phone (USB `adb reverse` for local) or HTTPS staging. macOS/Xcode iOS testing and actual Cloudflare R2 integration have not been performed.
