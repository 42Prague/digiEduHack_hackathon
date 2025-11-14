# Design Document

## Overview

The Eventarc Integration is an infrastructure component that provides event-driven automation for the data processing pipeline. It uses Google Cloud's Eventarc service to automatically trigger the MIME Decoder when files are uploaded to Cloud Storage, eliminating the need for polling and ensuring immediate processing.

### Key Design Principles

1. **Infrastructure as Code**: All configuration managed via Terraform
2. **Reliability**: At-least-once delivery with retries and dead letter queue
3. **Security**: Least-privilege service accounts
4. **Observability**: Comprehensive metrics and logging
5. **Regional Compliance**: EU region for data locality

## Architecture

### High-Level Flow

```
User uploads file → Cloud Storage
    ↓
Cloud Storage emits OBJECT_FINALIZE event
    ↓
Eventarc Trigger (filters and routes)
    ↓
MIME Decoder Cloud Run service
    ↓
(on success) Processing continues
    ↓
(on failure after retries) Error logged with full context
```


### Components

1. **Eventarc Trigger**: Subscribes to Cloud Storage events and routes to MIME Decoder
2. **Service Account**: Identity for Eventarc to invoke Cloud Run
3. **Event Filters**: Configuration to select relevant files

## Terraform Configuration

### Module Structure

```
infra/terraform/
├── eventarc.tf              # Eventarc trigger and related resources
├── variables.tf             # Variables for configuration
├── outputs.tf               # Outputs for trigger
└── iam.tf                   # Service account and permissions
```

### Eventarc Trigger Resource

```hcl
resource "google_eventarc_trigger" "storage_trigger" {
  name     = "${var.project_name}-storage-trigger"
  location = var.region
  project  = var.project_id

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }

  matching_criteria {
    attribute = "bucket"
    value     = google_storage_bucket.upload_bucket.name
  }

  destination {
    cloud_run_service {
      service = google_cloud_run_service.mime_decoder.name
      region  = var.region
    }
  }

  service_account = google_service_account.eventarc_trigger.email
}
```


### Service Account Configuration

```hcl
resource "google_service_account" "eventarc_trigger" {
  account_id   = "eventarc-trigger-sa"
  display_name = "Eventarc Trigger Service Account"
  project      = var.project_id
}

resource "google_cloud_run_service_iam_member" "eventarc_invoker" {
  service  = google_cloud_run_service.mime_decoder.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.eventarc_trigger.email}"
}

resource "google_project_iam_member" "eventarc_receiver" {
  project = var.project_id
  role    = "roles/eventarc.eventReceiver"
  member  = "serviceAccount:${google_service_account.eventarc_trigger.email}"
}
```



## Event Payload Format

### CloudEvents Specification

Eventarc delivers events in CloudEvents format:

```json
{
  "specversion": "1.0",
  "type": "google.cloud.storage.object.v1.finalized",
  "source": "//storage.googleapis.com/projects/_/buckets/BUCKET_NAME",
  "subject": "objects/FILE_PATH",
  "id": "unique-event-id",
  "time": "2025-11-13T10:30:00Z",
  "datacontenttype": "application/json",
  "data": {
    "bucket": "eduscale-uploads-eu",
    "name": "uploads/region-123/file-456.pdf",
    "contentType": "application/pdf",
    "size": "1048576",
    "timeCreated": "2025-11-13T10:30:00Z",
    "updated": "2025-11-13T10:30:00Z"
  }
}
```

### MIME Decoder Integration

The MIME Decoder receives the event as an HTTP POST request with the CloudEvents payload in the request body. It extracts:
- `data.bucket`: Cloud Storage bucket name
- `data.name`: Object path (file_id can be derived)
- `data.contentType`: MIME type for classification
- `data.size`: File size for validation


## Retry and Error Handling

### Retry Strategy

1. **Initial Delivery**: Eventarc attempts to deliver the event to MIME Decoder
2. **Retry on Failure**: If MIME Decoder returns 5xx error or times out:
   - Retry 1: After 10 seconds
   - Retry 2: After 20 seconds
   - Retry 3: After 40 seconds
   - Retry 4: After 80 seconds
   - Retry 5: After 160 seconds (max)
3. **Final Failure**: After 5 failed attempts, error is logged with full context

### Error Scenarios

| Scenario | HTTP Status | Action |
|----------|-------------|--------|
| MIME Decoder success | 200-299 | Event processed, no retry |
| MIME Decoder validation error | 400-499 | No retry, log error |
| MIME Decoder temporary error | 500-599 | Retry with backoff |
| MIME Decoder timeout | - | Retry with backoff |
| All retries exhausted | - | Log error with full context |

### Error Logging

When all retry attempts are exhausted, Eventarc logs a structured error entry to Cloud Logging with:
- **Event ID**: Unique identifier for correlation
- **Bucket**: Cloud Storage bucket name
- **Object Name**: File path
- **Content Type**: MIME type
- **File Size**: Size in bytes
- **Error Message**: Last error received from MIME Decoder
- **Retry Count**: Total number of attempts made
- **Timestamps**: Initial attempt and final failure time

This information enables manual file reprocessing or debugging without requiring a Dead Letter Queue.


## Monitoring and Observability

### Cloud Monitoring Metrics

Eventarc automatically emits metrics to Cloud Monitoring:

1. **eventarc.googleapis.com/trigger/event_count**
   - Total events received by the trigger
   - Labels: trigger_name, event_type

2. **eventarc.googleapis.com/trigger/match_count**
   - Events matching the trigger filters
   - Labels: trigger_name

3. **eventarc.googleapis.com/trigger/delivery_success_count**
   - Successful event deliveries
   - Labels: trigger_name, destination

4. **eventarc.googleapis.com/trigger/delivery_failure_count**
   - Failed event deliveries
   - Labels: trigger_name, destination, error_code

5. **eventarc.googleapis.com/trigger/delivery_latency**
   - Time from event emission to delivery
   - Labels: trigger_name

### Logging

All event deliveries are logged to Cloud Logging with:
- Event ID
- Timestamp
- Delivery status (success/failure)
- Retry attempt number
- Error message (if failed)
- Destination service


### Alerting

Recommended Cloud Monitoring alerts:

1. **High Failure Rate**: Alert when delivery_failure_count > 10% of event_count over 5 minutes
2. **High Latency**: Alert when delivery_latency p95 > 30 seconds
3. **No Events**: Alert when event_count = 0 for > 1 hour (indicates potential issue)

## Security Considerations

### Service Account Permissions

The Eventarc trigger service account has minimal permissions:
- **Cloud Run Invoker**: Only for the MIME Decoder service
- **Eventarc Event Receiver**: Required for receiving events
- **NO** Cloud Storage permissions (events are pushed, not pulled)

### Network Security

- Eventarc delivers events over HTTPS
- MIME Decoder Cloud Run service can require authentication
- Service account identity is verified on each invocation

### Data Privacy

- Event payloads contain only metadata (file path, size, content type)
- No file content is transmitted through Eventarc
- All processing occurs within the configured GCP region (EU)


## Deployment Notes

### Prerequisites

1. **Cloud Storage bucket** must exist before creating the trigger
2. **MIME Decoder Cloud Run service** must be deployed
3. **Eventarc API** must be enabled in the GCP project

### Terraform Deployment Steps

1. Enable required APIs:
   ```bash
   gcloud services enable eventarc.googleapis.com
   ```

2. Apply Terraform configuration:
   ```bash
   cd infra/terraform
   terraform init
   terraform plan
   terraform apply
   ```

3. Verify trigger creation:
   ```bash
   gcloud eventarc triggers list --location=europe-west1
   ```

### Testing

1. Upload a test file to Cloud Storage:
   ```bash
   gsutil cp test.txt gs://eduscale-uploads-eu/test/test.txt
   ```

2. Check MIME Decoder logs for event receipt:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mime-decoder" --limit=10
   ```

3. Verify metrics in Cloud Monitoring console

## Tabular Service Trigger

### Purpose

Trigger Tabular service when Transformer saves text files to Cloud Storage, enabling fully event-driven data processing pipeline.

### Terraform Configuration

```hcl
resource "google_eventarc_trigger" "tabular_trigger" {
  name     = "${var.project_name}-tabular-trigger"
  location = var.region
  project  = var.project_id

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }

  matching_criteria {
    attribute = "bucket"
    value     = google_storage_bucket.upload_bucket.name
  }

  # Filter for text files only
  matching_criteria {
    attribute = "subject"
    value     = "objects/text/"
    operator  = "match-path-pattern"
  }

  destination {
    cloud_run_service {
      service = google_cloud_run_service.tabular.name
      region  = var.region
    }
  }

  service_account = google_service_account.eventarc_trigger.email
}
```

### Event Flow

1. **Transformer saves text** → `gs://bucket/text/file_id.txt` (with YAML frontmatter)
2. **GCS emits OBJECT_FINALIZE event**
3. **Eventarc filters** for `text/*` pattern
4. **Eventarc delivers CloudEvent** to Tabular service
5. **Tabular processes** and returns 200
6. **On error**, Eventarc retries with exponential backoff

### CloudEvents Payload

```json
{
  "specversion": "1.0",
  "type": "google.cloud.storage.object.v1.finalized",
  "source": "//storage.googleapis.com/projects/_/buckets/eduscale-uploads-eu",
  "subject": "objects/text/abc123.txt",
  "id": "event-id-456",
  "time": "2025-11-14T10:30:10Z",
  "data": {
    "bucket": "eduscale-uploads-eu",
    "name": "text/abc123.txt",
    "contentType": "text/plain",
    "size": "15000"
  }
}
```

### Integration with Pipeline

```
uploads/* → Eventarc Trigger #1 → MIME Decoder → Transformer
                                                      ↓
                                            saves text/file_id.txt
                                                      ↓
text/* → Eventarc Trigger #2 → Tabular Service → BigQuery
```

### Monitoring

The Tabular trigger emits the same metrics as the MIME Decoder trigger:
- `eventarc.googleapis.com/trigger/event_count`
- `eventarc.googleapis.com/trigger/match_count`
- `eventarc.googleapis.com/trigger/delivery_success_count`
- `eventarc.googleapis.com/trigger/delivery_failure_count`
- `eventarc.googleapis.com/trigger/delivery_latency`

Recommended alerts:
1. **High Failure Rate**: Alert when Tabular trigger delivery_failure_count > 10% of event_count
2. **High Latency**: Alert when Tabular processing latency p95 > 60 seconds (AI processing takes longer)
3. **No Events**: Alert when text file events = 0 for > 2 hours (indicates Transformer issues)

## Known Limitations

**No Dead Letter Queue for Failed Events**: After all retry attempts are exhausted (5 retries with exponential backoff), failed events are logged with full context but not queued for automatic reprocessing. This design choice prioritizes simplicity and rapid deployment for the MVP phase.

For manual reprocessing of failed files:
1. Query Cloud Logging for failed events
2. Extract bucket and object name from error logs
3. Re-upload or re-trigger processing manually

**Production Improvement**: For production deployments handling large volumes, consider adding a Dead Letter Queue (Pub/Sub topic) to enable automatic reprocessing workflows and better failure management.

