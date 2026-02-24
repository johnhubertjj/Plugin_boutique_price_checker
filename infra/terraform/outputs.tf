output "api_url" {
  description = "Cloud Run API URL"
  value       = google_cloud_run_v2_service.api.uri
}

output "cloudsql_connection_name" {
  description = "Cloud SQL connection string name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "artifact_repository" {
  description = "Artifact registry repository id"
  value       = google_artifact_registry_repository.docker_repo.id
}

output "app_service_account" {
  description = "Application service account email"
  value       = google_service_account.app.email
}

output "scheduler_service_account" {
  description = "Scheduler service account email"
  value       = google_service_account.scheduler.email
}

