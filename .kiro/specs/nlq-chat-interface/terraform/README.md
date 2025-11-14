# Terraform Configuration for NLQ Service Account

## Overview

This directory contains Terraform configuration to provision IAM resources for the NLQ Chat Interface service.

## Resources Created

### Service Account: `nlq-service`

**Purpose**: Execute read-only BigQuery queries for natural language query functionality

**IAM Roles**:
- `roles/bigquery.dataViewer` - Read table data, schemas, and metadata
- `roles/bigquery.jobUser` - Execute BigQuery queries and jobs

**Permissions Included**:
- ✅ Read BigQuery table data (`bigquery.tables.getData`)
- ✅ Read BigQuery table schemas (`bigquery.tables.get`)
- ✅ Execute SELECT queries (`bigquery.jobs.create`)
- ✅ View query results (`bigquery.jobs.get`)
- ❌ **NOT** write/update/delete data
- ❌ **NOT** create/alter/drop tables
- ❌ **NOT** access Cloud Storage

## Deployment

### Step 1: Copy to Main Terraform Directory

```bash
# Copy the service account configuration to your main Terraform directory
cp .kiro/specs/nlq-chat-interface/terraform/nlq-service-account.tf infra/terraform/
```

### Step 2: Apply Terraform Configuration

```bash
cd infra/terraform

# Initialize Terraform (if needed)
terraform init

# Preview changes
terraform plan

# Apply changes
terraform apply
```

### Step 3: Verify Service Account

```bash
# Get the service account email
SERVICE_ACCOUNT=$(terraform output -raw nlq_service_account_email)
echo "NLQ Service Account: $SERVICE_ACCOUNT"

# Verify IAM roles
gcloud projects get-iam-policy $(terraform output -raw project_id) \
  --flatten="bindings[].members" \
  --filter="bindings.members:$SERVICE_ACCOUNT" \
  --format="table(bindings.role)"

# Expected output:
# roles/bigquery.dataViewer
# roles/bigquery.jobUser
```

## Cloud Run Configuration

### Use Service Account in Cloud Run

Update your Cloud Run service to use the NLQ service account:

```yaml
# infra/nlq-config.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: eduscale-engine
spec:
  template:
    spec:
      serviceAccountName: nlq-service@PROJECT_ID.iam.gserviceaccount.com
      containers:
      - image: gcr.io/PROJECT_ID/eduscale-engine:latest
        env:
        - name: GCP_PROJECT_ID
          value: "PROJECT_ID"
        - name: BIGQUERY_DATASET_ID
          value: "jedouscale_core"
```

Or via gcloud command:

```bash
gcloud run services update eduscale-engine \
  --service-account=nlq-service@PROJECT_ID.iam.gserviceaccount.com \
  --region=europe-west1
```

## Security Verification

### Test Read Access (Should Work)

```bash
# Test query execution
gcloud auth activate-service-account --key-file=nlq-service-key.json

bq query --use_legacy_sql=false \
  "SELECT region_id, AVG(test_score) as avg_score 
   FROM \`PROJECT_ID.jedouscale_core.fact_assessment\` 
   GROUP BY region_id 
   LIMIT 10"
```

**Expected**: Query succeeds, returns results ✅

### Test Write Access (Should Fail)

```bash
# Try to insert data (should fail)
bq query --use_legacy_sql=false \
  "INSERT INTO \`PROJECT_ID.jedouscale_core.fact_assessment\` 
   (date, region_id, test_score) 
   VALUES (CURRENT_DATE(), 'test', 100)"
```

**Expected**: `Error: Access Denied: BigQuery BigQuery: Permission bigquery.tables.updateData denied` ❌

### Test Table Creation (Should Fail)

```bash
# Try to create table (should fail)
bq mk --table PROJECT_ID:jedouscale_core.test_table schema.json
```

**Expected**: `Error: Access Denied` ❌

## Troubleshooting

### Issue: "Permission denied" errors

**Symptom**:
```
Query execution failed: Permission denied. You may not have access to the requested data.
```

**Possible Causes**:
1. Service account not created yet
2. Cloud Run not using the correct service account
3. IAM roles not propagated (wait 60 seconds)

**Solutions**:

```bash
# 1. Verify service account exists
gcloud iam service-accounts list | grep nlq-service

# 2. Verify Cloud Run is using correct service account
gcloud run services describe eduscale-engine \
  --region=europe-west1 \
  --format="value(spec.template.spec.serviceAccountName)"

# 3. Verify IAM roles are attached
gcloud projects get-iam-policy $(gcloud config get-value project) \
  --flatten="bindings[].members" \
  --filter="bindings.members:nlq-service@" \
  --format="table(bindings.role)"

# 4. If missing roles, reapply Terraform
cd infra/terraform
terraform apply -auto-approve
```

### Issue: "Dataset not found"

**Symptom**:
```
Not found: Dataset PROJECT_ID:jedouscale_core was not found
```

**Solution**:
```bash
# Verify dataset exists
bq ls --project_id=$(terraform output -raw project_id)

# If missing, apply BigQuery Terraform
cd infra/terraform
terraform apply -target=google_bigquery_dataset.core
```

### Issue: "Table not found"

**Symptom**:
```
Not found: Table PROJECT_ID:jedouscale_core.fact_assessment was not found
```

**Solution**:
```bash
# List tables in dataset
bq ls $(terraform output -raw bigquery_dataset_id)

# If missing, apply all BigQuery tables
cd infra/terraform
terraform apply -target=google_bigquery_table.fact_assessment
```

## IAM Role Details

### roles/bigquery.dataViewer

Allows reading BigQuery data:
- `bigquery.datasets.get`
- `bigquery.tables.get`
- `bigquery.tables.list`
- `bigquery.tables.getData`
- `bigquery.models.getData`
- `resourcemanager.projects.get`

### roles/bigquery.jobUser

Allows executing BigQuery jobs:
- `bigquery.jobs.create` (submit queries)
- `bigquery.jobs.get` (view job status)
- `bigquery.jobs.list` (list user's jobs)
- `resourcemanager.projects.get`

**Combined**: Read data + execute queries = Perfect for NLQ! ✅

## Cleanup

To remove the service account:

```bash
cd infra/terraform
terraform destroy -target=google_service_account.nlq_service
```

## References

- [BigQuery IAM Roles](https://cloud.google.com/bigquery/docs/access-control)
- [Cloud Run Service Accounts](https://cloud.google.com/run/docs/securing/service-identity)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

