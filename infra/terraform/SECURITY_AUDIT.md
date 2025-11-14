# Security Audit Checklist for Eventarc Integration

This document provides security verification steps for the Eventarc integration infrastructure.

## Service Account Permissions Audit

### Eventarc Trigger Service Account

**Service Account**: `eventarc-trigger-sa@PROJECT_ID.iam.gserviceaccount.com`

**Expected Permissions**:
- ✅ `roles/run.invoker` for MIME Decoder service ONLY
- ✅ `roles/eventarc.eventReceiver` at project level
- ❌ NO `roles/storage.objectAdmin` or any Cloud Storage permissions
- ❌ NO `roles/editor` or `roles/owner`

**Verification Commands**:

```bash
# Get project ID
PROJECT_ID=$(gcloud config get-value project)

# Check project-level IAM bindings
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:eventarc-trigger-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --format="table(bindings.role)"

# Expected output:
# roles/eventarc.eventReceiver

# Check Cloud Run service IAM policy
gcloud run services get-iam-policy mime-decoder \
  --region=europe-west1 \
  --format="table(bindings.role, bindings.members)"

# Should include:
# roles/run.invoker | serviceAccount:eventarc-trigger-sa@PROJECT_ID.iam.gserviceaccount.com
```

**✅ Pass Criteria**:
- Service account has ONLY `roles/eventarc.eventReceiver` at project level
- Service account has ONLY `roles/run.invoker` for `mime-decoder` service
- Service account has NO Cloud Storage permissions

### MIME Decoder Service Account

**Service Account**: `PROJECT_NUMBER-compute@developer.gserviceaccount.com` (default compute SA)

**Expected Permissions**:
- ✅ `roles/storage.objectAdmin` for uploads bucket
- ❌ Should NOT have broad project-level permissions

**Verification Commands**:

```bash
# Get project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Check bucket-level IAM bindings
BUCKET_NAME=$(terraform output -raw uploads_bucket_name)
gsutil iam get gs://${BUCKET_NAME} | grep -A 5 "compute@developer.gserviceaccount.com"

# Should show roles/storage.objectAdmin
```

**✅ Pass Criteria**:
- Default compute SA has `roles/storage.objectAdmin` for uploads bucket only
- No broader project-level permissions

## Authentication and Authorization

### Eventarc to MIME Decoder Communication

**Requirement**: Eventarc must invoke MIME Decoder with service account authentication

**Verification**:

```bash
# Check Eventarc trigger configuration
gcloud eventarc triggers describe storage-upload-trigger \
  --location=europe-west1 \
  --format="value(serviceAccount)"

# Expected output:
# eventarc-trigger-sa@PROJECT_ID.iam.gserviceaccount.com
```

**✅ Pass Criteria**:
- Eventarc trigger uses `eventarc-trigger-sa` service account
- Service account is configured in trigger

### MIME Decoder Authentication

**Check if MIME Decoder requires authentication**:

```bash
# Check if allUsers has run.invoker role
gcloud run services get-iam-policy mime-decoder \
  --region=europe-west1 \
  --format="table(bindings.role, bindings.members)" \
  | grep "allUsers"

# If output contains "roles/run.invoker | allUsers", authentication is NOT required (less secure)
# If no output, authentication IS required (more secure)
```

**✅ Pass Criteria for Production**:
- MIME Decoder should NOT allow `allUsers` access
- Only `eventarc-trigger-sa` should have `roles/run.invoker`

**⚠️  Development/Testing**:
- `allUsers` access may be acceptable for testing
- Ensure `allow_unauthenticated=false` is set in production

## Network Security

### HTTPS Enforcement

**Requirement**: All communication must use HTTPS

**Verification**:

```bash
# Check MIME Decoder URL
MIME_DECODER_URL=$(gcloud run services describe mime-decoder \
  --region=europe-west1 \
  --format="value(status.url)")

echo $MIME_DECODER_URL

# URL must start with https://
```

**✅ Pass Criteria**:
- MIME Decoder URL uses `https://` protocol
- No HTTP endpoints exposed

### Private Networking (Optional)

**Current State**: Services use public endpoints with authentication

**Future Enhancement**: Use VPC Connector for private communication

```bash
# Check if VPC connector is configured (should be "")
gcloud run services describe mime-decoder \
  --region=europe-west1 \
  --format="value(spec.template.metadata.annotations['run.googleapis.com/vpc-access-connector'])"

# Empty output means no VPC connector (current state)
```

**✅ Pass Criteria**:
- For MVP: Public endpoints with service account authentication are acceptable
- For production: Consider adding VPC connector for private networking

## Data Locality and Privacy

### Regional Configuration

**Requirement**: All resources must be in EU region (GDPR compliance)

**Verification**:

```bash
# Check Cloud Storage bucket location
gsutil ls -L -b gs://$(terraform output -raw uploads_bucket_name) | grep Location

# Expected: europe-west1 or EU

# Check Eventarc trigger location
gcloud eventarc triggers describe storage-upload-trigger \
  --location=europe-west1 \
  --format="value(name)"

# Should succeed (trigger exists in europe-west1)

# Check MIME Decoder location
gcloud run services describe mime-decoder \
  --region=europe-west1 \
  --format="value(metadata.name)"

# Should succeed (service exists in europe-west1)
```

**✅ Pass Criteria**:
- Cloud Storage bucket is in `europe-west1` or `EU`
- Eventarc trigger is in `europe-west1`
- MIME Decoder service is in `europe-west1`
- No resources in non-EU regions

### Data Encryption

**Verification**:

```bash
# Check Cloud Storage encryption
gsutil ls -L -b gs://$(terraform output -raw uploads_bucket_name) | grep -i encryption

# Default encryption should be enabled (Google-managed keys)

# Check Cloud Run encryption
# Cloud Run uses Google-managed encryption by default (no verification needed)
```

**✅ Pass Criteria**:
- Cloud Storage bucket uses Google-managed encryption (default)
- Cloud Run uses Google-managed encryption (default)
- Consider customer-managed encryption keys (CMEK) for production

## Secret Management

### Environment Variables

**Check for secrets in environment variables**:

```bash
# Check MIME Decoder environment variables
gcloud run services describe mime-decoder \
  --region=europe-west1 \
  --format="yaml(spec.template.spec.containers[0].env)"

# Review output for any sensitive data
```

**✅ Pass Criteria**:
- NO API keys, passwords, or tokens in environment variables
- Use Secret Manager for sensitive data
- Only non-sensitive configuration (project ID, bucket names, etc.)

### Secret Manager Integration (Future)

**Current State**: No secrets in use

**Future Enhancement**: Use Secret Manager for API keys

```hcl
# Example: Mount secrets from Secret Manager
env {
  name = "API_KEY"
  value_source {
    secret_key_ref {
      secret  = google_secret_manager_secret.api_key.secret_id
      version = "latest"
    }
  }
}
```

## Audit Logging

### Cloud Audit Logs

**Verification**:

```bash
# Check if Cloud Audit Logs are enabled
gcloud logging read \
  'logName="projects/'$PROJECT_ID'/logs/cloudaudit.googleapis.com%2Factivity"' \
  --limit=5 \
  --format=json

# Should return audit log entries
```

**✅ Pass Criteria**:
- Cloud Audit Logs are enabled (enabled by default in GCP)
- Admin Activity logs are available
- Data Access logs can be enabled for Cloud Storage if needed

### Access Logging

```bash
# Check Cloud Run request logs
gcloud logging read \
  'resource.type="cloud_run_revision"
   resource.labels.service_name="mime-decoder"' \
  --limit=5 \
  --format=json
```

**✅ Pass Criteria**:
- Cloud Run logs all requests
- Logs include timestamp, request details, and response status
- Logs are retained according to Cloud Logging retention policy

## Security Best Practices Compliance

### Least Privilege Principle

**✅ Implemented**:
- Eventarc trigger SA has minimal permissions (Cloud Run Invoker + Eventarc Event Receiver)
- No overly permissive roles (editor, owner) assigned
- Service accounts are purpose-specific

### Defense in Depth

**✅ Implemented**:
- Service account authentication between Eventarc and MIME Decoder
- HTTPS for all communication
- Regional restriction (EU only)

**⚠️  To Consider**:
- VPC Service Controls for additional network boundaries
- Binary Authorization for container image verification

### Monitoring and Alerting

**✅ Implemented** (optional, via `alerts.tf`):
- Alert on high failure rates
- Alert on unusual latency
- Alert on absence of expected events

**Verification**:

```bash
# Check if alert policies are enabled
gcloud alpha monitoring policies list \
  --filter="displayName:'Eventarc'" \
  --format="table(displayName, enabled)"
```

## Security Scanning

### Container Image Scanning

```bash
# Check if Artifact Registry vulnerability scanning is enabled
gcloud artifacts repositories describe jedouscale-repo \
  --location=europe-west1 \
  --format="value(name)"

# Vulnerability scanning is enabled by default in Artifact Registry
```

**✅ Pass Criteria**:
- Artifact Registry vulnerability scanning enabled
- Review scan results regularly

### IAM Recommender

```bash
# Check IAM recommendations
gcloud recommender recommendations list \
  --project=$PROJECT_ID \
  --recommender=google.iam.policy.Recommender \
  --location=global \
  --format="table(name, primaryImpact.category, stateInfo.state)"

# Review any recommendations for service accounts
```

**✅ Pass Criteria**:
- Review and apply IAM Recommender suggestions
- Remove unused permissions

## Compliance Checklist

- [ ] Service accounts follow least-privilege principle
- [ ] No Cloud Storage permissions granted to Eventarc trigger SA
- [ ] MIME Decoder authentication configured appropriately
- [ ] All communication uses HTTPS
- [ ] All resources deployed in EU region
- [ ] No secrets in environment variables
- [ ] Cloud Audit Logs enabled
- [ ] Monitoring alerts configured (optional)
- [ ] Container images scanned for vulnerabilities
- [ ] IAM Recommender suggestions reviewed

## Security Incident Response

### Manual Reprocessing of Failed Events

If events fail and need manual reprocessing:

```bash
# Find failed events
gcloud logging read \
  'resource.type="cloud_run_revision"
   resource.labels.service_name="mime-decoder"
   jsonPayload.manual_reprocessing_required=true' \
  --format=json > failed_events.json

# Extract file information
# bucket: jsonPayload.bucket
# object_name: jsonPayload.object_name
# event_id: jsonPayload.event_id

# Trigger reprocessing by copying file
gsutil cp gs://BUCKET/OBJECT_NAME gs://BUCKET/reprocess/OBJECT_NAME
```

### Revoking Compromised Service Account

If Eventarc trigger SA is compromised:

```bash
# Disable service account
gcloud iam service-accounts disable eventarc-trigger-sa@$PROJECT_ID.iam.gserviceaccount.com

# Delete and recreate trigger with new SA
terraform taint google_eventarc_trigger.storage_trigger
terraform apply
```

## Regular Security Reviews

**Recommended Schedule**:
- **Weekly**: Review Cloud Logging for anomalies
- **Monthly**: Review IAM permissions and Recommender suggestions
- **Quarterly**: Full security audit using this checklist
- **Annually**: Penetration testing and security assessment

## Contact

For security concerns, contact the DevOps team or security officer.
