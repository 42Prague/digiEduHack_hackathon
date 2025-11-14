# NOTE: The MIME Decoder Cloud Run service is deployed via GitHub Actions
# See .github/workflows/deploy-mime-decoder.yml for deployment configuration
# Terraform only manages IAM permissions and infrastructure dependencies
#
# DEPLOYMENT ORDER:
# 1. Run Terraform with enable_eventarc=false (creates base infrastructure)
# 2. Deploy mime-decoder via GitHub Actions
# 3. Run Terraform with enable_eventarc=true (creates IAM and Eventarc trigger)

# Data source to reference the existing MIME Decoder service
# Only created when enable_eventarc is true
data "google_cloud_run_service" "mime_decoder" {
  count    = var.enable_eventarc ? 1 : 0
  name     = var.mime_decoder_service_name
  location = var.region
  project  = var.project_id
}

# Grant Eventarc service account permission to invoke MIME Decoder
resource "google_cloud_run_service_iam_member" "eventarc_invoker" {
  count    = var.enable_eventarc ? 1 : 0
  service  = data.google_cloud_run_service.mime_decoder[0].name
  location = data.google_cloud_run_service.mime_decoder[0].location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.eventarc_trigger.email}"
  project  = var.project_id
}

# Data source to reference the existing Transformer service
# Only created when enable_eventarc is true
data "google_cloud_run_service" "transformer" {
  count    = var.enable_eventarc ? 1 : 0
  name     = var.transformer_service_name
  location = var.region
  project  = var.project_id
}

# Grant cloud-run-engine service account permission to invoke Transformer
# This allows MIME Decoder (running as cloud-run-engine) to call Transformer
resource "google_cloud_run_service_iam_member" "transformer_invoker" {
  count    = var.enable_eventarc ? 1 : 0
  service  = data.google_cloud_run_service.transformer[0].name
  location = data.google_cloud_run_service.transformer[0].location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.cloud_run_engine.email}"
  project  = var.project_id
}

# Allow unauthenticated access to MIME Decoder if configured
# Note: In production, this should be false and only Eventarc should invoke the service
resource "google_cloud_run_service_iam_member" "mime_decoder_public_access" {
  count    = var.enable_eventarc && var.allow_unauthenticated ? 1 : 0
  service  = data.google_cloud_run_service.mime_decoder[0].name
  location = data.google_cloud_run_service.mime_decoder[0].location
  role     = "roles/run.invoker"
  member   = "allUsers"
  project  = var.project_id
}

# Eventarc Trigger for Cloud Storage OBJECT_FINALIZE events
# Automatically triggers MIME Decoder when files are uploaded to the bucket
resource "google_eventarc_trigger" "storage_trigger" {
  count    = var.enable_eventarc ? 1 : 0
  name     = var.eventarc_trigger_name
  location = var.region
  project  = var.project_id

  # Subscribe to Cloud Storage OBJECT_FINALIZE events
  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }

  # Filter events by bucket name
  matching_criteria {
    attribute = "bucket"
    value     = google_storage_bucket.uploads.name
  }

  # Note: Direct Cloud Storage events only support filtering by 'type' and 'bucket'
  # Path-based filtering (e.g., uploads/* vs text/*) must be done in the service code
  # The MIME Decoder service validates paths and returns HTTP 400 for invalid paths

  # Route events to MIME Decoder Cloud Run service
  destination {
    cloud_run_service {
      service = data.google_cloud_run_service.mime_decoder[0].name
      region  = data.google_cloud_run_service.mime_decoder[0].location
    }
  }

  # Retry policy for failed event deliveries
  # Eventarc automatically retries failed deliveries with exponential backoff
  # Default behavior: 5 retries with intervals: 10s, 20s, 40s, 80s, 160s
  # For Cloud Run destinations, retries occur when:
  # - Service returns 5xx status codes
  # - Service times out (timeout_seconds in Cloud Run service)
  # - Service is unavailable
  # Note: 4xx errors are NOT retried as they indicate client errors

  # Use Eventarc service account for invoking Cloud Run
  service_account = google_service_account.eventarc_trigger.email

  # Ensure all dependencies are ready
  depends_on = [
    google_project_service.eventarc,
    google_cloud_run_service_iam_member.eventarc_invoker,
    google_storage_bucket.uploads
  ]
}

# Data source to reference the existing Tabular service
# Only created when enable_text_trigger is true
data "google_cloud_run_service" "tabular" {
  count    = var.enable_text_trigger ? 1 : 0
  name     = var.tabular_service_name
  location = var.region
  project  = var.project_id
}

# Grant Eventarc service account permission to invoke Tabular Service
resource "google_cloud_run_service_iam_member" "eventarc_tabular_invoker" {
  count    = var.enable_text_trigger ? 1 : 0
  service  = data.google_cloud_run_service.tabular[0].name
  location = data.google_cloud_run_service.tabular[0].location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.eventarc_trigger.email}"
  project  = var.project_id
}

# Eventarc Trigger for text files
# Automatically triggers Tabular Service when Transformer produces text output
# NOTE: Set enable_text_trigger=true only after Tabular service is deployed
resource "google_eventarc_trigger" "text_trigger" {
  count    = var.enable_text_trigger ? 1 : 0
  name     = "text-files-trigger"
  location = var.region
  project  = var.project_id

  # Subscribe to Cloud Storage OBJECT_FINALIZE events
  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }

  # Filter events by bucket name
  matching_criteria {
    attribute = "bucket"
    value     = google_storage_bucket.uploads.name
  }

  # Note: Direct Cloud Storage events only support filtering by 'type' and 'bucket'
  # Path-based filtering must be done in the Tabular service code

  # Route events to Tabular Cloud Run service
  destination {
    cloud_run_service {
      service = data.google_cloud_run_service.tabular[0].name
      region  = data.google_cloud_run_service.tabular[0].location
    }
  }

  # Use Eventarc service account for invoking Cloud Run
  service_account = google_service_account.eventarc_trigger.email

  # Ensure all dependencies are ready
  depends_on = [
    google_project_service.eventarc,
    google_cloud_run_service_iam_member.eventarc_tabular_invoker,
    google_storage_bucket.uploads
  ]
}
