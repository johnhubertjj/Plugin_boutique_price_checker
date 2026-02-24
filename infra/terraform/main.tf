terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "required" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "sqladmin.googleapis.com",
    "cloudscheduler.googleapis.com",
    "iam.googleapis.com",
  ])
  project                    = var.project_id
  service                    = each.value
  disable_dependent_services = false
}

resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = var.artifact_repository
  format        = "DOCKER"
  depends_on    = [google_project_service.required]
}

resource "google_service_account" "app" {
  account_id   = "${var.name_prefix}-app"
  display_name = "Plugin Boutique application service account"
}

resource "google_service_account" "scheduler" {
  account_id   = "${var.name_prefix}-scheduler"
  display_name = "Plugin Boutique scheduler service account"
}

resource "google_project_iam_member" "scheduler_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_project_iam_member" "scheduler_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_project_iam_member" "app_secret_access" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.app.email}"
}

resource "google_project_iam_member" "app_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.app.email}"
}

resource "random_password" "db_password" {
  length  = 24
  special = false
}

resource "google_sql_database_instance" "postgres" {
  name             = "${var.name_prefix}-pg"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier = var.cloudsql_tier

    ip_configuration {
      ipv4_enabled = true
    }

    backup_configuration {
      enabled = true
    }
  }

  deletion_protection = var.deletion_protection
  depends_on          = [google_project_service.required]
}

resource "google_sql_database" "app_db" {
  name     = var.database_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app_user" {
  name     = var.database_user
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

locals {
  database_url = "postgresql+psycopg://${google_sql_user.app_user.name}:${random_password.db_password.result}@/${google_sql_database.app_db.name}?host=/cloudsql/${var.project_id}:${var.region}:${google_sql_database_instance.postgres.name}"
}

resource "google_secret_manager_secret" "secrets" {
  for_each = toset([
    "DATABASE_URL",
    "SMTP_ADDRESS",
    "EMAIL_ADDRESS",
    "EMAIL_PASSWORD",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_FROM_NUMBER",
  ])
  secret_id = each.value
  replication {
    auto {}
  }
  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.secrets["DATABASE_URL"].id
  secret_data = local.database_url
}

resource "google_cloud_run_v2_service" "api" {
  name     = var.api_service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.app.email
    max_instance_request_concurrency = 40

    containers {
      image = var.api_image

      env {
        name  = "APP_ENV"
        value = "production"
      }
      env {
        name  = "DB_AUTO_CREATE"
        value = "false"
      }
      env {
        name  = "AUTH_DEV_MODE"
        value = "false"
      }
      env {
        name  = "CORS_ALLOWED_ORIGINS"
        value = var.cors_allowed_origins
      }
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["DATABASE_URL"].secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "SMTP_ADDRESS"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["SMTP_ADDRESS"].secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "EMAIL_ADDRESS"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["EMAIL_ADDRESS"].secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "EMAIL_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["EMAIL_PASSWORD"].secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "TWILIO_ACCOUNT_SID"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["TWILIO_ACCOUNT_SID"].secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "TWILIO_AUTH_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["TWILIO_AUTH_TOKEN"].secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "TWILIO_FROM_NUMBER"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["TWILIO_FROM_NUMBER"].secret_id
            version = "latest"
          }
        }
      }
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = ["${var.project_id}:${var.region}:${google_sql_database_instance.postgres.name}"]
      }
    }
  }

  depends_on = [google_secret_manager_secret_version.database_url]
}

resource "google_cloud_run_v2_job" "worker" {
  name     = var.worker_job_name
  location = var.region

  template {
    template {
      service_account = google_service_account.app.email
      max_retries     = 1
      timeout         = "1800s"

      containers {
        image = var.worker_image
        env {
          name  = "APP_ENV"
          value = "production"
        }
        env {
          name  = "DB_AUTO_CREATE"
          value = "false"
        }
        env {
          name  = "WORKER_RUN_ONCE"
          value = "true"
        }
        env {
          name = "DATABASE_URL"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.secrets["DATABASE_URL"].secret_id
              version = "latest"
            }
          }
        }
      }
      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = ["${var.project_id}:${var.region}:${google_sql_database_instance.postgres.name}"]
        }
      }
    }
  }
}

resource "google_cloud_scheduler_job" "worker_trigger" {
  name        = "${var.name_prefix}-worker-trigger"
  description = "Periodic trigger for Cloud Run worker job"
  schedule    = var.worker_cron
  region      = var.region

  http_target {
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.worker.name}:run"
    http_method = "POST"

    oauth_token {
      service_account_email = google_service_account.scheduler.email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }
}

