# Terraform Scaffold (Google Cloud)

This folder provides optional infrastructure-as-code for:

- required Google APIs
- Artifact Registry (Docker)
- Cloud SQL (Postgres)
- Secret Manager placeholders
- Cloud Run API service
- Cloud Run worker job
- Cloud Scheduler trigger for worker job

## Usage

1. Initialize:

```bash
cd /Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker/infra/terraform
terraform init
```

2. Configure variables:

```bash
cp terraform.tfvars.example terraform.tfvars
```

3. Plan/apply:

```bash
terraform plan
terraform apply
```

## Important notes

- Set real SMTP/Twilio secret values in Secret Manager after apply.
- `DATABASE_URL` secret gets an initial value from Terraform using the generated Cloud SQL credentials.
- Keep `deletion_protection = true` for production databases.
- This scaffold is intentionally minimal and should be reviewed before production use.

