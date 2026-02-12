#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 6 ]]; then
  echo "Usage: $0 <project-id> <region> <worker-job-name> <scheduler-job-name> <cron-schedule> <scheduler-service-account-email>"
  echo "Example cron schedule: '*/10 * * * *'"
  exit 1
fi

PROJECT_ID="$1"
REGION="$2"
WORKER_JOB="$3"
SCHEDULER_JOB="$4"
CRON_SCHEDULE="$5"
SCHEDULER_SERVICE_ACCOUNT="$6"

gcloud config set project "${PROJECT_ID}"

RUN_URI=$(gcloud run jobs describe "${WORKER_JOB}" --region "${REGION}" --format='value(name)')

if gcloud scheduler jobs describe "${SCHEDULER_JOB}" --location "${REGION}" >/dev/null 2>&1; then
  echo "Updating existing scheduler job ${SCHEDULER_JOB}"
  gcloud scheduler jobs update http "${SCHEDULER_JOB}" \
    --location "${REGION}" \
    --schedule "${CRON_SCHEDULE}" \
    --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${WORKER_JOB}:run" \
    --http-method POST \
    --oauth-service-account-email "${SCHEDULER_SERVICE_ACCOUNT}" \
    --oauth-token-scope "https://www.googleapis.com/auth/cloud-platform"
else
  echo "Creating scheduler job ${SCHEDULER_JOB}"
  gcloud scheduler jobs create http "${SCHEDULER_JOB}" \
    --location "${REGION}" \
    --schedule "${CRON_SCHEDULE}" \
    --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${WORKER_JOB}:run" \
    --http-method POST \
    --oauth-service-account-email "${SCHEDULER_SERVICE_ACCOUNT}" \
    --oauth-token-scope "https://www.googleapis.com/auth/cloud-platform"
fi

echo "Worker scheduler configured for job resource: ${RUN_URI}"

