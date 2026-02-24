variable "project_id" {
  description = "GCP project id"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "name_prefix" {
  description = "Resource name prefix"
  type        = string
  default     = "plugin-boutique"
}

variable "artifact_repository" {
  description = "Artifact Registry repository id"
  type        = string
  default     = "plugin-boutique"
}

variable "api_service_name" {
  description = "Cloud Run API service name"
  type        = string
  default     = "plugin-boutique-api"
}

variable "worker_job_name" {
  description = "Cloud Run worker job name"
  type        = string
  default     = "plugin-boutique-worker"
}

variable "api_image" {
  description = "Container image URI for API"
  type        = string
}

variable "worker_image" {
  description = "Container image URI for worker"
  type        = string
}

variable "cors_allowed_origins" {
  description = "Comma-separated CORS origins"
  type        = string
  default     = ""
}

variable "database_name" {
  description = "Cloud SQL database name"
  type        = string
  default     = "plugin_boutique"
}

variable "database_user" {
  description = "Cloud SQL username"
  type        = string
  default     = "plugin_boutique"
}

variable "cloudsql_tier" {
  description = "Cloud SQL machine tier"
  type        = string
  default     = "db-custom-1-3840"
}

variable "deletion_protection" {
  description = "Enable deletion protection on Cloud SQL instance"
  type        = bool
  default     = true
}

variable "worker_cron" {
  description = "Cron schedule for worker trigger"
  type        = string
  default     = "*/10 * * * *"
}

