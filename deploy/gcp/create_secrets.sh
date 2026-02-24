#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <project-id>"
  exit 1
fi

PROJECT_ID="$1"

gcloud config set project "${PROJECT_ID}"

create_secret_if_missing() {
  local name="$1"
  if gcloud secrets describe "${name}" >/dev/null 2>&1; then
    echo "Secret ${name} already exists"
  else
    gcloud secrets create "${name}" --replication-policy="automatic"
    echo "Created secret ${name}"
  fi
}

for secret in DATABASE_URL SMTP_ADDRESS EMAIL_ADDRESS EMAIL_PASSWORD TWILIO_ACCOUNT_SID TWILIO_AUTH_TOKEN TWILIO_FROM_NUMBER; do
  create_secret_if_missing "${secret}"
done

echo "Now add values, for example:"
echo "echo -n 'postgresql+psycopg://USER:PASS@/DB?host=/cloudsql/PROJECT:REGION:INSTANCE' | gcloud secrets versions add DATABASE_URL --data-file=-"

