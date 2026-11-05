# Operations runbook: monitoring, support, recovery and finance
Version 0.1 — 2026-11-05. Fill service URLs, on-call contacts, and legal escalation paths privately before production.

## Daily operations
- Check API health/error rate, DB connection pool, Redis health and background queue age.
- Examine payment processor event failures; reconcile prior-day payment/hold/release/refund and ledger against provider's authoritative settlement report. Unmatched items block payouts.
- Review new seller approvals, animal/report queues, urgent welfare cases, customer support unresolved cases.
- Track Stream uploaded/stored/delivered minutes and billing projection; prevent runaway prefetch and uploads.
- Verify backups completed and are encrypted; check alert noise and spam patterns.

## Weekly
- Review moderation false positives and response times; species policy changes.
- Inspect top slow SQL queries, API p95, memory, mobile crash rates, failed jobs, blocked uploads.
- Review conversion funnel, seller verification throughput, disputes, cancellations and completed protected sales.
- Cost review vs approved ceiling. Rotate access on departures and audit staff privilege grants.
- Exercise staging release and rollback scenario.

## Monthly
- Perform isolated restore test and report restored snapshot timestamp, integrity, RTO/RPO.
- Reconcile all held customer funds and provider statements; finance/legal sign off exceptions.
- Review data retention and deletion requests, staff/audit access and vendor terms.
- Reforecast variable media and payment costs; reserve for chargebacks and support.

## Alerts and severity
SEV1 triggers: unauthorized/duplicate payout, incorrect fund release, identity-document exposure, suspected active animal abuse trade, unavailable protected checkout for broad audience. Immediately freeze affected financial feature and riskier actions, preserve logs, page incident commander, notify provider/client and legal; publish status update according to incident policy.
SEV2: API widespread outage, chat unavailability, video delivery disruption, moderation backlog threatening safety.
SEV3: cosmetic or isolated noncritical issue.
Every alert must have owner, threshold, escalation route and action. Private pager/phone contacts should not be committed.

## Recovery and deployment
- Production release only from protected reviewed main with CI success, pinned commit artifact, migration preflight and rollback/feature flag plan.
- Use backup snapshots with encryption and separate storage credentials; regularly restore to isolated environment and validate referential/financial invariants.
- For API failure rollback tested artifact; for irreversible migrations, restore strategy must be explicitly planned before deploy.
- For corrupted finance data do not blindly restore over later valid events; enter incident mode, reconcile with financial provider and use controlled repair with double approval.

## Support and appeals
Tier 1: accounts, chats, listing visibility, status explanation; Tier 2: seller verification, payment exceptions, welfare, legal. SLA targets need business approval. Document every case with access controls and redacted exports; no support agent direct payout. The user can report/block and access appeal routes in app.

## Data protection
Respect legal retention schedule and holds; export/delete user data by verified request; preserve transactional obligations where legally required; secure document/key rotation; access log every admin inspection of identity or private health evidence.

## Billing incident
If Stream/watch minutes grow unexpectedly: lower prefetch, freeze new uploads of abusers, enforce creator caps, alert finance; do not silently remove customer evidence or delete paid order records. Disable nonessential analytics capture if usage caps exceeded.

## Production contacts to create externally
Client legal representative, product owner, engineering on-call, payment partner merchant support, finance controller, animal-welfare escalation, transport partners, cloud provider support. Store contact methods in a private incident tool, not public repository.
