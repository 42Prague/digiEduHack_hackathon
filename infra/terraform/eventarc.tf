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

  # Optional: Filter events by object name prefix
  # Only applied if event_filter_prefix is not empty
  dynamic "matching_criteria" {
    for_each = var.event_filter_prefix != "" ? [1] : []
    content {
      attribute = "bucket"
      value     = google_storage_bucket.uploads.name
      operator  = "match-path-pattern"
    }
  }

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
