# Security, privacy, legal compliance and animal welfare
Planning controls — not a substitute for legal counsel or payment-provider underwriting. 2026-11-05.

## Security baseline
- Threat-model identity fraud, impersonation, fake animal listings, stolen media, fraudulent payment webhooks, malicious refunds, account takeover, private chat leak, location/doxxing, animal welfare abuse, insider payouts and CI supply-chain compromise.
- OWASP ASVS for backend/web and OWASP MASVS for mobile checklist; review before release.
- TLS everywhere, MFA for all staff, least-privilege production credentials and time-limited signed media links.
- Secure password hashing (Argon2), breach-resistant session management, refresh rotation/revocation, optional user MFA, brute-force protection.
- Validate request permissions and scopes server-side; no direct object references bypass, no user-controlled order amounts.
- Secret scanning, dependency audits, pinned builds/lockfiles and signed release artifacts.
- Production and stage accounts/buckets/keys separated; no live customer data in local/staging.
- Provider webhooks verified; all financial operations recorded and independently reconciled.
- Sensitive evidence encrypted at rest, access logged, retention enforced; private keys never in app bundle.
- Backups encrypted, restore tested, admin access through minimum privileges and break-glass audit.
- Use Cloudflare Turnstile for relevant web attack surfaces; server-side token verification required. Not a substitute for mobile abuse controls.

## Privacy by design
Nigeria-first assumption. Review Nigeria Data Protection Act and NDPC guidance, plus other applicable territories before launch. Produce: data inventory; lawful bases; user notices; privacy impact assessment for ID verification, chat and animal/location data; processor contracts; cross-border transfer analysis; data deletion/export; retention schedule; breach response; child safety policy. Never publicly show seller's street address, private identity documents, buyer delivery location or other users' phone numbers without deliberate sharing.
Session replays and analytics must redact private chat, health documents, banking and address fields. Disable replay on checkout and sensitive admin pages.

## Legal gating checklist
- Legal entity and contractual seller/buyer relationships clear.
- Written payment marketplace/escrow suitability and provider contracts.
- Species restriction list by launch jurisdiction, licensed trade requirements, protected wildlife.
- Live-animal transportation regulations, required veterinary certificates, transit and welfare standards; operator liability and insurance.
- Seller claims, breed/purity verification language, health disclaimers, independent lab records and misrepresentation policy.
- Fair refund/consumer terms; dispute appeals; prohibited-activity enforcement.
- Off-platform warning does not disclaim non-waivable rights.
- Store developer ownership, app reviews and payments by the correctly registered business.
- Distinguish physical animal purchase from digital boosts/subscriptions under Apple/Google billing policies.
- Regional VAT, corporate taxes, withholding, marketplace invoices and payout reporting reviewed with accountant.

## Trust & safety workflow
Animal welfare report -> immediate triage -> remove risky listing or disable sale as needed -> preserve evidence -> escalate to qualified expert/law enforcement where legally required -> notify stakeholders within lawful limits -> appeal process. Never reveal confidential reports to public.
No endangered/trade-prohibited species, no abusive breeding practices, no animal fighting, no undocumented wildlife trade. Create species-specific review matrix and review it periodically.

## Incident severity
SEV1: unauthorized money movement, customer-data leak, live-animal safety incident, prolonged checkout outage. Pause affected checkout/payout via feature flag, assign commander, retain evidence, notify payment partner and legal, reconcile and restore from known state. SEV2: widespread messaging/media failure. SEV3: isolated feature bug. Log escalation channels and on-call contacts outside repository secrets.

## Vendor and account control
The client's legal entity should own domains, cloud billing, payment provider, Apple/Google publishing, Firebase, and monitoring projects; developers granted roles without sharing personal passwords. Avoid service-account JSON in GitHub. Use encrypted GitHub environment secrets or cloud workload identity when supported.

## Compliance references
- Nigeria Data Protection Commission: https://ndpc.gov.ng/
- Apple App Review: https://developer.apple.com/app-store/review/guidelines/
- Google Play policies: https://support.google.com/googleplay/android-developer/
- OWASP ASVS: https://owasp.org/www-project-application-security-verification-standard/
- OWASP MASVS: https://mas.owasp.org/
- NIgerian wildlife regulator: https://nesrea.gov.ng/
