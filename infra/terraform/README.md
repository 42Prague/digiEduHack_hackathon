# EduScale Engine - Terraform Infrastructure

This folder contains Terraform configuration to provision core GCP infrastructure for the EduScale Engine service, including:

- **Google Artifact Registry**: Docker repository for container images
- **Cloud Storage**: Bucket for file uploads with lifecycle management
- **Shared Model Cache Bucket**: Dedicated GCS bucket that stores Ollama and sentence-transformer artifacts for reuse across Cloud Run instances
- **Eventarc**: Event-driven automation for file processing
- **BigQuery**: Data warehouse with dimension and fact tables
- **IAM Permissions**: Service accounts and access policies
- **Cloud Monitoring**: Dashboard for event delivery metrics

**Note**: Cloud Run services (jedouscale-engine, mime-decoder) are deployed via GitHub Actions, not Terraform. See `.github/workflows/` for deployment workflows.

## Deployment Order

**IMPORTANT**: Follow this two-step process:

### Step 1: Base Infrastructure
Run Terraform with `enable_eventarc=false` to create base infrastructure:
```bash
terraform apply -var="enable_eventarc=false"
```
This creates: Artifact Registry, Storage Bucket, Service Accounts, APIs

### Step 2: Deploy Cloud Run Services
Deploy services via GitHub Actions:
- Push to master branch or manually trigger workflows
- `.github/workflows/deploy.yml` - deploys jedouscale-engine
- `.github/workflows/deploy-mime-decoder.yml` - deploys mime-decoder

### Step 3: Enable Eventarc
Run Terraform with `enable_eventarc=true` to create IAM and Eventarc:
```bash
terraform apply -var="enable_eventarc=true"
```
This creates: IAM permissions, Eventarc trigger, Monitoring dashboard

## Prerequisites

Before using this Terraform configuration, ensure you have:

1. **Terraform CLI** installed (version >= 1.5)
   ```bash
   terraform version
   ```

2. **gcloud CLI** installed and authenticated
   ```bash
   gcloud auth application-default login
   ```

3. **GCP Project** already created
   ```bash
   gcloud projects list
   ```

4. **IAM Permissions**: Your user or service account needs the following roles:
   - `roles/run.admin` (Cloud Run Admin)
   - `roles/artifactregistry.admin` (Artifact Registry Admin)
   - `roles/serviceusage.serviceUsageAdmin` (Service Usage Admin - to enable APIs)
   - `roles/iam.serviceAccountUser` (if using a custom service account)
   
   Or simply `roles/editor` for a hackathon/development environment.

## Quick Start

### 1. Configure Variables

Create a `terraform.tfvars` file from the example:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and set your GCP project ID:

```hcl
project_id = "my-gcp-project-id"
region     = "europe-west1"
```

### 2. Initialize Terraform

```bash
terraform init
```

This downloads the Google Cloud provider and prepares your workspace.

### 3. Review the Plan

```bash
terraform plan
```

Review the resources that will be created:
- Artifact Registry repository
- Cloud Run service
- API enablement (run.googleapis.com, artifactregistry.googleapis.com)
- IAM policy for public access

### 4. Apply the Configuration

```bash
terraform apply
```

Type `yes` when prompted. Terraform will:
1. Enable required Google Cloud APIs
2. Create the Artifact Registry repository
3. Create the Cloud Run service (will fail initially if no image exists)
4. Configure public access

**Note**: The first `terraform apply` may fail if the Docker image doesn't exist yet. See "Building and Pushing Images" below.

### 5. View Outputs

After successful apply:

```bash
terraform output
```

You'll see:
- `cloud_run_url`: The public URL of your service
- `artifact_registry_repository`: The repository URL for pushing images
- `full_image_path`: The complete image path

## Building and Pushing Docker Images

Terraform does NOT build or push Docker images. You must do this separately:

### Build the Image

From the repository root:

```bash
docker build -f docker/Dockerfile -t europe-west1-docker.pkg.dev/YOUR_PROJECT_ID/eduscale-engine-repo/eduscale-engine:latest .
```

### Authenticate Docker with Artifact Registry

```bash
gcloud auth configure-docker europe-west1-docker.pkg.dev
```

### Push the Image

```bash
docker push europe-west1-docker.pkg.dev/YOUR_PROJECT_ID/eduscale-engine-repo/eduscale-engine:latest
```

### Deploy the New Image

After pushing a new image, update Cloud Run:

```bash
terraform apply
```

Or to deploy a specific tag:

```bash
terraform apply -var="image_tag=v1.0.0"
```

## Configuration Variables

### Required Variables

- `project_id`: Your GCP project ID (no default)

### Optional Variables (with defaults)

| Variable | Default | Description |
|----------|---------|-------------|
| `region` | `europe-west1` | GCP region for all resources |
| `service_name` | `eduscale-engine` | Cloud Run service name |
| `repository_id` | `eduscale-engine-repo` | Artifact Registry repository ID |
| `image_tag` | `latest` | Docker image tag to deploy |
| `service_version` | `0.1.0` | Service version (env var) |
| `environment` | `prod` | Environment name (env var) |
| `min_instance_count` | `0` | Minimum Cloud Run instances (0 = scale to zero) |
| `max_instance_count` | `10` | Maximum Cloud Run instances |
| `cpu` | `1` | CPU allocation (1 or 2 vCPU) |
| `memory` | `512Mi` | Memory allocation (512Mi, 1Gi, etc.) |
| `container_port` | `8080` | Container port (must match app) |
| `allow_unauthenticated` | `true` | Allow public access |
| `bigquery_dataset_id` | `jedouscale_core` | BigQuery dataset ID for core tables |
| `bigquery_staging_dataset_id` | `jedouscale_staging` | BigQuery dataset ID for staging tables |
| `bigquery_staging_table_expiration_days` | `7` | Days before staging tables auto-delete |

## Environment Variables

The Cloud Run service is configured with these environment variables (matching the FastAPI app):

- `ENV`: Deployment environment (from `var.environment`)
- `SERVICE_NAME`: Service name (from `var.service_name`)
- `SERVICE_VERSION`: Service version (from `var.service_version`)
- `GCP_PROJECT_ID`: GCP project ID (from `var.project_id`)
- `GCP_REGION`: GCP region (from `var.region`)
- `GCP_RUN_SERVICE`: Cloud Run service name (from `var.service_name`)

## Testing the Deployment

After successful deployment, test the health endpoint:

```bash
# Get the Cloud Run URL
CLOUD_RUN_URL=$(terraform output -raw cloud_run_url)

# Test the health endpoint
curl $CLOUD_RUN_URL/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "eduscale-engine",
  "version": "0.1.0"
}
```

## Connection to the FastAPI Application

The Cloud Run service expects:
- A FastAPI application listening on port 8080
- A `/health` endpoint returning JSON
- Environment variables: `ENV`, `SERVICE_NAME`, `SERVICE_VERSION`, `GCP_PROJECT_ID`, `GCP_REGION`

The application code is in `src/eduscale/` and uses:
- `src/eduscale/main.py`: FastAPI app factory
- `src/eduscale/core/config.py`: Configuration management
- `src/eduscale/api/v1/routes_health.py`: Health endpoint

## Updating the Infrastructure

### Change Configuration

Edit `terraform.tfvars` or pass variables via command line:

```bash
terraform apply -var="max_instance_count=20" -var="memory=1Gi"
```

### Deploy New Image Tag

```bash
# Build and push new image with tag
docker build -f docker/Dockerfile -t europe-west1-docker.pkg.dev/YOUR_PROJECT_ID/eduscale-engine-repo/eduscale-engine:v1.0.0 .
docker push europe-west1-docker.pkg.dev/YOUR_PROJECT_ID/eduscale-engine-repo/eduscale-engine:v1.0.0

# Update Terraform
terraform apply -var="image_tag=v1.0.0"
```

### Scale to Zero for Cost Savings

```bash
terraform apply -var="min_instance_count=0"
```

## Destroying Resources

To remove all infrastructure:

```bash
terraform destroy
```

**Warning**: This will delete:
- The Cloud Run service
- The Artifact Registry repository (and all images)
- IAM policies

## Remote State (Optional)

For team collaboration, consider using remote state in GCS:

1. Create a GCS bucket:
   ```bash
   gsutil mb -l europe-west1 gs://your-terraform-state-bucket
   ```

2. Enable versioning:
   ```bash
   gsutil versioning set on gs://your-terraform-state-bucket
   ```

3. Uncomment the backend block in `versions.tf`:
   ```hcl
   backend "gcs" {
     bucket = "your-terraform-state-bucket"
     prefix = "eduscale-engine/terraform/state"
   }
   ```

4. Re-initialize:
   ```bash
   terraform init -migrate-state
   ```

## Eventarc Integration

The infrastructure includes an event-driven file processing pipeline:

### Architecture Flow

```
User uploads file → Cloud Storage
    ↓ (OBJECT_FINALIZE event)
Eventarc Trigger
    ↓ (HTTP POST with CloudEvent)
MIME Decoder (Cloud Run)
    ↓ (file type classification)
Transformer Service (future)
    ↓ (text extraction)
Tabular Service (future)
    ↓ (schema inference & loading)
BigQuery (future)
```

### Components

1. **Cloud Storage Bucket** (`google_storage_bucket.uploads`)
   - Stores uploaded files
   - Emits OBJECT_FINALIZE events when files are uploaded
   - Lifecycle policy: Delete files after 90 days (configurable)

2. **Eventarc Trigger** (`google_eventarc_trigger.storage_trigger`)
   - Subscribes to Cloud Storage OBJECT_FINALIZE events
   - Filters events by bucket name
   - Routes events to MIME Decoder service
   - Automatic retry with exponential backoff (5 attempts)

3. **MIME Decoder Service** (`google_cloud_run_service.mime_decoder`)
   - Receives CloudEvents from Eventarc
   - Detects file MIME type
   - Classifies files into categories: text, image, audio, archive, other
   - Logs all processing with structured logging

4. **Service Accounts**
   - `eventarc-trigger-sa`: Used by Eventarc to invoke MIME Decoder
   - Has only Cloud Run Invoker and Eventarc Event Receiver permissions
   - NO Cloud Storage permissions (events are pushed, not pulled)

### Deployment Steps for Eventarc Integration

#### Prerequisites

1. Ensure all required APIs are enabled:
   ```bash
   gcloud services enable eventarc.googleapis.com
   gcloud services enable storage.googleapis.com
   gcloud services enable run.googleapis.com
   ```

2. Build and push MIME Decoder Docker image:
   ```bash
   # Build MIME Decoder image
   docker build -f docker/Dockerfile.mime-decoder \
     -t europe-west1-docker.pkg.dev/YOUR_PROJECT_ID/jedouscale-repo/mime-decoder:latest \
     --target mime-decoder .

   # Authenticate Docker
   gcloud auth configure-docker europe-west1-docker.pkg.dev

   # Push image
   docker push europe-west1-docker.pkg.dev/YOUR_PROJECT_ID/jedouscale-repo/mime-decoder:latest
   ```

#### Deploy Infrastructure

```bash
cd infra/terraform

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply configuration
terraform apply
```

This will create:
- Cloud Storage bucket for uploads
- Eventarc trigger
- MIME Decoder Cloud Run service
- Service accounts and IAM permissions
- (Optional) Monitoring alert policies

#### Testing the Eventarc Integration

1. **Upload a test file to Cloud Storage:**
   ```bash
   echo "test content" | gsutil cp - gs://$(terraform output -raw uploads_bucket_name)/test.txt
   ```

2. **Verify event was received:**
   ```bash
   # Check MIME Decoder logs
   gcloud logging read \
     'resource.type="cloud_run_revision"
      resource.labels.service_name="mime-decoder"
      jsonPayload.message="CloudEvent received"' \
     --limit=5 \
     --format=json
   ```

3. **Check Eventarc metrics:**
   ```bash
   # View event delivery metrics
   gcloud monitoring timeseries list \
     --filter='metric.type="eventarc.googleapis.com/trigger/delivery_success_count"' \
     --format="table(metric.type, points)"
   ```

4. **Test retry mechanism:**
   ```bash
   # Temporarily break MIME Decoder to trigger retries
   # (This requires modifying the service to return 5xx errors)
   # Upload a file and observe retry attempts in logs

   gcloud logging read \
     'resource.type="eventarc.googleapis.com/trigger"
      severity>=ERROR' \
     --limit=10
   ```

### Monitoring and Alerting

Alert policies are defined in `alerts.tf` (disabled by default).

To enable monitoring alerts:

```bash
terraform apply \
  -var="enable_monitoring_alerts=true" \
  -var="alert_email=devops@example.com"
```

This creates three alert policies:
1. **High Failure Rate**: Alerts when >10% of events fail
2. **High Latency**: Alerts when p95 latency >30 seconds
3. **No Events**: Alerts when no events received for >1 hour

See `monitoring.md` for detailed monitoring configuration.

### Configuration Variables for Eventarc

| Variable | Default | Description |
|----------|---------|-------------|
| `mime_decoder_service_name` | `mime-decoder` | Name of MIME Decoder Cloud Run service |
| `transformer_service_name` | `transformer` | Name of Transformer Cloud Run service |
| `tabular_service_name` | `tabular-service` | Name of Tabular Cloud Run service |
| `eventarc_trigger_name` | `storage-upload-trigger` | Name of Eventarc trigger |
| `event_filter_prefix` | `""` (all files) | Optional prefix filter for events |
| `enable_monitoring_alerts` | `false` | Enable alert policies |
| `alert_email` | `""` | Email for alert notifications |
| `uploads_bucket_lifecycle_days` | `90` | Days before file deletion |

### Troubleshooting Eventarc

**Events not being delivered:**
```bash
# Check Eventarc trigger status
gcloud eventarc triggers describe storage-upload-trigger \
  --location=europe-west1

# Check service account permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:eventarc-trigger-sa"
```

**MIME Decoder errors:**
```bash
# View recent errors
gcloud logging read \
  'resource.type="cloud_run_revision"
   resource.labels.service_name="mime-decoder"
   severity>=ERROR' \
  --limit=20
```

**Failed events after retries:**
```bash
# Find events that need manual reprocessing
gcloud logging read \
  'resource.type="cloud_run_revision"
   resource.labels.service_name="mime-decoder"
   jsonPayload.manual_reprocessing_required=true' \
  --format=json
```

### Security Considerations

1. **Service Account Permissions**:
   - Eventarc trigger SA has minimal permissions (Cloud Run Invoker only)
   - NO Cloud Storage read/write permissions for Eventarc SA
   - MIME Decoder uses compute default SA for Cloud Storage access

2. **Authentication**:
   - Eventarc invokes MIME Decoder with service account authentication
   - MIME Decoder can optionally require authentication (set `allow_unauthenticated=false`)

3. **Data Locality**:
   - All resources deployed in EU region (europe-west1)
   - Events and data never leave configured region
   - Complies with GDPR data residency requirements

## BigQuery Data Warehouse

The infrastructure includes a complete BigQuery data warehouse for storing and analyzing educational data.

### Data Warehouse Structure

The BigQuery configuration creates two datasets:

1. **Core Dataset** (`jedouscale_core`): Permanent storage for dimension and fact tables
2. **Staging Dataset** (`jedouscale_staging`): Temporary tables for data loading (auto-expire after 7 days)

### Tables

#### Dimension Tables

**dim_region**: Regional information
- `region_id` (STRING, REQUIRED): Unique region identifier
- `region_name` (STRING): Human-readable region name
- `from_date` (DATE): Validity start date
- `to_date` (DATE): Validity end date

**dim_school**: School information
- `school_name` (STRING, REQUIRED): School name
- `region_id` (STRING): Associated region
- `from_date` (DATE): Validity start date
- `to_date` (DATE): Validity end date

**dim_time**: Time dimension for temporal analysis
- `date` (DATE, REQUIRED): Calendar date
- `year` (INTEGER): Year
- `month` (INTEGER): Month (1-12)
- `day` (INTEGER): Day of month
- `quarter` (INTEGER): Quarter (1-4)
- `day_of_week` (INTEGER): Day of week (0-6)

#### Fact Tables

**fact_assessment**: Student assessment results
- Partitioned by `date` (DAY)
- Clustered by `region_id`
- Columns: date, region_id, school_name, student_id, student_name, subject, test_score, file_id, ingest_timestamp

**fact_intervention**: Educational intervention data
- Partitioned by `date` (DAY)
- Clustered by `region_id`
- Columns: date, region_id, school_name, intervention_type, participants_count, file_id, ingest_timestamp

#### Supporting Tables

**observations**: Unstructured/mixed data
- Partitioned by `ingest_timestamp` (DAY)
- Clustered by `region_id`
- Stores free-form text and data that doesn't fit into fact tables

**ingest_runs**: Pipeline execution tracking
- Partitioned by `created_at` (DAY)
- Clustered by `region_id`, `status`
- Tracks all data ingestion operations for audit and debugging

### Partitioning and Clustering Strategy

All fact tables use:
- **Partitioning**: By date fields for query performance and cost optimization
- **Clustering**: By `region_id` for efficient regional queries

Benefits:
- Reduced query costs (only scan relevant partitions)
- Improved query performance
- Automatic partition pruning

### Integration with Tabular Service

The BigQuery tables are designed to work with the Tabular Service:

1. Transformer extracts text from files → saves to `gs://bucket/text/`
2. Eventarc triggers Tabular Service on text file creation
3. Tabular Service:
   - Reads text file from Cloud Storage
   - Infers schema and table type
   - Normalizes data
   - Loads into appropriate BigQuery tables
4. Data available for analysis in BigQuery

### Tabular Service Configuration

The infrastructure provisions:

**Service Account** (`tabular-service`):
- Storage Object Viewer role on uploads bucket (read text files)
- BigQuery Data Editor role at project level (write to tables)
- BigQuery Job User role at project level (execute queries)

**Eventarc Trigger** (`text-files-trigger`):
- Monitors `gs://bucket/text/*` for new files
- Automatically invokes Tabular Service with CloudEvent
- Includes file metadata (bucket, name, size, etc.)

**Deployment Order**:
1. Deploy base infrastructure with `enable_eventarc=false`
2. Deploy Tabular Service via GitHub Actions
3. Enable Eventarc with `enable_eventarc=true`

**Event Flow**:
```
Transformer → gs://bucket/text/file_id.txt
    ↓ (OBJECT_FINALIZE event)
Eventarc text-files-trigger
    ↓ (HTTP POST with CloudEvent)
Tabular Service (Cloud Run)
    ↓ (schema inference & normalization)
BigQuery tables (fact_assessment, fact_intervention, observations)
```

### Testing BigQuery Tables

After deployment, verify tables were created:

```bash
# List datasets
bq ls --project_id=$(terraform output -raw project_id)

# List tables in core dataset
bq ls $(terraform output -raw bigquery_dataset_id)

# View table schema
bq show $(terraform output -raw bigquery_dataset_id).fact_assessment

# Run a test query
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) as row_count FROM \`$(terraform output -raw project_id).$(terraform output -raw bigquery_dataset_id).fact_assessment\`"
```

### Example Queries

**Regional assessment summary:**
```sql
SELECT 
  r.region_name,
  COUNT(DISTINCT a.student_id) as student_count,
  AVG(a.test_score) as avg_score
FROM `jedouedu.jedouscale_core.fact_assessment` a
JOIN `jedouedu.jedouscale_core.dim_region` r ON a.region_id = r.region_id
WHERE a.date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY r.region_name
ORDER BY avg_score DESC;
```

**Intervention effectiveness:**
```sql
SELECT 
  i.intervention_type,
  COUNT(*) as intervention_count,
  SUM(i.participants_count) as total_participants
FROM `jedouedu.jedouscale_core.fact_intervention` i
WHERE i.date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY i.intervention_type
ORDER BY total_participants DESC;
```

**Data quality monitoring:**
```sql
SELECT 
  status,
  COUNT(*) as run_count,
  COUNT(DISTINCT file_id) as unique_files
FROM `jedouedu.jedouscale_core.ingest_runs`
WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY status;
```

## Future Enhancements

Future additions will include:

- **Transformer Services** for text extraction from various formats
- **Tabular Service** for schema inference and data loading
- **Cloud SQL** or **Firestore** for metadata storage
- **VPC configuration** for private networking
- **Cloud CDN** for static assets

## Troubleshooting

### Error: Image not found

```
Error: Error creating Service: Image 'europe-west1-docker.pkg.dev/...' not found
```

**Solution**: Build and push the Docker image first (see "Building and Pushing Images" above).

### Error: API not enabled

```
Error: Error creating Repository: googleapi: Error 403: Artifact Registry API has not been used
```

**Solution**: Wait a few minutes for API enablement to propagate, then run `terraform apply` again.

### Error: Permission denied

```
Error: Error creating Service: Permission denied
```

**Solution**: Ensure your user has the required IAM roles (see Prerequisites).

### Cloud Run service not accessible

**Solution**: Check that `allow_unauthenticated = true` and the IAM policy was created:

```bash
gcloud run services get-iam-policy eduscale-engine --region=europe-west1
```

## Support

For issues related to:
- **Terraform configuration**: Check this README and Terraform docs
- **GCP resources**: Check Google Cloud documentation
- **Application code**: See the main repository README at `../../README.md`

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     Developer                            │
│                                                          │
│  1. terraform apply                                      │
│  2. docker build & push                                  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│              Google Cloud Platform                       │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │     Artifact Registry (europe-west1)             │  │
│  │                                                  │  │
│  │  eduscale-engine-repo/                          │  │
│  │    └── eduscale-engine:latest                   │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                               │
│                         │ pulls image                   │
│                         ▼                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │     Cloud Run (europe-west1)                     │  │
│  │                                                  │  │
│  │  Service: eduscale-engine                       │  │
│  │  ├── Min instances: 0                           │  │
│  │  ├── Max instances: 10                          │  │
│  │  ├── CPU: 1                                     │  │
│  │  ├── Memory: 512Mi                              │  │
│  │  └── Port: 8080                                 │  │
│  │                                                  │  │
│  │  Public URL: https://eduscale-engine-xxx.run.app│  │
│  └──────────────────────────────────────────────────┘  │
│                         │                               │
└─────────────────────────┼───────────────────────────────┘
                          │
                          ▼
                    ┌──────────┐
                    │  Users   │
                    │  /health │
                    └──────────┘
```

## License

This infrastructure code is part of the EduScale Engine project.
