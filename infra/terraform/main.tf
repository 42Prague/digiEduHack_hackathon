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

# Artifact Registry Repository for Docker Images
resource "google_artifact_registry_repository" "eduscale_repo" {
  location      = var.region
  repository_id = var.repository_id
  description   = "Docker repository for EduScale Engine container images"
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

# Grant Cloud Run service account access to bucket
resource "google_storage_bucket_iam_member" "cloud_run_object_admin" {
  bucket = google_storage_bucket.uploads.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_cloud_run_v2_service.eduscale_engine.template[0].service_account}"
}

# Cloud Run Service (v2)
resource "google_cloud_run_v2_service" "eduscale_engine" {
  name               = var.service_name
  location           = var.region
  ingress            = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    # Scaling configuration
    scaling {
      min_instance_count = var.min_instance_count
      max_instance_count = var.max_instance_count
    }

    containers {
      # Container image from Artifact Registry
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_id}/${var.service_name}:${var.image_tag}"

      # Container port
      ports {
        container_port = var.container_port
      }

      # Resource limits
      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }

      # Environment variables matching the FastAPI application
      env {
        name  = "ENV"
        value = var.environment
      }

      env {
        name  = "SERVICE_NAME"
        value = var.service_name
      }

      env {
        name  = "SERVICE_VERSION"
        value = var.service_version
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "GCP_REGION"
        value = var.region
      }

      env {
        name  = "GCP_RUN_SERVICE"
        value = var.service_name
      }

      # Storage configuration
      env {
        name  = "STORAGE_BACKEND"
        value = "gcs"
      }

      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.uploads.name
      }

      env {
        name  = "MAX_UPLOAD_MB"
        value = "50"
      }

      env {
        name  = "ALLOWED_UPLOAD_MIME_TYPES"
        value = "text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/json,audio/mpeg,audio/wav"
      }
    }
  }

  # Ensure API is enabled and repository exists before creating service
  depends_on = [
    google_project_service.cloud_run,
    google_artifact_registry_repository.eduscale_repo
  ]
}

# IAM Policy to Allow Unauthenticated Access
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  count = var.allow_unauthenticated ? 1 : 0

  location = google_cloud_run_v2_service.eduscale_engine.location
  name     = google_cloud_run_v2_service.eduscale_engine.name
  role     = "roles/run.invoker"
  member   = "allUsers"
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
