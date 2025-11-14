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

- [ ] 11. Add BigQuery variables to configuration
  - Add bigquery_dataset_id variable to variables.tf (string, default "jedouscale_core")
  - Add bigquery_staging_dataset_id variable (string, default "jedouscale_staging")
  - Add bigquery_staging_table_expiration_days variable (number, default 7)
  - Add descriptions for all BigQuery variables
  - Update terraform.tfvars.example with BigQuery variable examples
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [ ] 12. Create BigQuery infrastructure configuration
  - Create `bigquery.tf` file in infra/terraform/
  - Add google_project_service resource for "bigquery.googleapis.com"
  - Set disable_on_destroy to false for BigQuery API resource
  - _Requirements: 13.1_

- [ ] 13. Implement BigQuery datasets
  - Add google_bigquery_dataset resource for core dataset in bigquery.tf
  - Set dataset_id to var.bigquery_dataset_id
  - Set location to var.region
  - Add description "Core dataset for EduScale data warehouse (dimensions and facts)"
  - Add depends_on for google_project_service.bigquery
  - Add google_bigquery_dataset resource for staging dataset
  - Set dataset_id to var.bigquery_staging_dataset_id
  - Set location to var.region
  - Add description "Staging dataset for temporary data loading operations"
  - Set default_table_expiration_ms using var.bigquery_staging_table_expiration_days
  - Add depends_on for google_project_service.bigquery
  - _Requirements: 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8_

- [ ] 14. Implement dimension tables
  - Add google_bigquery_table resource for dim_region in bigquery.tf
  - Define schema with columns: region_id (STRING, REQUIRED), region_name (STRING), from_date (DATE), to_date (DATE)
  - Add google_bigquery_table resource for dim_school
  - Define schema with columns: school_name (STRING, REQUIRED), region_id (STRING), from_date (DATE), to_date (DATE)
  - Add google_bigquery_table resource for dim_time
  - Define schema with columns: date (DATE, REQUIRED), year (INTEGER), month (INTEGER), day (INTEGER), quarter (INTEGER), day_of_week (INTEGER)
  - Use jsonencode for schema definitions
  - Reference google_bigquery_dataset.core.dataset_id for all dimension tables
  - _Requirements: 14.1, 14.9, 14.10_

- [ ] 15. Implement fact tables with partitioning and clustering
  - Add google_bigquery_table resource for fact_assessment in bigquery.tf
  - Define schema with columns: date (DATE, REQUIRED), region_id (STRING, REQUIRED), school_name (STRING), student_id (STRING), student_name (STRING), subject (STRING), test_score (FLOAT), file_id (STRING, REQUIRED), ingest_timestamp (TIMESTAMP, REQUIRED)
  - Add time_partitioning block with type "DAY" and field "date"
  - Add clustering with ["region_id"]
  - Add google_bigquery_table resource for fact_intervention
  - Define schema with columns: date (DATE, REQUIRED), region_id (STRING, REQUIRED), school_name (STRING), intervention_type (STRING), participants_count (INTEGER), file_id (STRING, REQUIRED), ingest_timestamp (TIMESTAMP, REQUIRED)
  - Add time_partitioning block with type "DAY" and field "date"
  - Add clustering with ["region_id"]
  - Reference google_bigquery_dataset.core.dataset_id for all fact tables
  - _Requirements: 14.2, 14.5, 14.6, 14.9, 14.10_

- [ ] 16. Implement observations and ingest_runs tables
  - Add google_bigquery_table resource for observations in bigquery.tf
  - Define schema with columns: file_id (STRING, REQUIRED), region_id (STRING, REQUIRED), observation_text (STRING), source_table_type (STRING), ingest_timestamp (TIMESTAMP, REQUIRED)
  - Add time_partitioning block with type "DAY" and field "ingest_timestamp"
  - Add clustering with ["region_id"]
  - Add google_bigquery_table resource for ingest_runs
  - Define schema with columns: file_id (STRING, REQUIRED), region_id (STRING, REQUIRED), status (STRING, REQUIRED), step (STRING), error_message (STRING), created_at (TIMESTAMP, REQUIRED), updated_at (TIMESTAMP, REQUIRED)
  - Add time_partitioning block with type "DAY" and field "created_at"
  - Add clustering with ["region_id", "status"]
  - Reference google_bigquery_dataset.core.dataset_id for both tables
  - _Requirements: 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9, 14.10_

- [ ] 17. Add BigQuery outputs
  - Add bigquery_dataset_id output to outputs.tf with value from google_bigquery_dataset.core.dataset_id
  - Add bigquery_staging_dataset_id output with value from google_bigquery_dataset.staging.dataset_id
  - Add bigquery_dataset_location output with value from google_bigquery_dataset.core.location
  - Add bigquery_tables output with list of created table IDs
  - Add descriptions for all BigQuery outputs
  - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

- [ ] 18. Update README with BigQuery documentation
  - Add BigQuery datasets and tables to provisioned resources list in README.md
  - Document BigQuery variables in configuration reference table
  - Add section explaining BigQuery data warehouse structure
  - Document dimension tables (dim_region, dim_school, dim_time)
  - Document fact tables (fact_assessment, fact_intervention)
  - Document observations and ingest_runs tables
  - Explain partitioning and clustering strategy
  - Add example queries for testing BigQuery tables
  - Document integration with Tabular service
  - _Requirements: 11.1, 11.2, 11.7_

- [ ] 19. Add Tabular Service configuration variables
  - Add tabular_service_name variable to variables.tf (string, default "tabular-service")
  - Add description "Name of the Tabular Cloud Run service"
  - Update terraform.tfvars.example with tabular_service_name example
  - _Requirements: 19.1, 19.2, 19.3, 19.4_

- [ ] 20. Create Tabular Service service account
  - Add google_service_account resource named "tabular_service" to main.tf or iam.tf
  - Set account_id to "tabular-service"
  - Set display_name to "Tabular Service Account"
  - Set description to "Service account for Tabular Service running on Cloud Run"
  - _Requirements: 17.1, 17.2, 17.3, 17.4_

- [ ] 21. Grant Tabular Service IAM permissions
  - Add google_storage_bucket_iam_member resource for Storage Object Viewer role
  - Grant tabular_service service account access to uploads bucket
  - Add google_project_iam_member resource for BigQuery Data Editor role
  - Grant tabular_service service account bigquery.dataEditor at project level
  - Add google_project_iam_member resource for BigQuery Job User role
  - Grant tabular_service service account bigquery.jobUser at project level
  - _Requirements: 17.5, 17.6, 17.7_

- [ ] 22. Add Eventarc trigger for text files
  - Add data source google_cloud_run_service for Tabular service in eventarc.tf
  - Use count with var.enable_eventarc condition
  - Reference var.tabular_service_name for service name
  - Add google_cloud_run_service_iam_member for Eventarc → Tabular invoker permission
  - Grant eventarc_trigger service account roles/run.invoker on Tabular service
  - Add google_eventarc_trigger resource named "text_trigger"
  - Configure matching_criteria for type "google.cloud.storage.object.v1.finalized"
  - Configure matching_criteria for bucket name
  - Configure matching_criteria for object name pattern "text/" with operator "match-path-pattern"
  - Set destination to Tabular Cloud Run service
  - Use eventarc_trigger service account
  - Add depends_on for eventarc API, IAM permissions, and storage bucket
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 18.8, 18.9_

- [ ] 23. Update README with Tabular Service documentation
  - Add Tabular Service to architecture overview
  - Document tabular_service_name variable
  - Document Tabular Service service account and permissions
  - Document text files Eventarc trigger
  - Add deployment order notes (deploy Tabular via GitHub Actions before enabling trigger)
  - Document event flow: Transformer → GCS → Eventarc → Tabular → BigQuery
  - _Requirements: 17.1, 18.1, 19.1_

- [x]* 24. Validate Terraform configuration
  - Run terraform fmt to format all .tf files
  - Run terraform validate to check syntax
  - Verify all variable references are correct
  - Check that resource dependencies are properly defined
  - Ensure no hardcoded values exist in configuration
  - Verify output references are correct
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8_
