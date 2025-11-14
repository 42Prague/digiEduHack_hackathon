# Artifact Registry Repository URL
output "artifact_registry_repository" {
  description = "The full Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_id}"
}

# Full Image Path
output "full_image_path" {
  description = "The complete image path used by Cloud Run"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_id}/${var.service_name}:${var.image_tag}"
}

# Project ID (for confirmation)
output "project_id" {
  description = "The GCP project ID"
  value       = var.project_id
}

# Region (for confirmation)
output "region" {
  description = "The GCP region"
  value       = var.region
}

# Service Name (for confirmation)
output "service_name" {
  description = "The Cloud Run service name"
  value       = var.service_name
}

# Cloud Run Engine Service Account Email
output "cloud_run_engine_service_account_email" {
  description = "The email of the Cloud Run Engine service account"
  value       = google_service_account.cloud_run_engine.email
}

# GitHub Actions Service Account Email
output "github_actions_service_account_email" {
  description = "The email of the GitHub Actions service account"
  value       = google_service_account.github_actions.email
}

# GitHub Actions Service Account Key (sensitive)
output "github_actions_service_account_key" {
  description = "The private key for GitHub Actions service account (base64 encoded)"
  value       = google_service_account_key.github_actions_key.private_key
  sensitive   = true
}

# Uploads Bucket Name
output "uploads_bucket_name" {
  description = "Name of the GCS bucket for file uploads"
  value       = google_storage_bucket.uploads.name
}

# MIME Decoder Service Information
# Note: Service is deployed via GitHub Actions, not Terraform
output "mime_decoder_service_name" {
  description = "The name of the MIME Decoder Cloud Run service"
  value       = var.mime_decoder_service_name
}

# Eventarc Trigger Information
output "eventarc_trigger_name" {
  description = "The name of the Eventarc trigger for Cloud Storage events"
  value       = var.enable_eventarc ? google_eventarc_trigger.storage_trigger[0].name : "Not created - set enable_eventarc=true"
}

output "eventarc_trigger_id" {
  description = "The full resource ID of the Eventarc trigger"
  value       = var.enable_eventarc ? google_eventarc_trigger.storage_trigger[0].id : "Not created - set enable_eventarc=true"
}

# Eventarc Service Account
output "eventarc_service_account_email" {
  description = "The email of the Eventarc trigger service account"
  value       = google_service_account.eventarc_trigger.email
}

# BigQuery Outputs
output "bigquery_dataset_id" {
  description = "The ID of the core BigQuery dataset"
  value       = google_bigquery_dataset.core.dataset_id
}

output "bigquery_staging_dataset_id" {
  description = "The ID of the staging BigQuery dataset"
  value       = google_bigquery_dataset.staging.dataset_id
}

output "bigquery_dataset_location" {
  description = "The location of the BigQuery datasets"
  value       = google_bigquery_dataset.core.location
}

output "bigquery_tables" {
  description = "List of created BigQuery table IDs"
  value = [
    google_bigquery_table.dim_region.table_id,
    google_bigquery_table.dim_school.table_id,
    google_bigquery_table.dim_time.table_id,
    google_bigquery_table.fact_assessment.table_id,
    google_bigquery_table.fact_intervention.table_id,
    google_bigquery_table.observations.table_id,
    google_bigquery_table.ingest_runs.table_id
  ]
}
