# Requirements Document

## Introduction

This specification defines the Terraform infrastructure-as-code configuration for provisioning Google Cloud Platform (GCP) resources for the EduScale Engine service. The Terraform configuration automates the creation of Artifact Registry for Docker image storage and Cloud Run for serverless container deployment. This infrastructure enables developers to deploy the FastAPI-based EduScale Engine application to GCP with a single command, following modern cloud-native best practices.

## Glossary

- **Terraform Configuration**: Infrastructure-as-code files written in HashiCorp Configuration Language (HCL) that define GCP resources
- **Artifact Registry**: Google Cloud's managed Docker container registry service for storing and managing container images
- **Cloud Run Service**: Google Cloud's fully managed serverless platform for running containerized applications
- **Terraform Provider**: A plugin that enables Terraform to interact with cloud platform APIs (Google Cloud in this case)
- **Terraform Variables**: Configurable parameters that allow customization of infrastructure without modifying code
- **Terraform Outputs**: Values exported after infrastructure creation for use in other tools or documentation
- **Terraform State**: A file tracking the current state of managed infrastructure resources
- **IAM Policy**: Identity and Access Management rules controlling who can access GCP resources
- **API Enablement**: The process of activating Google Cloud service APIs before using them

## Requirements

### Requirement 1

**User Story:** As a DevOps engineer, I want Terraform version constraints and provider configuration, so that I can ensure consistent infrastructure deployments across different environments

#### Acceptance Criteria

1. THE Terraform Configuration SHALL specify a required Terraform version constraint of ">= 1.5, < 2.0"
2. THE Terraform Configuration SHALL declare the Google Cloud provider with source "hashicorp/google" and version constraint "~> 7.0"
3. THE Terraform Configuration SHALL define a google provider block that uses variables for project_id and region
4. THE Terraform Configuration SHALL include a versions.tf file containing all version constraints and provider declarations
5. THE Terraform Configuration SHALL NOT hardcode project_id or region values in the provider configuration

### Requirement 2

**User Story:** As a developer, I want configurable Terraform variables with sensible defaults, so that I can easily customize infrastructure without modifying code

#### Acceptance Criteria

1. THE Terraform Configuration SHALL define a project_id variable of type string with no default value
2. THE Terraform Configuration SHALL define a region variable with default value "europe-west1"
3. THE Terraform Configuration SHALL define a service_name variable with default value "eduscale-engine"
4. THE Terraform Configuration SHALL define a repository_id variable with default value "eduscale-engine-repo"
5. THE Terraform Configuration SHALL define an image_tag variable with default value "latest"
6. THE Terraform Configuration SHALL define variables for service_version, environment, min_instance_count, max_instance_count, cpu, memory, container_port, and allow_unauthenticated
7. THE Terraform Configuration SHALL provide descriptive documentation for each variable
8. THE Terraform Configuration SHALL include a variables.tf file containing all variable definitions

### Requirement 3

**User Story:** As a DevOps engineer, I want Terraform to enable required GCP APIs automatically, so that I don't have to manually enable services before deployment

#### Acceptance Criteria

1. THE Terraform Configuration SHALL create a google_project_service resource for "artifactregistry.googleapis.com"
2. THE Terraform Configuration SHALL create a google_project_service resource for "run.googleapis.com"
3. THE Terraform Configuration SHALL set disable_on_destroy to false for API enablement resources
4. THE Terraform Configuration SHALL use the project_id variable for API enablement resources
5. WHEN Terraform applies the configuration, THE Terraform Configuration SHALL enable APIs before creating dependent resources

### Requirement 4

**User Story:** As a DevOps engineer, I want an Artifact Registry repository provisioned via Terraform, so that I can store Docker images for the EduScale Engine service

#### Acceptance Criteria

1. THE Terraform Configuration SHALL create a google_artifact_registry_repository resource
2. THE Terraform Configuration SHALL set the repository location to the value of the region variable
3. THE Terraform Configuration SHALL set the repository_id to the value of the repository_id variable
4. THE Terraform Configuration SHALL set the format to "DOCKER"
5. THE Terraform Configuration SHALL include a description "Docker repository for EduScale Engine container images"
6. THE Terraform Configuration SHALL declare a dependency on the Artifact Registry API enablement resource

### Requirement 5

**User Story:** As a DevOps engineer, I want a Cloud Run service provisioned via Terraform, so that I can deploy the containerized FastAPI application

#### Acceptance Criteria

1. THE Terraform Configuration SHALL create a google_cloud_run_v2_service resource
2. THE Terraform Configuration SHALL set the service name to the value of the service_name variable
3. THE Terraform Configuration SHALL set the location to the value of the region variable
4. THE Terraform Configuration SHALL set ingress to "INGRESS_TRAFFIC_ALL"
5. THE Terraform Configuration SHALL configure the container image as "{region}-docker.pkg.dev/{project_id}/{repository_id}/{service_name}:{image_tag}"
6. THE Terraform Configuration SHALL declare dependencies on both the Cloud Run API and Artifact Registry repository resources

### Requirement 6

**User Story:** As a DevOps engineer, I want Cloud Run scaling configuration managed by Terraform, so that I can control cost and performance

#### Acceptance Criteria

1. THE Terraform Configuration SHALL configure min_instance_count using the min_instance_count variable with default value 0
2. THE Terraform Configuration SHALL configure max_instance_count using the max_instance_count variable with default value 10
3. THE Terraform Configuration SHALL configure CPU allocation using the cpu variable with default value "1"
4. THE Terraform Configuration SHALL configure memory allocation using the memory variable with default value "512Mi"
5. THE Terraform Configuration SHALL configure the container port using the container_port variable with default value 8080

### Requirement 7

**User Story:** As a developer, I want Cloud Run environment variables configured via Terraform, so that the FastAPI application receives correct configuration

#### Acceptance Criteria

1. THE Terraform Configuration SHALL set an ENV environment variable to the value of the environment variable
2. THE Terraform Configuration SHALL set a SERVICE_NAME environment variable to the value of the service_name variable
3. THE Terraform Configuration SHALL set a SERVICE_VERSION environment variable to the value of the service_version variable
4. THE Terraform Configuration SHALL set a GCP_PROJECT_ID environment variable to the value of the project_id variable
5. THE Terraform Configuration SHALL set a GCP_REGION environment variable to the value of the region variable
6. THE Terraform Configuration SHALL set a GCP_RUN_SERVICE environment variable to the value of the service_name variable

### Requirement 8

**User Story:** As a developer, I want public access to the Cloud Run service configured via Terraform, so that the health endpoint is accessible without authentication

#### Acceptance Criteria

1. THE Terraform Configuration SHALL create a google_cloud_run_v2_service_iam_member resource
2. WHEN the allow_unauthenticated variable is true, THE Terraform Configuration SHALL grant the "roles/run.invoker" role to "allUsers"
3. THE Terraform Configuration SHALL use conditional creation based on the allow_unauthenticated variable value
4. THE Terraform Configuration SHALL reference the Cloud Run service location and name from the service resource
5. WHEN the allow_unauthenticated variable is false, THE Terraform Configuration SHALL NOT create the IAM member resource

### Requirement 9

**User Story:** As a developer, I want Terraform outputs for key infrastructure values, so that I can easily access service URLs and repository paths

#### Acceptance Criteria

1. THE Terraform Configuration SHALL output cloud_run_url containing the Cloud Run service URI
2. THE Terraform Configuration SHALL output artifact_registry_repository containing the full repository URL
3. THE Terraform Configuration SHALL output full_image_path containing the complete image path used by Cloud Run
4. THE Terraform Configuration SHALL output project_id for confirmation
5. THE Terraform Configuration SHALL output region for confirmation
6. THE Terraform Configuration SHALL output service_name for confirmation
7. THE Terraform Configuration SHALL include descriptions for all outputs
8. THE Terraform Configuration SHALL include an outputs.tf file containing all output definitions

### Requirement 10

**User Story:** As a developer, I want an example variables file, so that I can quickly configure Terraform for my GCP project

#### Acceptance Criteria

1. THE Terraform Configuration SHALL provide a terraform.tfvars.example file
2. THE Terraform Configuration SHALL include a placeholder value for project_id in the example file
3. THE Terraform Configuration SHALL include example values for all configurable variables
4. THE Terraform Configuration SHALL include comments explaining each variable in the example file
5. WHEN a developer copies terraform.tfvars.example to terraform.tfvars, THE Terraform Configuration SHALL be ready to use after updating project_id

### Requirement 11

**User Story:** As a new developer, I want comprehensive README documentation for the Terraform configuration, so that I can understand and use the infrastructure code

#### Acceptance Criteria

1. THE Terraform Configuration SHALL provide a README.md file in the infra/terraform directory
2. THE Terraform Configuration SHALL document the purpose of the Terraform configuration
3. THE Terraform Configuration SHALL list prerequisites including Terraform version, gcloud CLI, GCP project, and IAM permissions
4. THE Terraform Configuration SHALL provide step-by-step quick start instructions
5. THE Terraform Configuration SHALL explain how to build and push Docker images separately from Terraform
6. THE Terraform Configuration SHALL document all configuration variables in a table format
7. THE Terraform Configuration SHALL explain how to test the deployment using the health endpoint
8. THE Terraform Configuration SHALL document how to update infrastructure and deploy new image tags
9. THE Terraform Configuration SHALL include troubleshooting guidance for common errors
10. THE Terraform Configuration SHALL explain the connection to the FastAPI application

### Requirement 12

**User Story:** As a DevOps engineer, I want the Terraform configuration to follow best practices, so that the infrastructure is maintainable and secure

#### Acceptance Criteria

1. THE Terraform Configuration SHALL use separate files for versions, variables, main resources, and outputs
2. THE Terraform Configuration SHALL NOT include hardcoded credentials or secrets
3. THE Terraform Configuration SHALL use variable references instead of hardcoded values for all configurable parameters
4. THE Terraform Configuration SHALL include resource dependencies using depends_on where necessary
5. THE Terraform Configuration SHALL use descriptive resource names following a consistent naming convention
6. THE Terraform Configuration SHALL include comments explaining complex configurations
7. THE Terraform Configuration SHALL use the local backend by default with optional GCS backend configuration
8. THE Terraform Configuration SHALL be formatted according to Terraform style conventions

### Requirement 13

**User Story:** As a data engineer, I want BigQuery datasets provisioned via Terraform, so that the Tabular service can load structured data into the data warehouse

#### Acceptance Criteria

1. THE Terraform Configuration SHALL enable the BigQuery API (bigquery.googleapis.com)
2. THE Terraform Configuration SHALL create a BigQuery dataset for core tables with configurable dataset_id
3. THE Terraform Configuration SHALL create a BigQuery dataset for staging tables with configurable staging_dataset_id
4. THE Terraform Configuration SHALL set the dataset location to the value of the region variable for data locality
5. THE Terraform Configuration SHALL configure dataset default table expiration for staging tables (7 days)
6. THE Terraform Configuration SHALL NOT set table expiration for core dataset
7. THE Terraform Configuration SHALL add dataset descriptions explaining their purpose
8. THE Terraform Configuration SHALL declare dependencies on BigQuery API enablement

### Requirement 14

**User Story:** As a data engineer, I want BigQuery tables created via Terraform, so that the Tabular service has the correct schema for data loading

#### Acceptance Criteria

1. THE Terraform Configuration SHALL create dimension tables: dim_region, dim_school, dim_time in the core dataset
2. THE Terraform Configuration SHALL create fact tables: fact_assessment, fact_intervention in the core dataset
3. THE Terraform Configuration SHALL create an observations table for unstructured data in the core dataset
4. THE Terraform Configuration SHALL create an ingest_runs table for pipeline tracking in the core dataset
5. THE Terraform Configuration SHALL partition fact tables by date column
6. THE Terraform Configuration SHALL cluster fact tables by region_id
7. THE Terraform Configuration SHALL partition ingest_runs table by created_at
8. THE Terraform Configuration SHALL cluster ingest_runs table by region_id and status
9. THE Terraform Configuration SHALL define explicit schemas for all tables matching the Tabular service data models
10. THE Terraform Configuration SHALL declare dependencies on dataset creation

### Requirement 15

**User Story:** As a DevOps engineer, I want BigQuery configuration variables, so that I can customize dataset names and settings without modifying code

#### Acceptance Criteria

1. THE Terraform Configuration SHALL define a bigquery_dataset_id variable with default value "jedouscale_core"
2. THE Terraform Configuration SHALL define a bigquery_staging_dataset_id variable with default value "jedouscale_staging"
3. THE Terraform Configuration SHALL define a bigquery_staging_table_expiration_days variable with default value 7
4. THE Terraform Configuration SHALL provide descriptions for all BigQuery-related variables
5. THE Terraform Configuration SHALL use these variables in all BigQuery resource definitions

### Requirement 16

**User Story:** As a developer, I want Terraform outputs for BigQuery resources, so that I can easily access dataset and table information

#### Acceptance Criteria

1. THE Terraform Configuration SHALL output bigquery_dataset_id containing the core dataset ID
2. THE Terraform Configuration SHALL output bigquery_staging_dataset_id containing the staging dataset ID
3. THE Terraform Configuration SHALL output bigquery_dataset_location containing the dataset location
4. THE Terraform Configuration SHALL output bigquery_tables containing a list of created table names
5. THE Terraform Configuration SHALL include descriptions for all BigQuery outputs

### Requirement 17

**User Story:** As a DevOps engineer, I want a dedicated service account for Tabular Service, so that it has appropriate permissions for data processing operations

#### Acceptance Criteria

1. THE Terraform Configuration SHALL create a google_service_account resource named "tabular_service"
2. THE Terraform Configuration SHALL set account_id to "tabular-service"
3. THE Terraform Configuration SHALL set display_name to "Tabular Service Account"
4. THE Terraform Configuration SHALL set description to "Service account for Tabular Service running on Cloud Run"
5. THE Terraform Configuration SHALL grant this service account Storage Object Viewer role on the uploads bucket
6. THE Terraform Configuration SHALL grant this service account BigQuery Data Editor role at project level
7. THE Terraform Configuration SHALL grant this service account BigQuery Job User role at project level

### Requirement 18

**User Story:** As a data engineer, I want Eventarc trigger for text files, so that Tabular Service is automatically invoked when Transformer produces text output

#### Acceptance Criteria

1. THE Terraform Configuration SHALL create a google_eventarc_trigger resource named "text_trigger"
2. WHEN enable_eventarc variable is true, THE Terraform Configuration SHALL create the text trigger
3. THE Terraform Configuration SHALL configure the trigger to match "google.cloud.storage.object.v1.finalized" events
4. THE Terraform Configuration SHALL configure the trigger to filter events by bucket name
5. THE Terraform Configuration SHALL configure the trigger to filter events by object name pattern "text/*"
6. THE Terraform Configuration SHALL route events to the Tabular Cloud Run service
7. THE Terraform Configuration SHALL use the Eventarc service account for invoking the Tabular service
8. THE Terraform Configuration SHALL grant Eventarc service account "roles/run.invoker" permission on Tabular service
9. THE Terraform Configuration SHALL declare dependencies on Eventarc API, IAM permissions, and storage bucket

### Requirement 19

**User Story:** As a DevOps engineer, I want Tabular Service configuration variables, so that I can customize the service name without modifying code

#### Acceptance Criteria

1. THE Terraform Configuration SHALL define a tabular_service_name variable with default value "tabular-service"
2. THE Terraform Configuration SHALL provide a description for the tabular_service_name variable
3. THE Terraform Configuration SHALL use this variable in Eventarc trigger configuration
4. THE Terraform Configuration SHALL use this variable in IAM permission configuration
