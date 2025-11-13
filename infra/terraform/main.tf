# Enable Required Google Cloud APIs
resource "google_project_service" "artifact_registry" {
  project = var.project_id
  service = "artifactregistry.googleapis.com"

  disable_on_destroy = false
}

resource "google_project_service" "cloud_run" {
  project = var.project_id
  service = "run.googleapis.com"

  disable_on_destroy = false
}

resource "google_project_service" "storage" {
  project = var.project_id
  service = "storage.googleapis.com"

  disable_on_destroy = false
}

resource "google_project_service" "eventarc" {
  project = var.project_id
  service = "eventarc.googleapis.com"

  disable_on_destroy = false
}

# Artifact Registry Repository for Docker Images
resource "google_artifact_registry_repository" "jedouscale_repo" {
  location      = var.region
  repository_id = var.repository_id
  description   = "Docker repository for JedouScale Engine container images"
  format        = "DOCKER"

  # Ensure API is enabled before creating repository
  depends_on = [google_project_service.artifact_registry]
}

# GCS Bucket for File Uploads
resource "google_storage_bucket" "uploads" {
  name          = "${var.project_id}-eduscale-uploads"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = var.uploads_bucket_lifecycle_days
    }
    action {
      type = "Delete"
    }
  }

  versioning {
    enabled = false
  }

  depends_on = [google_project_service.storage]
}

# Data source to get project number for default compute service account
data "google_project" "project" {
  project_id = var.project_id
}

# Grant Cloud Run default service account access to bucket
# Cloud Run uses the default compute service account: PROJECT_NUMBER-compute@developer.gserviceaccount.com
resource "google_storage_bucket_iam_member" "cloud_run_object_admin" {
  bucket = google_storage_bucket.uploads.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Grant Eventarc service account access to bucket
# Eventarc needs to read bucket metadata to validate the trigger
resource "google_storage_bucket_iam_member" "eventarc_object_viewer" {
  bucket = google_storage_bucket.uploads.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.eventarc_trigger.email}"
}

# Service Account for GitHub Actions
resource "google_service_account" "github_actions" {
  account_id   = "github-actions"
  display_name = "GitHub Actions Service Account"
  description  = "Service account for GitHub Actions CI/CD pipeline"
}

# Grant Cloud Run Admin role to GitHub Actions service account
resource "google_project_iam_member" "github_actions_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Grant Artifact Registry Writer role to GitHub Actions service account
resource "google_project_iam_member" "github_actions_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Grant Service Account User role to GitHub Actions service account
resource "google_project_iam_member" "github_actions_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Create service account key for GitHub Actions
resource "google_service_account_key" "github_actions_key" {
  service_account_id = google_service_account.github_actions.name
}
