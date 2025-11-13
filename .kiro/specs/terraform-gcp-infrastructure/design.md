# Design Document: Terraform GCP Infrastructure

## Overview

This design document describes the Terraform infrastructure-as-code configuration for provisioning Google Cloud Platform resources for the EduScale Engine service. The configuration follows Terraform best practices with a modular file structure, comprehensive variable management, and clear separation of concerns. The design prioritizes simplicity, maintainability, and ease of use for developers while ensuring production-ready infrastructure.

The Terraform configuration provisions:
- **Artifact Registry**: A Docker repository for storing container images in an EU region
- **Cloud Run v2 Service**: A fully managed serverless platform for running the containerized FastAPI application
- **API Enablement**: Automatic activation of required Google Cloud APIs
- **IAM Policies**: Public access configuration for the health endpoint

## Architecture

### Infrastructure Components

```mermaid
graph TB
    subgraph "Terraform Configuration"
        TF[Terraform CLI]
        Vars[variables.tf]
        Main[main.tf]
        Outputs[outputs.tf]
        Versions[versions.tf]
    end
    
    subgraph "Google Cloud Platform"
        APIs[API Enablement]
        AR[Artifact Registry]
        CR[Cloud Run v2]
        IAM[IAM Policy]
    end
    
    subgraph "Developer Workflow"
        Dev[Developer]
        Docker[Docker Build/Push]
        TFApply[terraform apply]
    end
    
    TF --> Vars
    TF --> Main
    TF --> Outputs
    TF --> Versions
    
    Main --> APIs
    APIs --> AR
    APIs --> CR
    Main --> IAM
    
    Dev --> Docker
    Docker --> AR
    Dev --> TFApply
    TFApply --> TF
    
    style APIs fill:#e1f5ff
    style AR fill:#e1f5ff
    style CR fill:#e1f5ff
    style IAM fill:#e1f5ff
```

### Resource Dependency Graph

```mermaid
graph LR
    A[google_project_service<br/>artifactregistry] --> C[google_artifact_registry_repository<br/>eduscale_repo]
    B[google_project_service<br/>cloud_run] --> D[google_cloud_run_v2_service<br/>eduscale_engine]
    C --> D
    D --> E[google_cloud_run_v2_service_iam_member<br/>public_access]
    
    style A fill:#fff4e6
    style B fill:#fff4e6
    style C fill:#e3f2fd
    style D fill:#e8f5e9
    style E fill:#fce4ec
```

### File Structure

```
infra/terraform/
├── versions.tf              # Terraform and provider version constraints
├── variables.tf             # Input variable definitions
├── main.tf                  # Core resource definitions
├── outputs.tf               # Output value definitions
├── terraform.tfvars.example # Example variable values
└── README.md                # Documentation
```

## Components and Interfaces

### 1. Terraform Version Configuration (versions.tf)

**Responsibility**: Define Terraform and provider version constraints

**Key Elements**:
- Terraform version constraint: `>= 1.5, < 2.0`
- Google provider version: `~> 7.0`
- Provider configuration using variables
- Optional GCS backend configuration (commented)

**Design Decisions**:
- Use `~>` for provider version to allow patch updates but prevent breaking changes
- Separate versions.tf for clarity and easy version management
- Provider configuration uses variables for flexibility
- Local backend by default for simplicity
- GCS backend option documented but commented for team collaboration scenarios

**Interface**:
```hcl
terraform {
  required_version = ">= 1.5, < 2.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
```

### 2. Variable Definitions (variables.tf)

**Responsibility**: Define all configurable parameters with types, defaults, and descriptions

**Variable Categories**:

**Core GCP Configuration**:
- `project_id` (required, no default)
- `region` (default: "europe-west1")

**Service Configuration**:
- `service_name` (default: "eduscale-engine")
- `repository_id` (default: "eduscale-engine-repo")
- `image_tag` (default: "latest")
- `service_version` (default: "0.1.0")
- `environment` (default: "prod")

**Cloud Run Configuration**:
- `min_instance_count` (default: 0)
- `max_instance_count` (default: 10)
- `cpu` (default: "1")
- `memory` (default: "512Mi")
- `container_port` (default: 8080)
- `allow_unauthenticated` (default: true)

**Design Decisions**:
- No default for `project_id` forces explicit configuration
- Sensible defaults for all other variables enable quick setup
- String type for CPU to support Cloud Run's format ("1", "2", "4")
- Boolean for `allow_unauthenticated` enables conditional IAM policy
- Comprehensive descriptions for self-documenting configuration

**Variable Validation**:
- Type constraints ensure correct data types
- Defaults align with EduScale Engine requirements
- Memory values use Cloud Run format (Mi, Gi)

### 3. Main Resource Configuration (main.tf)

**Responsibility**: Define all GCP resources and their relationships

#### 3.1 API Enablement Resources

**Resources**:
- `google_project_service.artifact_registry`
- `google_project_service.cloud_run`

**Configuration**:
```hcl
resource "google_project_service" "artifact_registry" {
  project = var.project_id
  service = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}
```

**Design Decisions**:
- Enable APIs before creating dependent resources
- `disable_on_destroy = false` prevents accidental API disablement
- Separate resources for each API for granular control
- Idempotent: safe to apply multiple times

#### 3.2 Artifact Registry Repository

**Resource**: `google_artifact_registry_repository.eduscale_repo`

**Configuration**:
```hcl
resource "google_artifact_registry_repository" "eduscale_repo" {
  location      = var.region
  repository_id = var.repository_id
  description   = "Docker repository for EduScale Engine container images"
  format        = "DOCKER"
  
  depends_on = [google_project_service.artifact_registry]
}
```

**Design Decisions**:
- Format set to "DOCKER" for container images
- Location uses region variable for consistency
- Explicit dependency on API enablement
- No cleanup policies in initial version (can be added later)
- Repository ID from variable for flexibility

**Image Path Format**:
```
{region}-docker.pkg.dev/{project_id}/{repository_id}/{service_name}:{image_tag}
```

#### 3.3 Cloud Run v2 Service

**Resource**: `google_cloud_run_v2_service.eduscale_engine`

**Configuration Structure**:
```hcl
resource "google_cloud_run_v2_service" "eduscale_engine" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
  
  template {
    scaling { ... }
    containers { ... }
  }
  
  depends_on = [
    google_project_service.cloud_run,
    google_artifact_registry_repository.eduscale_repo
  ]
}
```

**Scaling Configuration**:
- `min_instance_count`: Scale to zero for cost savings (default: 0)
- `max_instance_count`: Prevent runaway costs (default: 10)
- Cloud Run manages autoscaling based on traffic

**Container Configuration**:
- Image constructed from variables
- Port from `container_port` variable (8080)
- CPU and memory from variables
- Environment variables matching FastAPI app expectations

**Environment Variables**:
- `ENV`: Deployment environment
- `SERVICE_NAME`: Service identifier
- `SERVICE_VERSION`: Version string
- `GCP_PROJECT_ID`: GCP project
- `GCP_REGION`: Deployment region
- `GCP_RUN_SERVICE`: Service name

**Design Decisions**:
- Use Cloud Run v2 for latest features and better API
- `INGRESS_TRAFFIC_ALL` allows public internet access
- Explicit dependencies ensure correct creation order
- Environment variables match existing FastAPI configuration
- Resource limits prevent excessive costs

#### 3.4 IAM Policy for Public Access

**Resource**: `google_cloud_run_v2_service_iam_member.public_access`

**Configuration**:
```hcl
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  count = var.allow_unauthenticated ? 1 : 0
  
  location = google_cloud_run_v2_service.eduscale_engine.location
  name     = google_cloud_run_v2_service.eduscale_engine.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
```

**Design Decisions**:
- Conditional creation using `count` meta-argument
- Grants `roles/run.invoker` to `allUsers` for public access
- References service attributes for consistency
- Can be disabled by setting `allow_unauthenticated = false`
- Enables health endpoint access without authentication

### 4. Output Definitions (outputs.tf)

**Responsibility**: Export useful values after infrastructure creation

**Outputs**:

**Primary Outputs**:
- `cloud_run_url`: The public URL of the Cloud Run service
- `artifact_registry_repository`: The repository URL for Docker push
- `full_image_path`: Complete image path used by Cloud Run

**Confirmation Outputs**:
- `project_id`: Confirms the GCP project
- `region`: Confirms the deployment region
- `service_name`: Confirms the service name

**Design Decisions**:
- All outputs include descriptions
- Primary outputs provide actionable information
- Confirmation outputs help verify configuration
- URL output enables immediate testing
- Repository output used in CI/CD pipelines

**Usage Examples**:
```bash
# Get Cloud Run URL
terraform output -raw cloud_run_url

# Test health endpoint
curl $(terraform output -raw cloud_run_url)/health

# Get image path for docker push
terraform output -raw full_image_path
```

### 5. Example Variables File (terraform.tfvars.example)

**Responsibility**: Provide template for user configuration

**Content**:
- All variables with example values
- Comments explaining each variable
- Placeholder for `project_id`
- Defaults shown for reference

**Design Decisions**:
- Separate example file prevents accidental commits of real values
- Users copy to `terraform.tfvars` and customize
- `.gitignore` should exclude `terraform.tfvars`
- Shows all available configuration options
- Includes both required and optional variables

### 6. Documentation (README.md)

**Responsibility**: Comprehensive guide for using the Terraform configuration

**Sections**:

**Introduction**:
- Purpose and scope
- List of provisioned resources

**Prerequisites**:
- Terraform version requirement
- gcloud CLI setup
- GCP project requirement
- IAM permissions needed

**Quick Start**:
- Step-by-step instructions
- Variable configuration
- Terraform commands (init, plan, apply)
- Expected outputs

**Docker Image Management**:
- Build commands
- Authentication setup
- Push commands
- Image tagging strategy

**Configuration Reference**:
- Table of all variables
- Defaults and descriptions
- Usage examples

**Testing**:
- How to verify deployment
- Health endpoint testing
- Expected responses

**Updating Infrastructure**:
- Changing configuration
- Deploying new images
- Scaling adjustments

**Troubleshooting**:
- Common errors and solutions
- Permission issues
- API enablement delays
- Image not found errors

**Future Enhancements**:
- Planned additions (GCS, BigQuery, etc.)
- Extension points

**Design Decisions**:
- Comprehensive but scannable
- Code examples for all operations
- Troubleshooting based on common issues
- Links to relevant documentation
- Architecture diagram for visual understanding

## Data Flow

### Deployment Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant TF as Terraform
    participant GCP as Google Cloud
    participant AR as Artifact Registry
    participant CR as Cloud Run
    
    Dev->>TF: terraform init
    TF->>TF: Download providers
    
    Dev->>TF: terraform plan
    TF->>GCP: Check current state
    GCP->>TF: Return state
    TF->>Dev: Show planned changes
    
    Dev->>TF: terraform apply
    TF->>GCP: Enable APIs
    GCP->>TF: APIs enabled
    
    TF->>AR: Create repository
    AR->>TF: Repository created
    
    TF->>CR: Create service
    CR->>AR: Pull image
    AR->>CR: Image pulled
    CR->>TF: Service created
    
    TF->>CR: Set IAM policy
    CR->>TF: Policy set
    
    TF->>Dev: Outputs (URL, etc.)
```

### Image Update Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Docker as Docker CLI
    participant AR as Artifact Registry
    participant TF as Terraform
    participant CR as Cloud Run
    
    Dev->>Docker: docker build
    Docker->>Dev: Image built
    
    Dev->>Docker: docker push
    Docker->>AR: Push image
    AR->>Docker: Image stored
    
    Dev->>TF: terraform apply
    TF->>CR: Update service
    CR->>AR: Pull new image
    AR->>CR: New image pulled
    CR->>TF: Service updated
    TF->>Dev: Deployment complete
```

## Configuration Management

### Variable Precedence

Terraform loads variables in this order (later sources override earlier):

1. Default values in `variables.tf`
2. `terraform.tfvars` file
3. `*.auto.tfvars` files (alphabetical order)
4. `-var` command-line flags
5. Environment variables (`TF_VAR_name`)

**Recommended Approach**:
- Use `terraform.tfvars` for project-specific values
- Use `-var` flags for CI/CD overrides
- Keep defaults in `variables.tf` for common values

### State Management

**Local State (Default)**:
- State stored in `terraform.tfstate` file
- Simple for single-developer scenarios
- Should be backed up regularly
- Not suitable for team collaboration

**Remote State (Optional)**:
- State stored in GCS bucket
- Enables team collaboration
- Provides state locking
- Requires pre-created bucket
- Configuration commented in `versions.tf`

**State Security**:
- State files contain sensitive data
- Never commit state to version control
- Use encrypted remote backends for production
- Restrict access to state storage

## Error Handling

### API Enablement Delays

**Issue**: APIs may take time to propagate after enablement

**Mitigation**:
- Explicit `depends_on` relationships
- Retry `terraform apply` if initial attempt fails
- Document expected delay in README

### Image Not Found

**Issue**: Cloud Run service creation fails if image doesn't exist

**Mitigation**:
- Document image build/push as prerequisite
- Provide clear error message guidance
- README includes image management section
- Consider using a placeholder image for initial setup

### Permission Errors

**Issue**: Insufficient IAM permissions for resource creation

**Mitigation**:
- Document required roles in README
- Provide clear error messages
- Suggest using `roles/editor` for development
- List fine-grained roles for production

### Resource Conflicts

**Issue**: Resources already exist from manual creation

**Mitigation**:
- Use `terraform import` to adopt existing resources
- Document import commands in README
- Use unique resource names
- Check for conflicts before apply

## Security Considerations

### IAM and Access Control

**Public Access**:
- Controlled by `allow_unauthenticated` variable
- Can be disabled for internal services
- Default is `true` for health endpoint access
- Future: Add authentication for data endpoints

**Service Account**:
- Uses default Cloud Run service account
- Future: Create dedicated service account with minimal permissions
- Document service account best practices

### Secrets Management

**Current State**:
- No secrets required for initial setup
- Environment variables are non-sensitive

**Future Considerations**:
- Use Google Secret Manager for sensitive data
- Reference secrets in Cloud Run configuration
- Never store secrets in Terraform code or state
- Use separate secret management workflow

### Network Security

**Current State**:
- Public ingress for health endpoint
- HTTPS enforced by Cloud Run

**Future Enhancements**:
- VPC connector for private resources
- Cloud Armor for DDoS protection
- Load balancer with custom domain
- IP allowlisting for admin endpoints

## Performance Considerations

### Cold Start Optimization

**Configuration**:
- `min_instance_count = 0` for cost savings
- Small container image for fast pulls
- Minimal startup time in FastAPI app

**Trade-offs**:
- First request after idle has latency
- Can set `min_instance_count = 1` for always-warm instance
- Cost vs. performance decision

### Scaling Configuration

**Defaults**:
- Min: 0 instances (scale to zero)
- Max: 10 instances (cost protection)
- Cloud Run autoscales based on traffic

**Tuning**:
- Increase max for high traffic
- Set min > 0 for consistent performance
- Monitor Cloud Run metrics for optimization

### Resource Allocation

**Defaults**:
- CPU: 1 vCPU
- Memory: 512Mi

**Considerations**:
- FastAPI is lightweight, defaults sufficient
- Increase for ML model inference
- Monitor container metrics
- Cost increases with resources

## Testing Strategy

### Terraform Validation

**Commands**:
```bash
terraform fmt -check    # Check formatting
terraform validate      # Validate syntax
terraform plan          # Preview changes
```

**Integration**:
- Run in CI/CD pipeline
- Validate before merge
- Check for drift regularly

### Infrastructure Testing

**Manual Testing**:
1. Apply configuration
2. Verify resources created
3. Test health endpoint
4. Check logs in Cloud Logging
5. Verify scaling behavior

**Automated Testing** (Future):
- Terratest for infrastructure tests
- Validate outputs
- Test resource properties
- Cleanup after tests

### Deployment Verification

**Checklist**:
- [ ] Artifact Registry repository exists
- [ ] Cloud Run service is running
- [ ] Health endpoint returns 200
- [ ] Logs appear in Cloud Logging
- [ ] IAM policy allows public access
- [ ] Outputs contain correct values

## Deployment Workflow

### Initial Deployment

1. **Setup**:
   - Install Terraform >= 1.5
   - Authenticate with gcloud
   - Create GCP project

2. **Configuration**:
   - Copy `terraform.tfvars.example` to `terraform.tfvars`
   - Set `project_id`
   - Customize other variables if needed

3. **Build Image**:
   - Build Docker image
   - Authenticate Docker with Artifact Registry
   - Push image to registry

4. **Deploy Infrastructure**:
   - `terraform init`
   - `terraform plan`
   - `terraform apply`

5. **Verify**:
   - Get Cloud Run URL from outputs
   - Test health endpoint
   - Check Cloud Logging

### Update Deployment

**Configuration Changes**:
```bash
# Edit terraform.tfvars
terraform plan
terraform apply
```

**New Image Version**:
```bash
# Build and push new image
docker build -t {image_path}:v1.0.0 .
docker push {image_path}:v1.0.0

# Update Terraform
terraform apply -var="image_tag=v1.0.0"
```

**Rollback**:
```bash
# Deploy previous image tag
terraform apply -var="image_tag=previous-tag"
```

## Future Extensibility

### Planned Additions

**Phase 2 - Data Storage**:
- Cloud Storage buckets for file uploads
- BigQuery datasets for analytics
- Firestore for metadata

**Phase 3 - Advanced Features**:
- Cloud Functions for ML inference
- Pub/Sub for event processing
- Cloud Scheduler for batch jobs

**Phase 4 - Production Hardening**:
- Custom service accounts
- VPC networking
- Cloud Armor
- Cloud CDN
- Custom domains

### Extension Points

**Modular Structure**:
- Add new `.tf` files for new resources
- Use Terraform modules for reusable components
- Separate environments with workspaces

**Variable Expansion**:
- Add variables for new features
- Maintain backward compatibility
- Document new variables

**Output Expansion**:
- Export new resource attributes
- Provide connection strings
- Include resource IDs for other tools

## Technology Choices

### Terraform vs. Alternatives

**Why Terraform**:
- Declarative infrastructure-as-code
- Multi-cloud support (future flexibility)
- Large community and ecosystem
- State management
- Plan/preview before apply

**Alternatives Considered**:
- **gcloud CLI**: Imperative, harder to maintain
- **Cloud Deployment Manager**: GCP-specific, less popular
- **Pulumi**: Requires programming language knowledge
- **Manual Console**: Not reproducible, error-prone

### Cloud Run v2 vs. v1

**Why v2**:
- Modern API design
- Better feature support
- Future-proof
- Improved configuration structure

**Trade-offs**:
- Slightly different resource structure
- Requires newer provider version
- Well-documented migration path

### Local vs. Remote State

**Default: Local**:
- Simple for hackathon/development
- No additional setup required
- Easy to understand

**Optional: Remote (GCS)**:
- Team collaboration
- State locking
- Backup and versioning
- Documented for future use

## Success Criteria

The Terraform configuration is successful if:

1. ✅ Developer can deploy infrastructure with 3 commands (init, plan, apply)
2. ✅ All required GCP resources are created automatically
3. ✅ Configuration is customizable via variables
4. ✅ Outputs provide actionable information
5. ✅ Documentation is clear and comprehensive
6. ✅ Code follows Terraform best practices
7. ✅ Resources are properly dependent and ordered
8. ✅ Public access works for health endpoint
9. ✅ Configuration is maintainable and extensible
10. ✅ No hardcoded values or secrets in code
