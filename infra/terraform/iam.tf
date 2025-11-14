# Service Account for Eventarc Trigger
# This service account is used by Eventarc to invoke the MIME Decoder Cloud Run service
# when Cloud Storage OBJECT_FINALIZE events occur.
resource "google_service_account" "eventarc_trigger" {
  account_id   = "eventarc-trigger-sa"
  display_name = "Eventarc Trigger Service Account"
  description  = "Service account for Eventarc to invoke MIME Decoder Cloud Run service"
  project      = var.project_id
}

# Grant Eventarc Event Receiver role at project level
# Required for Eventarc to receive and process events from Cloud Storage
resource "google_project_iam_member" "eventarc_receiver" {
  project = var.project_id
  role    = "roles/eventarc.eventReceiver"
  member  = "serviceAccount:${google_service_account.eventarc_trigger.email}"
}

# Note: Cloud Run Invoker role for MIME Decoder service will be added in eventarc.tf
# after the MIME Decoder Cloud Run service is defined, to avoid circular dependencies.

# Grant Cloud Storage service agent permission to publish to Pub/Sub
# Required for Eventarc to receive Cloud Storage events via Pub/Sub
# The Cloud Storage service agent has the format: service-PROJECT_NUMBER@gs-project-accounts.iam.gserviceaccount.com
resource "google_project_iam_member" "gcs_pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:service-${data.google_project.project.number}@gs-project-accounts.iam.gserviceaccount.com"
}

# Service Account for Tabular Service
# This service account is used by the Tabular Service Cloud Run to access GCS and BigQuery
resource "google_service_account" "tabular_service" {
  account_id   = "tabular-service"
  display_name = "Tabular Service Account"
  description  = "Service account for Tabular Service running on Cloud Run"
  project      = var.project_id
}

# Grant Tabular Service access to read text files from Cloud Storage
resource "google_storage_bucket_iam_member" "tabular_storage_viewer" {
  bucket = google_storage_bucket.uploads.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.tabular_service.email}"
}

# Grant Tabular Service permission to write to BigQuery tables
resource "google_project_iam_member" "tabular_bigquery_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.tabular_service.email}"
}

# Grant Tabular Service permission to execute BigQuery jobs
resource "google_project_iam_member" "tabular_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.tabular_service.email}"
}
