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
