# Terraform and Provider Version Constraints
terraform {
  required_version = ">= 1.5, < 2.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }

  # Optional: Uncomment to use remote state in GCS
  # Requires a pre-created GCS bucket
  # backend "gcs" {
  #   bucket = "your-terraform-state-bucket"
  #   prefix = "eduscale-engine/terraform/state"
  # }
}

# Google Cloud Provider Configuration
provider "google" {
  project = var.project_id
  region  = var.region
}
