# Requirements Document

## Introduction

The MIME Decoder service is experiencing a retry storm causing 10+ RPS. Root cause analysis reveals:

1. **Eventarc trigger misconfiguration**: The `storage_trigger` listens to ALL files in the bucket, including `text/*` files created by the Transformer service
2. **Retry loop**: When Transformer uploads processed files to `text/{file_id}.txt`, it triggers `storage_trigger` → mime-decoder receives event → path validation fails (doesn't match `uploads/{region_id}/{file_id}_{filename}`) → continues processing anyway → calls Transformer → gets 429 (rate limited) → returns 500 → Eventarc retries → infinite loop

**Root Cause**: Eventarc `storage_trigger` should only listen to `uploads/*` prefix, not all files in the bucket.

**Simple Solution**: Add path prefix filter to Eventarc trigger to only process files in `uploads/` folder.

## Glossary

- **MIME Decoder Service**: Cloud Run service that receives GCS events via Eventarc and routes files to the Transformer service
- **Transformer Service**: Downstream Cloud Run service that processes files and uploads results to `text/` folder
- **Eventarc**: GCP service that delivers Cloud Storage events to Cloud Run services with automatic retry logic
- **Retry Storm**: Condition where failed requests are continuously retried, creating exponential load

## Requirements

### Requirement 1: Return Client Error for Invalid Paths

**User Story:** As a system operator, I want invalid file paths to be rejected immediately, so that malformed events don't cause processing errors

#### Acceptance Criteria

1. WHEN an object path does not match pattern "uploads/{region_id}/{file_id}_{filename}", THE MIME Decoder Service SHALL return HTTP 400
2. THE MIME Decoder Service SHALL NOT process files with invalid paths
3. THE MIME Decoder Service SHALL NOT call the Transformer Service for files with invalid paths
4. THE MIME Decoder Service SHALL log path validation failures with severity ERROR and include the invalid path
5. THE MIME Decoder Service SHALL include validation error details in the HTTP 400 response body

### Requirement 2: Add Simple Retry Logic for Transformer Calls

**User Story:** As a system operator, I want the MIME Decoder to retry failed Transformer calls a few times before giving up, so that temporary failures are handled gracefully

#### Acceptance Criteria

1. WHEN calling the Transformer Service, THE MIME Decoder Service SHALL attempt up to 3 total attempts (1 initial + 2 retries)
2. THE MIME Decoder Service SHALL wait 2 seconds between retry attempts
3. WHEN any attempt succeeds, THE MIME Decoder Service SHALL return HTTP 200 with status "success"
4. WHEN all 3 attempts fail with HTTP 5xx errors, THE MIME Decoder Service SHALL return HTTP 500 to trigger Eventarc retry
5. WHEN all 3 attempts fail with HTTP 429 errors, THE MIME Decoder Service SHALL return HTTP 500 to trigger Eventarc retry
6. THE MIME Decoder Service SHALL log each retry attempt with attempt number and error details

### Requirement 3: Add Observability for Debugging

**User Story:** As a system operator, I want detailed logs about event processing, so that I can monitor and debug issues

#### Acceptance Criteria

1. THE MIME Decoder Service SHALL log each retry attempt with structured fields: event_id, file_id, attempt_number, error_type, status_code
2. THE MIME Decoder Service SHALL log final processing outcome with structured fields: event_id, status (success/failed/invalid_path), total_attempts, processing_time_ms
3. THE MIME Decoder Service SHALL log path validation failures with structured fields: event_id, object_path, expected_pattern
4. THE MIME Decoder Service SHALL log Transformer responses with structured fields: event_id, file_id, status_code, response_status
