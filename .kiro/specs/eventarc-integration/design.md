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
(on failure after retries) Dead Letter Queue (Pub/Sub)
```


### Components

1. **Eventarc Trigger**: Subscribes to Cloud Storage events and routes to MIME Decoder
2. **Service Account**: Identity for Eventarc to invoke Cloud Run
3. **Dead Letter Topic**: Pub/Sub topic for failed events
4. **Event Filters**: Configuration to select relevant files

## Terraform Configuration

### Module Structure

```
infra/terraform/
├── eventarc.tf              # Eventarc trigger and related resources
├── variables.tf             # Variables for configuration
├── outputs.tf               # Outputs for trigger and topic
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

  transport {
    pubsub {
      topic = google_pubsub_topic.dead_letter.id
    }
  }
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

### Dead Letter Queue Configuration

```hcl
resource "google_pubsub_topic" "dead_letter" {
  name    = "${var.project_name}-eventarc-dlq"
  project = var.project_id

  message_retention_duration = "604800s"  # 7 days
}

resource "google_pubsub_subscription" "dead_letter_sub" {
  name    = "${var.project_name}-eventarc-dlq-sub"
  topic   = google_pubsub_topic.dead_letter.name
  project = var.project_id

  ack_deadline_seconds = 600
  retain_acked_messages = true
  message_retention_duration = "604800s"
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
3. **Dead Letter Queue**: After 5 failed attempts, event is published to DLQ

### Error Scenarios

| Scenario | HTTP Status | Action |
|----------|-------------|--------|
| MIME Decoder success | 200-299 | Event processed, no retry |
| MIME Decoder validation error | 400-499 | No retry, log error |
| MIME Decoder temporary error | 500-599 | Retry with backoff |
| MIME Decoder timeout | - | Retry with backoff |
| All retries exhausted | - | Send to DLQ |


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
2. **Dead Letter Queue Growth**: Alert when DLQ subscription has > 100 unacked messages
3. **High Latency**: Alert when delivery_latency p95 > 30 seconds
4. **No Events**: Alert when event_count = 0 for > 1 hour (indicates potential issue)

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
4. **Pub/Sub API** must be enabled for dead letter queue

### Terraform Deployment Steps

1. Enable required APIs:
   ```bash
   gcloud services enable eventarc.googleapis.com
   gcloud services enable pubsub.googleapis.com
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

