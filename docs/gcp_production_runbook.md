# Google Cloud Production Runbook

This runbook shows how to deploy the API + worker on Google Cloud with Cloud Run, Cloud SQL, Secret Manager, and Cloud Scheduler.

## Architecture

- Cloud Run service: `plugin-boutique-api`
- Cloud Run job: `plugin-boutique-worker` (one-shot)
- Cloud Run job: `plugin-boutique-migrate` (runs `alembic upgrade head`)
- Cloud SQL (Postgres): primary database
- Secret Manager: `DATABASE_URL`, SMTP, Twilio secrets
- Artifact Registry: API and worker container images
- Cloud Scheduler: triggers worker job on a cron schedule

## Prerequisites

- `gcloud` CLI installed and authenticated
- Billing-enabled Google Cloud project
- Twilio account + verified sender
- SMTP credentials for email verification codes

## 1) Bootstrap project services and artifact repo

```bash
cd /Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker
bash deploy/gcp/bootstrap_gcp.sh <PROJECT_ID> <REGION> <ARTIFACT_REPOSITORY>
```

## 2) Create secret containers

```bash
bash deploy/gcp/create_secrets.sh <PROJECT_ID>
```

Then add real values to each secret:

```bash
echo -n 'postgresql+psycopg://USER:PASS@/DB?host=/cloudsql/PROJECT:REGION:INSTANCE' | gcloud secrets versions add DATABASE_URL --data-file=-
echo -n 'smtp.gmail.com' | gcloud secrets versions add SMTP_ADDRESS --data-file=-
echo -n 'your_email@gmail.com' | gcloud secrets versions add EMAIL_ADDRESS --data-file=-
echo -n 'your_app_password' | gcloud secrets versions add EMAIL_PASSWORD --data-file=-
echo -n 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' | gcloud secrets versions add TWILIO_ACCOUNT_SID --data-file=-
echo -n 'your_twilio_auth_token' | gcloud secrets versions add TWILIO_AUTH_TOKEN --data-file=-
echo -n '+15551234567' | gcloud secrets versions add TWILIO_FROM_NUMBER --data-file=-
```

## 3) Build and deploy (API + migration job + worker job)

```bash
bash deploy/gcp/deploy_via_cloud_build.sh <PROJECT_ID> <REGION> <ARTIFACT_REPOSITORY> <PROJECT:REGION:CLOUDSQL_INSTANCE> <APP_SERVICE_ACCOUNT_EMAIL> "https://your-frontend-domain.com"
```

This script uses `cloudbuild.yaml` to:

1. build and push API + worker images
2. deploy API Cloud Run service
3. deploy and execute migration job (`alembic upgrade head`)
4. deploy worker Cloud Run job (one-shot mode)

## 4) Schedule worker execution

```bash
bash deploy/gcp/create_worker_scheduler.sh <PROJECT_ID> <REGION> plugin-boutique-worker plugin-boutique-worker-every-10m "*/10 * * * *" <SCHEDULER_SERVICE_ACCOUNT_EMAIL>
```

## 5) Production env requirements

Set these env vars on Cloud Run (done via `cloudbuild.yaml`):

- `APP_ENV=production`
- `DB_AUTO_CREATE=false`
- `AUTH_DEV_MODE=false`
- `AUTH_COOKIE_SECURE=true`
- `CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com`

## 6) Health and readiness checks

- Liveness: `GET /health`
- Readiness: `GET /ready`

## 7) Rollback plan

1. Re-deploy previous image tag for API and worker.
2. If migration introduced a problem, restore from Cloud SQL backup.
3. Re-run smoke checks:
   - `GET /health`
   - `GET /ready`
   - registration/login path

## 8) Optional Terraform path

There is also a Terraform scaffold:

- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/infra/terraform/main.tf`
- `/Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/infra/terraform/README.md`

Use Terraform when you want repeatable infra provisioning in code.

