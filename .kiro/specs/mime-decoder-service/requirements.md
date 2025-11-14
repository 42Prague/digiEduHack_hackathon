# Requirements Document

## Introduction

The MIME Decoder Service is an orchestration microservice that receives file upload events from Eventarc, classifies files by MIME type, and routes them to appropriate processing services. It acts as the central coordinator in the event-driven data processing pipeline, ensuring each file type is handled by the correct processor (Transformer service).

The MIME Decoder operates as part of the pipeline: Cloud Storage → Eventarc → **MIME Decoder** → Transformer → Tabular → BigQuery, with status flowing back to the Backend.

## Glossary

- **MIME Decoder**: Orchestration service that classifies and routes files based on MIME type
- **MIME Type**: Media type identifier (e.g., application/pdf, image/jpeg, text/csv)
- **File Classification**: Process of categorizing files into types: text, image, audio, archive, other
- **Transformer Service**: Downstream service that converts files to text format
- **CloudEvents**: Standard format for event data used by Eventarc
- **Processing Status**: Result returned from downstream services (INGESTED, FAILED)
- **Backend Service**: Upstream service that initiated the upload and receives status updates


## Requirements

### Requirement 1: CloudEvents Reception

**User Story:** As a system architect, I want the MIME Decoder to receive CloudEvents from Eventarc, so that file uploads trigger automatic processing.

#### Acceptance Criteria

1. THE MIME Decoder SHALL expose an HTTP POST endpoint to receive CloudEvents
2. WHEN an event is received, THE MIME Decoder SHALL parse the CloudEvents payload
3. WHEN parsing succeeds, THE MIME Decoder SHALL extract bucket name, object name, content type, and size from the event data
4. WHEN parsing fails, THE MIME Decoder SHALL return HTTP 400 with error details
5. THE MIME Decoder SHALL validate that required fields (bucket, name) are present
6. WHEN validation fails, THE MIME Decoder SHALL return HTTP 400 and log the error

### Requirement 2: File Metadata Extraction

**User Story:** As a developer, I want file metadata extracted from events, so that downstream services have context about the file.

#### Acceptance Criteria

1. WHEN an event is received, THE MIME Decoder SHALL extract the file_id from the object name path
2. WHEN an event is received, THE MIME Decoder SHALL extract the region_id from the object name path
3. WHEN the object name follows the pattern uploads/{region_id}/{file_id}.ext, THE MIME Decoder SHALL parse region_id and file_id
4. WHEN the object name does not match expected patterns, THE MIME Decoder SHALL log a warning and use default values
5. THE MIME Decoder SHALL store the original object name for audit purposes



### Requirement 3: MIME Type Classification

**User Story:** As a system architect, I want files classified by MIME type, so that each file type is processed appropriately.

#### Acceptance Criteria

1. WHEN a file has MIME type text/*, THE MIME Decoder SHALL classify it as "text"
2. WHEN a file has MIME type audio/*, THE MIME Decoder SHALL classify it as "audio"
3. WHEN a file has MIME type application/zip or application/x-tar, THE MIME Decoder SHALL classify it as "archive"
4. WHEN a file has MIME type application/pdf, THE MIME Decoder SHALL classify it as "text"
5. WHEN a file has MIME type application/vnd.openxmlformats-officedocument.*, THE MIME Decoder SHALL classify it as "text"
6. WHEN a file has MIME type image/*, THE MIME Decoder SHALL classify it as "other"
7. WHEN a file has an unrecognized MIME type, THE MIME Decoder SHALL classify it as "other"
8. THE MIME Decoder SHALL log the classification decision with MIME type and category



### Requirement 4: Transformer Service Integration

**User Story:** As a system architect, I want the MIME Decoder to route files to the Transformer service, so that files are converted to text format.

#### Acceptance Criteria

1. WHEN a file is classified, THE MIME Decoder SHALL call the Transformer service with file metadata
2. THE MIME Decoder SHALL send file_id, region_id, bucket, object_name, content_type, and file_category to Transformer
3. THE MIME Decoder SHALL use HTTP POST to invoke the Transformer service endpoint
4. WHEN the Transformer returns success (200), THE MIME Decoder SHALL extract the processing status
5. WHEN the Transformer returns an error (4xx/5xx), THE MIME Decoder SHALL log the error and return HTTP 500
6. THE MIME Decoder SHALL set a timeout of 300 seconds for Transformer calls
7. WHEN the Transformer times out, THE MIME Decoder SHALL return HTTP 500 to trigger Eventarc retry



### Requirement 5: Status Propagation

**User Story:** As a product manager, I
 want processing status returned to the Backend, so that users can see file processing progress.

#### Acceptance Criteria

1. WHEN the Transformer returns a status, THE MIME Decoder SHALL forward the status to the Backend service
2. THE MIME Decoder SHALL call the Backend API endpoint with file_id, status, and processing details
3. WHEN the Backend call succeeds, THE MIME Decoder SHALL log the status update
4. WHEN the Backend call fails, THE MIME Decoder SHALL log the error but still return success to Eventarc
5. THE MIME Decoder SHALL not block on Backend status updates (fire-and-forget pattern)

### Requirement 6: Error Handling and Logging

**User Story:** As a DevOps engineer, I want comprehensive error logging, so that I can debug processing failures.

#### Acceptance Criteria

1. WHEN any error occurs, THE MIME Decoder SHALL log the error with full context (file_id, region_id, error message, stack trace)
2. THE MIME Decoder SHALL use structured logging with JSON format
3. THE MIME Decoder SHALL log at appropriate levels (INFO for success, WARNING for retryable errors, ERROR for failures)
4. WHEN a validation error occurs (400), THE MIME Decoder SHALL return HTTP 400 to prevent Eventarc retries
5. WHEN a processing error occurs (500), THE MIME Decoder SHALL return HTTP 500 to trigger Eventarc retries
6. THE MIME Decoder SHALL include correlation IDs in all logs for request tracing



### Requirement 7: Health Check Endpoint

**User Story:** As a DevOps engineer, I want health check endpoints, so that Cloud Run can monitor service health.

#### Acceptance Criteria

1. THE MIME Decoder SHALL expose a GET /health endpoint
2. WHEN the service is healthy, THE /health endpoint SHALL return HTTP 200 with status "healthy"
3. THE /health endpoint SHALL check connectivity to Transformer service
4. WHEN dependencies are unavailable, THE /health endpoint SHALL return HTTP 503
5. THE /health endpoint SHALL respond within 5 seconds

### Requirement 8: Configuration Management

**User Story:** As a DevOps engineer, I want configuration via environment variables, so that I can deploy to different environments.

#### Acceptance Criteria

1. THE MIME Decoder SHALL read TRANSFORMER_SERVICE_URL from environment variables
2. THE MIME Decoder SHALL read BACKEND_SERVICE_URL from environment variables
3. THE MIME Decoder SHALL read GCP_PROJECT_ID and GCP_REGION from environment variables
4. THE MIME Decoder SHALL read LOG_LEVEL from environment variables with default "INFO"
5. THE MIME Decoder SHALL read REQUEST_TIMEOUT from environment variables with default 300 seconds
6. THE configuration SHALL be validated at startup and log errors for missing required variables



### Requirement 9: Cloud Run Deployment

**User Story:** As a DevOps engineer, I want the MIME Decoder dep