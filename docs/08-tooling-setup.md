# Best free tools and environment setup
Version 0.1 — 2026-11-05. This is a self-service checklist, not a record that accounts have already been created.

## Recommended stack, selected for standards and practical cost
| Purpose | Recommendation | Free? | Notes |
|---|---|---|---|
| Repository/CI | GitHub Free, Actions, Issues, Projects, Dependabot | Yes within limits | Keep repo private until brand/business approves disclosure |
| IDE | VS Code + Dart/Flutter/Python extensions | Yes | Android Studio for emulator and Android SDK |
| Cross-platform mobile | Flutter + Dart (stable pinned SDK) | Open source | Android and iOS in one app |
| Backend | Python + Django + Django REST Framework | Open source | Built-in Django Admin for initial internal staff tools |
| Realtime | Django Channels + Redis | Open source | Server-side persisted messages; no free managed Redis guarantee |
| Jobs | Celery + Redis | Open source | Notifications/reconciliation/media events |
| Relational database | PostgreSQL | Open source | Local Docker free; managed production hosting billed |
| DB GUI | DBeaver Community / pgAdmin | Free | Never expose production DB publicly |
| Local services | Docker Engine / Docker Compose | Free/open alternatives | Docker Desktop commercial terms depend on organization size |
| Mobile state/routing | Riverpod + go_router | Open source | Prefer a single consistent architecture, tested interfaces |
| Media | Cloudflare R2 photos/documents | 10GB monthly free allowance | Subscription/billing setup may be required |
| Video | Cloudflare Stream | Paid, usage-based | Do not activate before video-budget approval |
| Push and crashes | Firebase Cloud Messaging + Crashlytics | No-cost services | Firebase billing varies for other products |
| Analytics | PostHog | Free monthly events allowance | Limit PII and session replay |
| Error tracking | Sentry (optional) | Has free tier | Choose either Sentry or PostHog error monitoring initially |
| Bot controls | Cloudflare Turnstile | Free plan | Appropriate for web forms; verify tokens server-side |
| Designs | Figma Starter or Penpot | Free tiers/open source | Maintain components and screen flows |
| Admin browser tests | Playwright | Open source | Cross-browser admin functionality |
| Backend tests | pytest, pytest-django, coverage, Ruff, Bandit, pip-audit | Open source | Static and integration checks |
| Mobile tests | flutter test, integration_test | Included | Android and iOS device matrix |
| Load tests | k6 or Locust | Open source | Run only against test environment |
| Dev secrets | .env outside git, GitHub Actions secrets | Free basics | Production cloud secret manager as needed |
| Monitoring | Uptime Kuma self-hosted (optional), PostHog, provider metrics | Free software | Infrastructure cost remains |
| Diagrams | Mermaid in Markdown, diagrams.net | Free | Source-controlled architecture diagrams |

## Step 1 — GitHub repository ownership
Repo currently found at https://github.com/eghosa001/Animal-app. It was public on inspection; **Settings > General > Danger Zone > Change repository visibility > Private** (GitHub may require confirmation). Never create public issues with client identity documents, credentials or payment contracts. If client is the owner, transfer to their organization only after signed authorization and backup. Add collaborators via GitHub invitations and minimum permissions. Create labels: feature, bug, risk, legal, payment-gate, security, blocked, launch, documentation.

## Step 2 — Workstation
Install Git, Python 3.13 compatible with selected Django version, Flutter stable SDK, Android Studio SDK/emulator, VS Code, Docker/Compose, and DBeaver. On Windows enable WSL2 if feasible. Android builds can be tested on a USB-enabled physical Android phone. To compile/sign iOS releases, arrange a macOS/Xcode environment (owned Mac or permitted macOS CI): Android/Windows tooling alone cannot perform all iOS release signing steps.

Check:
- git --version
- python --version
- flutter doctor -v
- docker compose version
- adb devices
- On macOS: xcodebuild -version

Prefer local PostgreSQL/Redis containers for first development, not always-on paid infrastructure. Set backend environment files outside Git; copy example env file without real credentials.

## Step 3 — Cloud accounts in order
**Now:** GitHub, Cloudflare, Firebase project for test environment, Figma/Penpot, PostHog (optional analytics), Google Play Console owner planning (registration required for distribution), Apple Developer organization owner planning. Enable MFA. Document each account's organization, owner and billing admin without storing secrets in Git.
**When mobile/backend skeleton exists:** Development R2 bucket (private), Firebase Android/iOS app registration and Cloud Messaging integration, optionally Turnstile site keys, stage hosting.
**Before upload beta:** Cloudflare Stream active with budget alert and signed-direct-upload design; set low test quotas.
**Before commerce:** Business verification/KYC provider evaluation, marketplace payment partner written preapproval, sandbox credentials, legal terms, test consumer/merchant accounts.
**Before public release:** production hosting, database backups, domain, app store accounts, refund/support channels, legal policies and support staff.

## Step 4 — Preferred environments
- Local: Django, Postgres, Redis, fake providers; no payment authority.
- Staging: separate managed or low-cost services, synthetic users and animals, sandbox payments, test push.
- Production: separately billed host/database, secure cloud storage, real monitored video quotas, authorized provider, verified legal/business accounts. Avoid borrowing current Cane Corso Oracle database or keys.

## Step 5 — GitHub settings to configure
Enable 2FA for maintainers, Dependabot security alerts and updates, secret scanning if available, protected main branch/rulesets where plan permissions support, required CI checks, PR review, GitHub Actions minimal permissions, environment secrets for staging/production. Store package signing certificates outside repo. Prefer workload identity over long-lived secret when provider supports it.

## Step 6 — Provider links
- Flutter: https://docs.flutter.dev/get-started/install
- Android Studio: https://developer.android.com/studio
- Python: https://www.python.org/
- Django: https://docs.djangoproject.com/
- PostgreSQL: https://www.postgresql.org/
- Django REST Framework: https://www.django-rest-framework.org/
- GitHub: https://github.com/pricing
- Figma: https://www.figma.com/pricing/
- Penpot: https://penpot.app/
- Firebase: https://firebase.google.com/pricing
- Cloudflare: https://dash.cloudflare.com/
- R2: https://developers.cloudflare.com/r2/pricing/
- Stream: https://developers.cloudflare.com/stream/pricing/
- PostHog: https://posthog.com/pricing
- Sentry: https://sentry.io/pricing/
- Google Play Console: https://play.google.com/console/
- Apple Developer: https://developer.apple.com/programs/enroll/
- Railway: https://railway.com/pricing
- Render: https://render.com/pricing
- Neon: https://neon.com/pricing
- Cloudflare Turnstile: https://developers.cloudflare.com/turnstile/plans/

## Design system and accessibility
Choose one body type scale, consistent spacing, tappable controls >=44x44 logical pixels when appropriate, accessible labels, high contrast, responsive/safe-area and keyboard handling, loading/empty/error states, multilingual-ready copy, low-bandwidth fallback. Use Material 3 as foundation, not a generic template copied without adapting animal marketplace flows.

## Secrets to create LATER (names only)
DJANGO_SECRET_KEY, DATABASE_URL, REDIS_URL, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, CLOUDFLARE_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET, STREAM_API_TOKEN, FIREBASE_PROJECT_ID, FCM credentials, POSTHOG_PROJECT_KEY (public ingest), SENTRY_DSN, PAYMENT_PROVIDER_API_KEY, PAYMENT_WEBHOOK_SECRET, SMTP_API_KEY, APPLE signing materials, ANDROID keystore.
Never place actual values in Git, chat, screenshots or issue comments. Public mobile keys (e.g. Firebase client config) still need backend policies and limits.
