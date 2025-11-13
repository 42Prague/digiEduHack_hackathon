# Core GCP Configuration
variable "project_id" {
  description = "The GCP project ID where resources will be created"
  type        = string
  # No default - must be explicitly provided
}

variable "region" {
  description = "The GCP region for resources (e.g., europe-west1)"
  type        = string
  default     = "europe-west1"
}

# Service Configuration
variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
  default     = "jedouscale-engine"
}

variable "repository_id" {
  description = "The Artifact Registry repository ID for Docker images"
  type        = string
  default     = "jedouscale-engine-repo"
}

variable "image_tag" {
  description = "The Docker image tag to deploy"
  type        = string
  default     = "latest"
}

# Cloud Run Configuration
variable "service_version" {
  description = "The service version to set in environment variables"
  type        = string
  default     = "0.1.0"
}

variable "environment" {
  description = "The deployment environment (e.g., prod, dev, staging)"
  type        = string
  default     = "prod"
}

variable "min_instance_count" {
  description = "Minimum number of Cloud Run instances (0 for cost savings)"
  type        = number
  default     = 0
}

variable "max_instance_count" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 10
}

variable "cpu" {
  description = "CPU allocation for Cloud Run container (e.g., '1', '2')"
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory allocation for Cloud Run container (e.g., '512Mi', '1Gi')"
  type        = string
  default     = "512Mi"
}

variable "container_port" {
  description = "The port the container listens on"
  type        = number
  default     = 8080
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to the Cloud Run service"
  type        = bool
  default     = true
}

# Storage Configuration
variable "uploads_bucket_lifecycle_days" {
  description = "Number of days before uploaded files are deleted"
  type        = number
  default     = 90
}

# Eventarc Configuration
variable "mime_decoder_service_name" {
  description = "The name of the MIME Decoder Cloud Run service"
  type        = string
  default     = "mime-decoder"
}

variable "enable_eventarc" {
  description = "Enable Eventarc trigger and MIME Decoder IAM. Set to false on first run, then true after deploying mime-decoder via GitHub Actions."
  type        = bool
  default     = false
}

variable "eventarc_trigger_name" {
  description = "The name of the Eventarc trigger for Cloud Storage events"
  type        = string
  default     = "storage-upload-trigger"
}

variable "event_filter_prefix" {
  description = "Optional prefix filter for Cloud Storage objects (e.g., 'uploads/'). Leave empty to process all files."
  type        = string
  default     = ""
}

# Monitoring and Alerting Configuration
variable "enable_monitoring_alerts" {
  description = "Enable Cloud Monitoring alert policies for Eventarc"
  type        = bool
  default     = false
}

variable "alert_email" {
  description = "Email address for monitoring alerts. Leave empty to disable email notifications."
  type        = string
  default     = ""
}

variable "enable_monitoring_dashboard" {
  description = "Create Cloud Monitoring dashboard for Eventarc integration"
  type        = bool
  default     = true
}
