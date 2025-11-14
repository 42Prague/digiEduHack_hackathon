# Eventarc trigger for Tabular Service
# Triggers when ANY file is created in GCS uploads bucket
# Filtering by path (text/*.txt) is done in the Cloud Run service code

resource "google_eventarc_trigger" "tabular_text_files" {
  count    = var.enable_text_trigger ? 1 : 0
  name     = "tabular-text-files-trigger"
  location = var.region
  project  = var.project_id

  # Match all finalized objects in the uploads bucket
  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }

  matching_criteria {
    attribute = "bucket"
    value     = google_storage_bucket.uploads.name
  }

  # Note: Path filtering (text/*.txt) is handled in the service code
  # GCS direct events only support 'type' and 'bucket' attributes

  # Route to Tabular Service (deployed separately via GitHub)
  destination {
    cloud_run_service {
      service = var.tabular_service_name
      region  = var.region
      path    = "/"
    }
  }

  # Service account for Eventarc
  service_account = google_service_account.eventarc_trigger.email

  labels = {
    service = "tabular"
    trigger = "text-files"
  }
}

# Allow Eventarc to invoke Tabular Service
resource "google_cloud_run_service_iam_member" "tabular_eventarc_invoker" {
  count    = var.enable_text_trigger ? 1 : 0
  service  = var.tabular_service_name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.eventarc_trigger.email}"
}

output "tabular_eventarc_trigger_name" {
  description = "Name of the Eventarc trigger for Tabular Service"
  value       = var.enable_text_trigger ? google_eventarc_trigger.tabular_text_files[0].name : null
}
