# Implementation Plan

- [x] 1. Create Terraform directory structure and versions configuration
  - Create `infra/terraform/` directory
  - Create `versions.tf` with Terraform version constraint ">= 1.5, < 2.0"
  - Add required_providers block with google provider source "hashicorp/google" and version "~> 7.0"
  - Add provider "google" block that uses var.project_id and var.region
  - Add commented backend "gcs" block with instructions for optional remote state
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Create comprehensive variable definitions
  - Create `variables.tf` file
  - Define project_id variable (string, no default, with description)
  - Define region variable (string, default "europe-west1")
  - Define service_name variable (string, default "eduscale-engine")
  - Define repository_id variable (string, default "eduscale-engine-repo")
  - Define image_tag variable (string, default "latest")
  - Define service_version variable (string, default "0.1.0")
  - Define environment variable (string, default "prod")
  - Define min_instance_count variable (number, default 0)
  - Define max_instance_count variable (number, default 10)
  - Define cpu variable (string, default "1")
  - Define memory variable (string, default "512Mi")
  - Define container_port variable (number, default 8080)
  - Define allow_unauthenticated variable (bool, default true)
  - Add descriptive documentation for each variable
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

- [x] 3. Implement API enablement resources
  - Create `main.tf` file
  - Add google_project_service resource for "artifactregistry.googleapis.com"
  - Add google_project_service resource for "run.googleapis.com"
  - Set disable_on_destroy to false for both API resources
  - Use var.project_id for the project parameter
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Implement Artifact Registry repository resource
  - Add google_artifact_registry_repository resource named "eduscale_repo" to main.tf
  - Set location to var.region
  - Set repository_id to var.repository_id
  - Set format to "DOCKER"
  - Add description "Docker repository for EduScale Engine container images"
  - Add depends_on for google_project_service.artifact_registry
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 5. Implement Cloud Run v2 service resource with container configuration
  - Add google_cloud_run_v2_service resource named "eduscale_engine" to main.tf
  - Set name to var.service_name
  - Set location to var.region
  - Set ingress to "INGRESS_TRAFFIC_ALL"
  - Configure template.scaling with min_instance_count and max_instance_count from variables
  - Configure template.containers.image using "{region}-docker.pkg.dev/{project_id}/{repository_id}/{service_name}:{image_tag}"
  - Configure template.containers.ports with container_port from variable
  - Configure template.containers.resources.limits with cpu and memory from variables
  - Add depends_on for google_project_service.cloud_run and google_artifact_registry_repository.eduscale_repo
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 6. Configure Cloud Run environment variables
  - Add template.containers.env block for ENV variable using var.environment
  - Add template.containers.env block for SERVICE_NAME variable using var.service_name
  - Add template.containers.env block for SERVICE_VERSION variable using var.service_version
  - Add template.containers.env block for GCP_PROJECT_ID variable using var.project_id
  - Add template.containers.env block for GCP_REGION variable using var.region
  - Add template.containers.env block for GCP_RUN_SERVICE variable using var.service_name
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 7. Implement IAM policy for public access
  - Add google_cloud_run_v2_service_iam_member resource named "public_access" to main.tf
  - Use count meta-argument with condition var.allow_unauthenticated ? 1 : 0
  - Set location from google_cloud_run_v2_service.eduscale_engine.location
  - Set name from google_cloud_run_v2_service.eduscale_engine.name
  - Set role to "roles/run.invoker"
  - Set member to "allUsers"
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 8. Create output definitions
  - Create `outputs.tf` file
  - Define cloud_run_url output with value from google_cloud_run_v2_service.eduscale_engine.uri
  - Define artifact_registry_repository output with value "{region}-docker.pkg.dev/{project_id}/{repository_id}"
  - Define full_image_path output with complete image path
  - Define project_id output with value var.project_id
  - Define region output with value var.region
  - Define service_name output with value var.service_name
  - Add descriptions for all outputs
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_

- [x] 9. Create example variables file
  - Create `terraform.tfvars.example` file
  - Add placeholder value for project_id (e.g., "your-gcp-project-id")
  - Add example values for all configurable variables
  - Include comments explaining each variable
  - Show default values for reference
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 10. Create comprehensive README documentation
  - Create `README.md` in infra/terraform directory
  - Add introduction explaining purpose and provisioned resources
  - Document prerequisites (Terraform version, gcloud CLI, GCP project, IAM permissions)
  - Add quick start section with step-by-step instructions
  - Document how to configure variables using terraform.tfvars
  - Explain terraform init, plan, and apply commands
  - Add section on building and pushing Docker images separately from Terraform
  - Create table documenting all configuration variables with defaults and descriptions
  - Add section on testing deployment using health endpoint with curl example
  - Document how to update infrastructure and deploy new image tags
  - Add troubleshooting section for common errors (image not found, API not enabled, permissions)
  - Explain connection to FastAPI application (port 8080, /health endpoint, environment variables)
  - Add section on future enhancements (GCS, BigQuery, etc.)
  - Include architecture diagram showing resource relationships
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10_

- [x]* 11. Validate Terraform configuration
  - Run terraform fmt to format all .tf files
  - Run terraform validate to check syntax
  - Verify all variable references are correct
  - Check that resource dependencies are properly defined
  - Ensure no hardcoded values exist in configuration
  - Verify output references are correct
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8_
