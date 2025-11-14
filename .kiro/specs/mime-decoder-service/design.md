# Design Document

## Overview

The MIME Decoder Service is an orchestration microservice that receives file upload events from Eventarc, classifies files by MIME type, and routes them to the Transformer service for processing. It acts as the central coordinator in the event-driven data processing pipeline.

### Key Design Principles

1. **Lightweight Orchestration**: Minimal processing, focus on routing
2. **Fast Response**: Return quickly to Eventarc to avoid timeouts
3. **Fire-and-Forget**: Don't block on Backend status updates
4. **Structured Logging**: JSON logs with correlation IDs
5. **Fail-Fast**: Clear error responses for validation vs processing errors

## Architecture

### High-Level Flow

```
Eventarc → MIME Decoder (CloudEvents)
    ↓
Parse event & extract metadata
    ↓
Classify MIME type → category (text/image/audio/archive/other)
    ↓
Call Transformer service
    ↓
(async) Update Backend with status
    ↓
Return 200 to Eventarc
```

### Module Structure

```
src/eduscale/services/mime_decoder/
├── __init__.py
├── main.py                    # FastAPI app and endpoints
├── service.py                 # Main orchestration logic
├── classifier.py              # MIME type classification logic
├── models.py                  # Data models (CloudEvent, ProcessingRequest)
└── clients.py                 # HTTP clients for Transformer and Backend
```


## Components and Interfaces

### 1. CloudEvents Handler (main.py)

**Purpose**: Receive and parse CloudEvents from Eventarc

**Interface**:
```python
@app.post("/")
async def handle_cloud_event(request: Request) -> JSONResponse:
    """Receive CloudEvents from Eventarc and orchestrate processing."""
```

**CloudEvents Payload**:
```json
{
  "specversion": "1.0",
  "type": "google.cloud.storage.object.v1.finalized",
  "source": "//storage.googleapis.com/projects/_/buckets/BUCKET",
  "subject": "objects/uploads/region-123/file-456.pdf",
  "id": "event-id-123",
  "time": "2025-11-13T10:30:00Z",
  "data": {
    "bucket": "eduscale-uploads-eu",
    "name": "uploads/region-123/file-456.pdf",
    "contentType": "application/pdf",
    "size": "1048576"
  }
}
```

**Response**:
- 200: Successfully queued for processing
- 400: Invalid event payload (no retry)
- 500: Processing error (Eventarc will retry)



### 2. Metadata Extraction (models.py)

**Purpose**: Extract file_id and region_id from object path

**Interface**:
```python
@dataclass
class ProcessingRequest:
    file_id: str
    region_id: str
    bucket: str
    object_name: str
    content_type: str
    file_category: str
    size_bytes: int
    event_id: str
    timestamp: datetime

    @classmethod
    def from_cloud_event(cls, event: CloudEvent, file_category: str) -> "ProcessingRequest":
        """Create ProcessingRequest from CloudEvent with region_id extraction."""
```

**Path Parsing**:
- Pattern: `uploads/{region_id}/{file_id}.{ext}`
- Example: `uploads/region-cz-01/abc123.pdf` → region_id=`region-cz-01`, file_id=`abc123`

### 3. MIME Type Classifier (classifier.py)

**Purpose**: Classify files into processing categories

**Interface**:
```python
def classify_mime_type(content_type: str) -> Literal["text", "image", "audio", "archive", "other"]:
    """Classify MIME type into processing category."""
```

**Classification Rules**:
```python
MIME_CATEGORIES = {
    "text": [
        "text/*",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.*",
        "application/vnd.ms-*",
        "application/json",
        "application/xml"
    ],
    "audio": ["audio/*", "video/*"],
    "archive": [
        "application/zip",
        "application/x-tar",
        "application/gzip",
        "application/x-rar"
    ]
    # Note: image/* files are classified as "other" since OCR is not implemented
}
```



### 4. Service Orchestrator (service.py)

**Purpose**: Coordinate the processing flow

**Interface**:
```python
async def process_cloud_event(event_data: dict) -> dict:
    """
    Process CloudEvent and orchestrate file routing.
    
    Flow:
    1. Parse CloudEvent
    2. Classify MIME type
    3. Extract metadata (file_id, region_id)
    4. Call Transformer service
    5. Fire-and-forget status update to Backend
    6. Return result
    """
```

**Response**:
```python
{
    "status": "success",
    "event_id": "event-123",
    "file_id": "abc123",
    "file_category": "text",
    "message": "Event processed successfully"
}
```



### 5. Transformer Client (clients.py)

**Purpose**: Call Transformer service

**Interface**:
```python
async def call_transformer(
    transformer_url: str,
    request: ProcessingRequest,
    timeout: int = 300
) -> dict:
    """Call Transformer service to process file."""
```

**Request to Transformer**:
```json
{
  "file_id": "abc123",
  "region_id": "region-cz-01",
  "bucket": "eduscale-uploads-eu",
  "object_name": "uploads/region-cz-01/abc123.pdf",
  "content_type": "application/pdf",
  "file_category": "text",
  "size": 1048576
}
```

**Response from Transformer**:
```json
{
  "status": "INGESTED",
  "text_uri": "gs://eduscale-uploads-eu/text/abc123.txt",
  "processing_time_ms": 5000
}
```

### 6. Backend Client (clients.py)

**Purpose**: Update Backend with processing status (fire-and-forget)

**Interface**:
```python
async def update_backend_status(
    backend_url: str,
    file_id: str,
    status: str,
    details: dict,
    timeout: int = 5
) -> None:
    """Update Backend with processing status (non-blocking)."""
```

**Request to Backend**:
```json
{
  "file_id": "abc123",
  "status": "PROCESSING",
  "stage": "TRANSFORMER",
  "timestamp": "2025-11-13T10:30:05Z"
}
```



## Error Handling

### Error Categories

| Error Type | HTTP Status | Eventarc Action | Example |
|------------|-------------|-----------------|---------|
| Invalid CloudEvents | 400 | No retry | Missing required fields |
| Invalid path format | 400 | No retry | Cannot parse file_id |
| Transformer timeout | 500 | Retry | Request timeout after 300s |
| Transformer error | 500 | Retry | Transformer returns 500 |
| Backend update failure | - | Log only | Don't fail the request |

### Logging Strategy

**Structured JSON Logs**:
```json
{
  "timestamp": "2025-11-13T10:30:00Z",
  "level": "INFO",
  "correlation_id": "event-id-123",
  "file_id": "abc123",
  "region_id": "region-cz-01",
  "event": "file_classified",
  "mime_type": "application/pdf",
  "category": "text"
}
```

**Log Levels**:
- INFO: Successful processing steps
- WARNING: Retryable errors (Transformer timeout)
- ERROR: Non-retryable errors (invalid payload)



## Configuration

### Environment Variables

```python
class Settings(BaseSettings):
    # Service URLs
    TRANSFORMER_SERVICE_URL: str
    BACKEND_SERVICE_URL: str
    
    # GCP Configuration
    GCP_PROJECT_ID: str
    GCP_REGION: str = "europe-west1"
    
    # Timeouts
    REQUEST_TIMEOUT: int = 300  # seconds
    BACKEND_UPDATE_TIMEOUT: int = 5  # seconds
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Cloud Run
    PORT: int = 8080
```

## Deployment

### Cloud Run Configuration

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: mime-decoder
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/maxScale: "10"
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
      - image: gcr.io/PROJECT_ID/mime-decoder:latest
        resources:
          limits:
            memory: 512Mi
            cpu: "1"
        env:
        - name: TRANSFORMER_SERVICE_URL
          value: "https://transformer-service-xxx.run.app"
        - name: BACKEND_SERVICE_URL
          value: "https://backend-service-xxx.run.app"
        - name: GCP_PROJECT_ID
          value: "eduscale-prod"
        - name: GCP_REGION
          value: "europe-west1"
```

### Health Check

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy", "service": "mime-decoder"}
```

Note: Transformer connectivity check is optional and can be added if needed, but keeping it simple avoids cascading health check failures.



## Testing Strategy

### Unit Tests

1. **test_classifier.py**: Test MIME type classification logic
2. **test_models.py**: Test path parsing and metadata extraction in ProcessingRequest.from_cloud_event()
3. **test_service.py**: Test service orchestration flow with mocked clients

### Integration Tests

1. **test_cloudevents.py**: Test CloudEvents parsing and end-to-end flow
2. **test_clients.py**: Test Transformer and Backend client calls with mocked responses
3. **test_error_handling.py**: Test error scenarios and retries

### Test Fixtures

```python
# tests/fixtures/cloudevents.json
{
  "valid_pdf_event": {
    "specversion": "1.0",
    "type": "google.cloud.storage.object.v1.finalized",
    "data": {
      "bucket": "test-bucket",
      "name": "uploads/region-test/file123.pdf",
      "contentType": "application/pdf",
      "size": "1024"
    }
  }
}
```

## Security Considerations

1. **Authentication**: Cloud Run requires authentication, only Eventarc service account can invoke
2. **No Data Access**: MIME Decoder never reads file content, only metadata
3. **Timeout Protection**: 300s timeout prevents hanging requests
4. **Input Validation**: Strict validation of CloudEvents payload
5. **Regional Deployment**: EU region for data locality

