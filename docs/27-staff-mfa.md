# Staff authenticator MFA — Admin and moderation security

**Implemented and merged in [PR #26](https://github.com/eghosa001/Animal-app/pull/26).** The [combined branch tests](https://github.com/eghosa001/Animal-app/actions/runs/42598245974) and [post-merge tests](https://github.com/eghosa001/Animal-app/actions/runs/42598475720) passed **74 tests + 4 subtests** with PostgreSQL, Django migration validation and lint. Staging operator enrollment and real-device acceptance remain separate release gates. This security improvement is not a claim that all operational security or client identity verification is finished.

## Why

The previous staff login accepted password-only Django Admin sessions and there was an authenticated HTTP endpoint for photo review. Those controls were insufficient for staff who can view sensitive seller documents or approve listings. This task hardens those boundaries.

## Design and free dependency

Use the public-domain open-source [django-otp](https://github.com/django-otp/django-otp) v1.7.5+ under a version-constrained dependency. The project supplies time-based codes (TOTP) and one-time static emergency codes. No paid SMS, Authy contract, hosted identity platform or extra commercial account is required. It runs within the existing Django and PostgreSQL architecture.

- The Django Admin now uses **OTPAdminSite**, which requires a valid password plus a confirmed second factor before staff can access protected admin pages or actions.
- Custom seller-review, listing-moderation and photo-moderation Admin actions inherit that check.
- The media moderation API **only accepts session-based authentication** and additionally verifies the session passed an OTP challenge. A JWT cannot bypass it.
- Seller identity-evidence reads by assigned reviewers and photo-moderator private reads also require OTP-verified Django sessions. Buyer/seller ownership rules are unchanged.
- Staff accounts are blocked from the consumer/mobile JWT login, refresh and JWT authorization. Existing staff bearer tokens issued before rollout also fail.
- Customer/breeder JWT, profile and listing functionality remain separate.

## First staff authenticator enrollment

**Do not deploy this change with no approved, enrolled administrator.** Otherwise Admin will intentionally deny access until the bootstrap is completed.

1. Back up the staging database and test the procedure in staging. Choose a qualified platform owner with an active, email-verified staff account. Ensure that user has a strong unique password and secure control of the registration email.
2. On a **private, interactive SSH console** connected to the Django service (never a CI job, cloud build log, chat, screen share or ticket), run:
   ```sh
   cd backend
   python manage.py bootstrap_staff_totp --email=administrator@example.com
   ```
3. The command generates an **unconfirmed** TOTP device and displays a one-time private `otpauth://` provisioning URI. Import the URI into a reputable authenticator application on the administrator's device, or manually add the embedded secret. The URI/secret should never be stored in Git, issue comments, photos, support tickets or cloud logging.
4. Enter the current authenticator code at the private terminal prompt. Only an accepted code confirms enrollment; failed attempts erase the temporary device. The command rejects non-interactive shells and refuses to overwrite a confirmed device.
5. Open `/admin/login/`; enter the staff account password, choose the enrolled device and enter the current authenticator code. Verify the staff moderation queue is available.
6. Enroll a second authorized administrator on a separate securely controlled device as a documented recovery path. A separate one-time recovery code can be provisioned through django-otp's `addstatictoken` management command only by an authorized operator, with the code transmitted through a distinct secure channel and erased after use.

**Important:** The first factor alone cannot access any privileged moderation page. Enrolling an additional device, disabling a device, or resetting staff MFA is a privileged operator procedure. No customer self-service MFA enrollment is exposed, and never email a TOTP secret.

## Account and API boundaries

| Route | Staff requirement |
|---|---|
| `/admin/`, Admin seller/media review and publication actions | Django session with confirmed OTP |
| `POST /api/v1/media/{uuid}/review/` | Django session, confirmed OTP and explicit media-review permission |
| Private evidence `GET /api/v1/media/{uuid}/file/` | Own file, or assigned authorized OTP-verified staff |
| `POST /api/v1/auth/login`, `/refresh`, bearer-authorized API | Consumer accounts only; staff JWT issuance and use denied |

Staff have no privileged mobile JWT path. OTP verification is tied to the session; ending or invalidating the session removes that trust. Django and django-otp must run behind HTTPS with secure cookies, correct CSRF protection, brute-force controls and a monitored server clock. Standard TOTP devices use no network service.

## Restrictions and remaining production gates

- Staff TOTP secrets are in the database as defined by django-otp; restrict database access and encrypt managed PostgreSQL storage and backups. Review envelope encryption and key rotation before long-term production adoption.
- TOTP phishing resistance is **not** as strong as WebAuthn/passkeys. Hardware-bound/WebAuthn MFA is a recommended P1 security enhancement for privileged finance and identity roles.
- Staff login throttling/WAF limits, separate anomaly alerts, audited permission assignment, secure recovery playbooks, device-lost procedures and real authorized user testing must be completed in staging. A one-time backup code must not be stored as plaintext in support systems.
- A migration from password-only staff sessions intentionally locks out existing sessions until full MFA login. Run bootstrap for administrators first.
- Device enrollment via the private command is limited to approved operators with access to the runtime; no public enrollment endpoint is exposed.
- Uploading an identity document and being a verified seller remain separate from staff authentication and do not imply automated KYC.
- No real R2 account, Apple signing, transactional email delivery, live checkout or client accounts are provisioned by this task.
- [Account security issue #10](https://github.com/eghosa001/Animal-app/issues/10) remains open for explicit session/device management, account export/deletion, secure staff recovery operations, and device-level acceptance.

## Acceptance

Django/PostgreSQL CI must prove:
1. Password-only staff browser session cannot enter Admin, including superusers.
2. Session with valid confirmed device can access Admin; device deactivation revokes access.
3. Nonstaff browser sessions and staff JWTs cannot moderate or download seller identity evidence.
4. Consumer JWT login and refresh remain functional.
5. Staff auth routes return no JWT and old staff JWTs fail.
6. TOTP code replay is rejected; bootstrap refuses noninteractive and already-confirmed accounts.
7. Existing seller and media review tests remain green with OTP staff test sessions.
8. `makemigrations --check` and Django system checks pass.

Human acceptance still requires staging enrollment, a working real authenticator, server time drift checks, browser checks and a recovery drill. These are not proven by unit tests alone.
