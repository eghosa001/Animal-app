# Cost model, verified rates and spending controls
Prices checked 2026-11-05. **USD estimates exclude FX, tax/VAT, developer time, support staffing, legal fees, insurance, and provider negotiations.** Prices are not committed quotes. Revalidate before spending.

## Verified official prices and free allowances
| Item | Free allowance / verified price | Source |
|---|---|---|
| GitHub Free | Unlimited public/private repos, 2,000 Actions minutes/month for private repos; public standard runners often free | https://github.com/pricing |
| Android Google Play developer registration | $25 one-time | https://support.google.com/googleplay/android-developer/answer/6112435 |
| Apple Developer Program | $99/year | https://developer.apple.com/help/account/membership/program-enrollment |
| Cloudflare Stream video storage | $5 monthly per 1,000 video minutes stored (prepaid increments) | https://developers.cloudflare.com/stream/pricing/ |
| Cloudflare Stream delivery | $1 per 1,000 delivered minutes; preloading may count | https://developers.cloudflare.com/stream/pricing/ |
| Cloudflare R2 Standard storage | First 10 GB-month, 1M Class A, 10M Class B operations free/month; thereafter $0.015/GB-month, $4.50/M Class A and $0.36/M Class B | https://developers.cloudflare.com/r2/pricing/ |
| Cloudflare Workers | Free tier 100,000 requests/day (limits apply) | https://developers.cloudflare.com/workers/platform/pricing/ |
| Firebase Cloud Messaging & Crashlytics | No-cost service per Firebase price table | https://firebase.google.com/pricing |
| PostHog product analytics | First 1M events/month free | https://posthog.com/product-analytics/pricing |
| Cloudflare Turnstile | Free plan available | https://developers.cloudflare.com/turnstile/plans/ |
| Neon PostgreSQL free | 1 GB per project and 100 CU-hours/project monthly as of Oct 2026; can autosuspend | https://neon.com/blog/neon-free-plan-1-gb-per-project |
| Supabase free alternative | 500MB database and low-activity pause; Pro from $25/month | https://supabase.com/pricing |
| Railway Hobby | $5/month minimum includes $5 usage; excess is usage billed | https://docs.railway.com/pricing/plans |
| Render free alternative | For preview/testing only; official docs warn not to use free instances for production | https://render.com/docs/free |

**Choose one primary managed Postgres, not both Neon and Supabase.** Free dev tiers must never be represented as durable commerce production hosting.

## Video cost calculation
Monthly Stream dollars = 5 * CEILING(total stored video minutes / 1000) + delivered minutes / 1000, plus any applicable tax/extra features. Preloading counts as delivered minutes; reduce it by careful client design.
Examples:
| Scenario | Video storage | Video delivery | Stream only |
|---|---:|---:|---:|
| Tiny beta | 300 minutes | 5,000 minutes | $5 + $5 = $10/month |
| Limited pilot | 800 minutes | 20,000 minutes | $5 + $20 = $25/month |
| Public launch | 1,200 minutes | 200,000 minutes | $10 + $200 = $210/month |
| Heavy usage | 6,000 minutes | 1,000,000 minutes | $30 + $1,000 = $1,030/month |
These are mathematical scenarios, not traffic forecasts. An uploaded 60-second clip seen by 1,000 people for 30 seconds each consumes about 500 delivered minutes; actual buffer/preload can increase billed delivery.

## Planning budgets (illustrative, **not provider quotes**)
| Stage | Monthly operating range | Conditions |
|---|---:|---|
| Local development | $0–$15 | Free software + local containers; no always-on production, no commercial video traffic |
| Hosted staging / small closed beta | $20–$90 | Small backend+DB/Redis and media, test accounts, no high-availability |
| Limited live pilot | $60–$220 | ~20k video delivered minutes ($20) and low/moderate hosting |
| Early public release | $250–$700+ | Example ~200k video minutes ($200) and scaled backend, storage, ops |
| Fast-growing social platform | $1,000+/month | Video watch time, moderation and uptime drive costs |

These ranges include broad provisional hosting/observability allowances, but **exclude** identity checks, transaction fees, SMS, labor, human moderation, legal/tax/insurance, transport and customer refunds. Real invoices can be materially lower or higher.
Fixed store registration in first year: $25 Google + $99 Apple = **$124** before any local tax; recurring annual Apple $99. Domain name usually paid annually; obtain registrar quote. A Mac/macOS CI may add cost for iOS build/signing if none is available.

## Variable charges not yet quotable
- Approved marketplace payment provider transaction fee, hold and release fee, bank transfer and chargeback fees.
- Seller identity/business verification per check and document validation.
- SMS OTP or email delivery once free tiers insufficient.
- Law firm review, consumer terms, NDPA/privacy audit, animal law/veterinary consultants and possible licensing.
- Live-animal logistics, insurance, customer-service and dispute staff.
- Marketing/creator incentives, content moderation provider, fraud detection.

## Example unit economics
Illustrative animal listing at ₦250,000 sold with 5% commission yields **₦12,500 gross platform commission**, NOT profit. Net revenue is gross commission minus attributable processing, payout, refunds/chargebacks, support, tax and variable infrastructure. Never assume seller net from commission alone; disclose payer of each fee.
Break-even orders = monthly fixed+variable operating cost / average realized net commission per completed order. Model real dispute/refund risk.

## Controls to implement
- Assign client-owned billing administrator; no hidden auto-upgrade.
- Set cloud provider billing alerts (25%, 50%, 80%, 100%), video rate limits, video quota, anomaly alerts.
- Weekly tracking: active creators, stored minutes, watched/delivered minutes, R2 GB/operations, DB CPU/GB, Redis memory, API requests, payment volume, chargebacks.
- Month-end cost review: infra per 1k active users, video cost per watch hour, cost per completed order, moderation overhead and commission margin.
- Cutoff policy: pause video uploads or cap bandwidth-heavy features safely if budget hard cap reached; never lose payments or evidence.
- Use service-level usage alerts rather than guessing free tiers are unlimited.

## Spending order
1. $0: engineering tools, local dev, mocked checkout, design, documents.
2. $25 Play Console and $99/year Apple Developer **only when ready for distribution/testing needs**; organization ownership first.
3. Low-cost staging compute/database and minimal Stream allocation for media tests.
4. Production infrastructure, security, vetted payment partnership and legal/commercial approval.
5. Paid growth/marketing tools only when metrics justify them.
