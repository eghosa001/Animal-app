# Account creation and client self-service checklist
2026-11-05. **No accounts listed here are claimed to have been connected or configured.** The client/business should own billing and legal registrations. Invite developers using roles, never share passwords, OTPs or secret keys through chat/GitHub issues.

## Set up now (free unless marked otherwise)
- [ ] **GitHub:** Visit https://github.com/eghosa001/Animal-app, consider Private visibility. Set maintainers, require MFA, enable Issues/Projects and Dependabot. If business will own repository, agree legal transfer path.
- [ ] **Business identity:** Determine entity/name, verified business email, phone, registered address, business banking and seller agreement owner; do not publish sensitive details.
- [ ] **Design:** Create Figma Starter or Penpot workspace; share editor invitations. Save brand choice, logo drafts and user-flow decisions.
- [ ] **Cloudflare account:** https://dash.cloudflare.com/; enable MFA. R2 subscription may require a billing method; use a DEV bucket only and small quotas. Do not buy Stream capacity until test video work is ready.
- [ ] **Firebase:** https://console.firebase.google.com/ create separate development project. Later register Android package and iOS bundle IDs, configure Cloud Messaging/Crashlytics. Assign developer access.
- [ ] **PostHog (optional):** https://posthog.com/ create a project, configure retention and PII suppression, billing limits.
- [ ] **Monitoring:** select Sentry free or PostHog error tracking, not two overlapping systems by default.
- [ ] **Google Play Console:** https://play.google.com/console/ ; $25 one-time when registration is ready; use correct business/developer account. Note personal-account 12-testers/14-days requirement if applicable.
- [ ] **Apple Developer Program:** https://developer.apple.com/programs/enroll/ ; $99/year when TestFlight/App Store distribution planned; organization enrollment and identity checks can add lead time.
- [ ] **Domain:** evaluate brand/trademark, obtain registrar quote, establish support@ and privacy/legal URLs before public launch.

## Later: stage hosting choices
Choose **one**:
- [ ] Railway: https://railway.com/pricing — easier staging/managed deployment; Hobby $5 monthly minimum.
- [ ] Render: https://render.com/pricing — free preview only, paid production.
- [ ] Existing managed host with separate resources — ONLY if client agrees and no Cane Corso database/secrets shared.
For database choose local PostgreSQL for development and independently hosted production Postgres. Neon free can help with dev; production requires backup, uptime and capacity review.

## Later: upload and payment
- [ ] Cloudflare Stream: authorize prepaid video storage and delivery usage, set monthly cost alerts, test a short upload.
- [ ] R2 separate buckets: public approved media, private identity/health evidence, offsite backup; no public ACL on sensitive bucket.
- [ ] Identity provider: ask vendors for Nigeria KYC/KYB coverage, data processing and per-check rates; use manual staff verification initially in beta with privacy rules.
- [ ] Payment partner: provide business deck, animal categories, buyer/seller countries, expected transaction values, exact fund hold/release request, dispute policy. Get **written acceptance** before live payment integration.
- [ ] Banking and tax counsel: approve money custody model, seller terms, commission VAT/tax treatment and refunds.
- [ ] Support: public complaint channel and animal welfare escalation process with accountable staff.

## Materials developers need from client
Product name/brand assets; approved species list; legal business/entity details (shared securely); explicit launch territories; commission policy; pickup/shipping policy; trust badge criteria; refund/inspection period; moderation rules; approved third-party contracts; support contact and privacy policy; billing owner and monthly cap.

## Signoff checklist
- [ ] Product scope approved
- [ ] Animal trading and welfare policies reviewed by qualified advisers
- [ ] Money flow/provider approved in writing
- [ ] Financial fees, payout and returns policy agreed
- [ ] Host/media budget and billing alert thresholds agreed
- [ ] App developer and domain accounts in business control
- [ ] CI/mobile/device testing plan approved
- [ ] Independent staging and production credentials prepared
- [ ] Public legal documents reviewed and published
- [ ] Beta support staff and moderation schedule assigned

## Links for policy and published fees
- GitHub https://github.com/pricing
- Firebase https://firebase.google.com/pricing
- Cloudflare https://developers.cloudflare.com/r2/pricing/
- Stream https://developers.cloudflare.com/stream/pricing/
- Apple https://developer.apple.com/help/account/membership/program-enrollment
- Google https://support.google.com/googleplay/android-developer/answer/6112435
- Railway https://docs.railway.com/pricing/plans
