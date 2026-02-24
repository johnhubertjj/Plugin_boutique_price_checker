#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 5 ]]; then
  echo "Usage: $0 <project-id> <region> <artifact-repo> <cloudsql-connection> <service-account-email> [cors-origins]"
  exit 1
fi

PROJECT_ID="$1"
REGION="$2"
REPOSITORY="$3"
CLOUDSQL_CONNECTION="$4"
SERVICE_ACCOUNT="$5"
CORS_ALLOWED_ORIGINS="${6:-}"

gcloud config set project "${PROJECT_ID}"

gcloud builds submit . \
  --config=cloudbuild.yaml \
  --substitutions="_REGION=${REGION},_REPOSITORY=${REPOSITORY},_CLOUDSQL_CONNECTION=${CLOUDSQL_CONNECTION},_SERVICE_ACCOUNT=${SERVICE_ACCOUNT},_CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}"

