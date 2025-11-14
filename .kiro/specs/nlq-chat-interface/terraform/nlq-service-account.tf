# Service Account for NLQ Chat Interface
# This service account is used by the NLQ Chat Interface Cloud Run service
# to execute read-only BigQuery queries for natural language query functionality.

resource "google_service_account" "nlq_service" {
  account_id   = "nlq-service"
  display_name = "NLQ Service Account"
  description  = "Service account for NLQ Chat Interface with read-only BigQuery access"
  project      = var.project_id
}

# Grant NLQ Service permission to view BigQuery data (read-only)
# This role allows reading table data but NOT writing/modifying
resource "google_project_iam_member" "nlq_bigquery_data_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.nlq_service.email}"
}

# Grant NLQ Service permission to execute BigQuery jobs (run queries)
# Required to submit and execute SELECT queries
resource "google_project_iam_member" "nlq_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.nlq_service.email}"
}

# Output the service account email for Cloud Run configuration
output "nlq_service_account_email" {
  description = "Email of the NLQ service account for Cloud Run"
  value       = google_service_account.nlq_service.email
}

# Security Note:
# This service account has ONLY read-only access to BigQuery:
# - bigquery.dataViewer: Can read table data, schemas, and metadata (NO write/delete)
# - bigquery.jobUser: Can execute queries and create jobs (but limited by dataViewer)
# 
# This service account CANNOT:
# - Write, update, or delete table data (no dataEditor role)
# - Create, alter, or drop tables (no dataEditor role)
# - Access Cloud Storage buckets (no storage roles)
# - Invoke other services (no run.invoker roles)
#
# Use this service account for the NLQ Cloud Run service to ensure
# users can only query data, not modify it.

