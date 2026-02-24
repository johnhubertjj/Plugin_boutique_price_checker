# Google Cloud Cost Estimate (USD, us-central1)

This is a practical estimate for the current architecture:

- Cloud Run API service
- Cloud Run worker job (scheduled)
- Cloud SQL Postgres
- Secret Manager
- Artifact Registry
- Cloud Scheduler

Pricing changes over time, so use this as a planning baseline.

## Current price points used

Sources:

- Cloud Run pricing and free tier: [cloud.google.com/run](https://cloud.google.com/run) and [cloud.google.com/run/pricing](https://cloud.google.com/run/pricing?authuser=3)
- Cloud SQL Postgres pricing (us-central1): [cloud.google.com/sql/docs/postgres/pricing](https://cloud.google.com/sql/docs/postgres/pricing)
- Cloud Scheduler pricing: [cloud.google.com/scheduler/pricing](https://cloud.google.com/scheduler/pricing)
- Secret Manager pricing: [cloud.google.com/secret-manager/pricing](https://cloud.google.com/secret-manager/pricing)
- Artifact Registry pricing: [cloud.google.com/artifact-registry/pricing](https://cloud.google.com/artifact-registry/pricing)
- Cloud Logging pricing summary: [cloud.google.com/products/observability/pricing](https://cloud.google.com/products/observability/pricing)

Key values used:

- Cloud Run CPU: `$0.000018 / vCPU-second` (beyond free tier)
- Cloud Run memory: `$0.000002 / GiB-second` (beyond free tier)
- Cloud Run free tier (request-based): `180,000 vCPU-seconds`, `360,000 GiB-seconds`, `2M requests` monthly (us-central1 baseline)
- Cloud SQL (us-central1 default pricing): `vCPU $0.0413/hour`, `RAM $0.007/GiB-hour`
- Cloud SQL SSD storage: `$0.000232877 / GiB-hour`
- Cloud SQL backups used: `$0.000109589 / GiB-hour`
- Cloud Scheduler: `$0.10/job/month` (first 3 jobs free)
- Secret Manager active versions: `$0.06/version/month` (first 6 free)
- Artifact Registry storage: `$0.10/GB/month` (first 0.5 GB free)
- Cloud Logging ingest: `$0.50/GiB` (first 50 GiB/project/month free)

## Scenario A: small production (early launch)

Assumptions:

- API traffic mostly within Cloud Run free tier
- Worker runs every 10 minutes (`Cloud Scheduler` + `Cloud Run Job`)
- Cloud SQL: `1 vCPU, 3.75 GiB RAM`
- Cloud SQL storage: `20 GiB`, backups used: `20 GiB`
- Artifact Registry: `2 GiB`
- Secret Manager: 7 active secrets

Estimated monthly:

- Cloud SQL compute: `~$49.31`
- Cloud SQL storage: `~$3.40`
- Cloud SQL backups: `~$1.60`
- Cloud Run API + worker: `~$0 to low single digits` (often fully in free tier at this scale)
- Cloud Scheduler: `~$0` (first 3 jobs free)
- Secret Manager: `~$0.06` (+ negligible access ops)
- Artifact Registry: `~$0.15`
- Logging/monitoring: often `$0` initially if under free allotments

Total: roughly **$55 to $75/month**

## Scenario B: moderate production

Assumptions:

- API exceeds free tier (steady user traffic)
- Cloud SQL same as Scenario A
- Logs and egress still modest

Estimated monthly:

- Cloud SQL stack: `~$54 to $60`
- Cloud Run overage: `~$20 to $80` (depends heavily on request duration + memory allocation)
- Other services: `~$1 to $10`

Total: roughly **$80 to $160/month**

## Biggest cost drivers

1. Cloud SQL size and HA setting (HA can roughly double compute/storage portions).
2. Cloud Run request duration and memory sizing.
3. Network egress.
4. Logging volume (if much more than 50 GiB/month).

## External costs not included

- Twilio SMS charges (2FA phone OTP)
- Domain/SSL/CDN if you add a separate frontend hosting path

## How to keep costs down

1. Start with non-HA Cloud SQL for early launch, then upgrade when needed.
2. Keep API memory/vCPU small and tune request timeouts.
3. Run worker as one-shot Cloud Run Job via Scheduler, not always-on service.
4. Set log retention and avoid noisy debug logging in production.
5. Co-locate Cloud Run, Cloud SQL, and Artifact Registry in same region.

