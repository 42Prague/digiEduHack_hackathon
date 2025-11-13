# Design Document

## Overview

The Transformer Service converts various file formats into text representation. It receives requests from the MIME Decoder, retrieves files from Cloud Storage, performs format-specific transformations (text extraction, ASR, archive unpacking), saves extracted text to Cloud Storage, and forwards text URIs to the Tabular service for structured data analysis.

### Key Design Principles

1. **Format-Specific Processing**: Different handlers for text, audio, archives
2. **Streaming for Large Files**: Memory-efficient processing
3. **Async Processing**: Non-blocking I/O for Cloud Storage and API calls
4. **Fail-Fast**: Clear errors for unprocessable files
5. **Scalable**: Cloud Run scales based on processing load

## Architecture

### High-Level Flow

```
MIME Decoder → Transformer
    ↓
Retrieve file from Cloud Storage
    ↓
Route to format-specific handler:
  - Text Handler (PDF, DOCX, TXT, CSV)
  - Audio Handler (MP3, WAV, M4A) → ASR
  - Archive Handler (ZIP, TAR) → Unpack → Process each
    ↓
Save extracted text to Cloud Storage (text/{file_id}.txt)
    ↓
Call Tabular service with text_uri
    ↓
Return status to MIME Decoder
```

### Module Structure

```
src/eduscale/
├── transformer/
│   ├── __init__.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── text_handler.py      # PDF, DOCX, TXT extraction
│   │   ├── audio_handler.py     # ASR for audio files
│   │   └── archive_handler.py   # ZIP, TAR unpacking
│   ├── storage.py               # Cloud Storage operations
│   └── orchestrator.py          # Main processing logic
├── api/
│   └── v1/
│       └── routes_transformer.py # FastAPI endpoints
└── core/
    └── config.py                # Configuration (extended)
```



## Data Models

### Request/Response Models

```python
from pydantic import BaseModel, Field
from typing import Literal

class TransformRequest(BaseModel):
    file_id: str = Field(..., description="Unique file identifier")
    region_id: str = Field(..., description="Region identifier")
    bucket: str = Field(..., description="GCS bucket name")
    object_name: str = Field(..., description="GCS object path")
    content_type: str = Field(..., description="MIME type")
    file_category: Literal["text", "audio", "archive", "other"]
    size: int = Field(..., description="File size in bytes")

class TransformResponse(BaseModel):
    status: Literal["INGESTED", "FAILED"]
    text_uri: str | list[str]  # Single URI or list for archives
    processing_time_ms: int
    tabular_status: dict | None = None
    metadata: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

class ExtractionMetadata(BaseModel):
    extraction_method: str  # "pdfplumber", "python-docx", "speech-to-text", etc.
    word_count: int | None = None
    page_count: int | None = None
    duration_seconds: float | None = None  # For audio
    confidence: float | None = None  # For ASR
    language: str | None = None
```

## Components and Interfaces

### 1. API Endpoint (routes_transformer.py)

**Purpose**: Receive processing requests from MIME Decoder

**Interface**:
```python
@dataclass
class TransformRequest:
    file_id: str
    region_id: str
    bucket: str
    object_name: str
    content_type: str
    file_category: str
    size: int

@dataclass
class TransformResponse:
    status: Literal["INGESTED", "FAILED"]
    text_uri: str | list[str]  # Single or multiple for archives
    processing_time_ms: int
    tabular_status: dict | None

@router.post("/api/v1/transformer/transform")
async def transform_file(request: TransformRequest) -> TransformResponse:
    """Transform file to text and forward to Tabular."""
```

### 2. Storage Client (storage.py)

**Purpose**: Handle Cloud Storage operations

**Interface**:
```python
async def download_file(bucket: str, object_name: str, local_path: str) -> None:
    """Download file from Cloud Storage."""

async def upload_text(bucket: str, text_uri: str, content: str) -> str:
    """Upload extracted text to Cloud Storage."""

async def stream_large_file(bucket: str, object_name: str) -> AsyncIterator[bytes]:
    """Stream large file from Cloud Storage."""
```



### 3. Text Handler (handlers/text_handler.py)

**Purpose**: Extract text from documents

**Interface**:
```python
async def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using PyPDF2 or pdfplumber."""

async def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX using python-docx."""

async def extract_text_from_plain(file_path: str) -> str:
    """Read plain text file with UTF-8 encoding."""

async def extract_text(file_path: str, content_type: str) -> tuple[str, dict]:
    """Route to appropriate extraction method and return text + metadata."""
```

**Implementation Details**:
- PDF: Use pdfplumber for better text extraction quality
- DOCX: Use python-docx to extract paragraphs and tables
- Plain text: Read with UTF-8 encoding, fallback to latin-1
- CSV/Excel: Read as plain text to preserve structure
- Return metadata: page count, word count, extraction method

**Libraries**:
- pdfplumber for PDF (better than PyPDF2)
- python-docx for Word documents
- Built-in file I/O for plain text

### 4. Audio Handler (handlers/audio_handler.py)

**Purpose**: Transcribe audio to text using ASR

**Interface**:
```python
async def transcribe_audio(file_path: str, language: str = "en-US") -> tuple[str, dict]:
    """Transcribe audio using Google Cloud Speech-to-Text."""

async def get_audio_metadata(file_path: str) -> dict:
    """Extract audio metadata (duration, format, sample rate)."""
```

**Implementation Details**:
- Use Google Cloud Speech-to-Text API v2
- Support languages: English (en-US), Czech (cs-CZ)
- For files > 60 seconds, use long-running recognition
- For files < 60 seconds, use synchronous recognition
- Convert audio to LINEAR16 if needed (using pydub)
- Return metadata: duration, format, sample rate, confidence scores

**Libraries**:
- google-cloud-speech for ASR
- pydub for audio format conversion
- mutagen for metadata extraction

### 5. Archive Handler (handlers/archive_handler.py)

**Purpose**: Unpack archives and process contents

**Interface**:
```python
async def unpack_and_process(
    file_path: str, 
    file_id: str, 
    bucket: str,
    region_id: str,
    depth: int = 0
) -> list[dict]:
    """Unpack archive and return list of processed file results."""

async def detect_archive_format(file_path: str) -> str:
    """Detect archive format from file signature."""
```

**Implementation Details**:
- Support formats: ZIP, TAR, TAR.GZ, TAR.BZ2
- Unpack to temporary directory with unique name
- Process each file by detecting its MIME type
- Recursively handle nested archives (max depth: 2)
- Generate unique text URIs: gs://bucket/text/{file_id}_001.txt
- Clean up temporary files after processing
- Return list of results with metadata for each file

**Algorithm**:
1. Detect archive format using magic bytes
2. Unpack to /tmp/{file_id}_{timestamp}/
3. Iterate through extracted files
4. For each file:
   - Detect MIME type
   - Route to appropriate handler (text/audio/archive)
   - Save extracted text with sequential naming
5. Clean up temporary directory
6. Return list of text URIs and metadata

**Libraries**:
- zipfile (built-in) for ZIP
- tarfile (built-in) for TAR formats
- python-magic for MIME detection



### 6. Orchestrator (orchestrator.py)

**Purpose**: Coordinate transformation flow

**Interface**:
```python
async def transform_file(request: TransformRequest) -> TransformResponse:
    """Main orchestration function."""

async def route_to_handler(
    file_path: str, 
    file_category: str, 
    content_type: str
) -> tuple[str | list[str], dict]:
    """Route file to appropriate handler based on category."""
```

**Implementation Details**:
- Validate request parameters
- Check file size limits before processing
- Download file to temporary location
- Route based on file_category:
  - "text" → text_handler
  - "audio" → audio_handler
  - "archive" → archive_handler
  - "other" → attempt text extraction
- Handle both single and multiple text outputs (archives)
- Upload extracted text(s) to Cloud Storage
- Call Tabular service for each text URI
- Aggregate results and return response
- Clean up temporary files in finally block

**Algorithm**:
1. Validate request (file_id, bucket, object_name)
2. Check file size against MAX_FILE_SIZE_MB
3. Download file from GCS to /tmp/{file_id}_{ext}
4. Route to handler based on file_category
5. Extract text (single or multiple)
6. For each extracted text:
   - Upload to gs://{bucket}/text/{file_id}[_NNN].txt
   - Call Tabular service with text_uri
7. Aggregate Tabular responses
8. Return TransformResponse with status and text_uri(s)
9. Clean up temporary files

**Error Handling**:
- Wrap in try/except with detailed logging
- Return 500 for retryable errors (GCS, extraction)
- Return 400 for permanent errors (invalid format, too large)
- Log all errors with full context
- Ensure cleanup in finally block

### 7. Tabular Client

**Purpose**: Forward text to Tabular service

**Interface**:
```python
async def call_tabular(
    file_id: str, 
    region_id: str, 
    text_uri: str, 
    original_content_type: str,
    extraction_metadata: dict
) -> dict:
    """Call Tabular service to analyze text."""
```

**Implementation Details**:
- Use httpx.AsyncClient for async HTTP calls
- Set timeout to 600 seconds (10 minutes)
- Include authentication headers for Cloud Run service-to-service
- Retry on transient failures (503, connection errors)
- Log request and response for debugging
- Return full response including status and any warnings

**Request to Tabular**:
```json
{
  "file_id": "abc123",
  "region_id": "region-cz-01",
  "text_uri": "gs://bucket/text/abc123.txt",
  "original_content_type": "application/pdf",
  "extraction_metadata": {
    "pages": 5,
    "word_count": 1234,
    "extraction_method": "pdfplumber"
  }
}
```

**Response from Tabular**:
```json
{
  "status": "INGESTED",
  "rows_loaded": 42,
  "issues": [],
  "warnings": ["Missing header row"]
}
```

**Error Handling**:
- Catch httpx exceptions (timeout, connection errors)
- Log Tabular errors but don't fail the Transformer request
- Return None if Tabular call fails (text extraction still succeeded)

## Configuration

### Environment Variables

```python
class TransformerSettings(BaseSettings):
    # Required
    TABULAR_SERVICE_URL: str  # e.g., https://tabular-service-xyz.run.app
    GCP_PROJECT_ID: str
    GCS_BUCKET_NAME: str
    
    # Optional with defaults
    GCP_REGION: str = "europe-west1"
    MAX_FILE_SIZE_MB: int = 100
    MAX_ARCHIVE_SIZE_MB: int = 500
    TESSERACT_LANG: str = "eng+ces"  # For OCR (future)
    LOG_LEVEL: str = "INFO"
    REQUEST_TIMEOUT: int = 600
    
    # Speech-to-Text
    SPEECH_LANGUAGE_EN: str = "en-US"
    SPEECH_LANGUAGE_CS: str = "cs-CZ"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
```

### Configuration Validation

- Validate at startup that required environment variables are set
- Log configuration (excluding sensitive values) at startup
- Fail fast if TABULAR_SERVICE_URL is not accessible
- Check GCS bucket exists and is accessible

## Deployment

### Cloud Run Configuration

```yaml
service: transformer-service
region: europe-west1
memory: 2Gi
cpu: 2
timeout: 900s
max-instances: 20
min-instances: 0
concurrency: 10
ingress: internal  # Only accessible from within GCP
```

### Service Account Permissions

The Transformer service account needs:
- `storage.objects.get` - Read files from GCS
- `storage.objects.create` - Write extracted text to GCS
- `cloudrun.services.invoke` - Call Tabular service
- `speech.recognize` - Use Speech-to-Text API

### Docker Configuration

```dockerfile
FROM python:3.11-slim

# Install system dependencies for audio/document processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
CMD ["uvicorn", "src.eduscale.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Python Dependencies

```txt
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Google Cloud
google-cloud-storage==2.10.0
google-cloud-speech==2.21.0

# Document processing
pdfplumber==0.10.3
python-docx==1.1.0

# Audio processing
pydub==0.25.1
mutagen==1.47.0

# Archive handling
python-magic==0.4.27

# HTTP client
httpx==0.25.2

# Logging
structlog==23.2.0
```

### Deployment Steps

1. Build Docker image: `docker build -t gcr.io/{project}/transformer-service .`
2. Push to GCR: `docker push gcr.io/{project}/transformer-service`
3. Deploy to Cloud Run: `gcloud run deploy transformer-service --image gcr.io/{project}/transformer-service`
4. Set environment variables via Cloud Run console or gcloud CLI
5. Configure service account with required permissions
6. Test health endpoint: `curl https://transformer-service-xyz.run.app/health`



## Error Handling

### Error Categories

| Error Type | HTTP Status | Action | Retry |
|------------|-------------|--------|-------|
| File not found in GCS | 500 | Log and return error | Yes (transient) |
| File too large | 400 | Log and return error | No (permanent) |
| Invalid file format | 400 | Log and return error | No (permanent) |
| Extraction failed | 500 | Log with details | Yes (may succeed) |
| GCS upload failed | 500 | Log and return error | Yes (transient) |
| Tabular call failed | 200 | Log warning only | N/A (non-blocking) |
| Invalid request params | 400 | Return validation error | No (bad input) |
| Archive too large | 400 | Log and return error | No (permanent) |
| Nested archive depth exceeded | 400 | Log and skip | No (by design) |

### Retry Strategy

- Transformer returns 500 for retryable errors (GCS, extraction)
- MIME Decoder will retry via Eventarc (exponential backoff)
- Tabular failures don't fail the Transformer request (text extraction succeeded)
- Maximum 3 retries for transient errors

### Logging Strategy

All logs include:
- `file_id` - Unique file identifier
- `region_id` - Region identifier
- `file_category` - File type category
- `content_type` - MIME type
- `operation` - Current operation (download, extract, upload, etc.)
- `duration_ms` - Operation duration
- `error` - Error message and stack trace (if applicable)

**Log Levels**:
- INFO: Successful operations, processing milestones
- WARNING: Partial failures (Tabular errors, skipped files in archives)
- ERROR: Complete failures (extraction failed, GCS errors)

**Example Log Entry**:
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "message": "Text extraction completed",
  "file_id": "abc123",
  "region_id": "region-cz-01",
  "file_category": "text",
  "content_type": "application/pdf",
  "operation": "extract_pdf",
  "duration_ms": 1234,
  "metadata": {
    "pages": 5,
    "word_count": 1234
  }
}
```

### Exception Handling

```python
class TransformerException(Exception):
    """Base exception for Transformer errors."""
    pass

class FileTooLargeError(TransformerException):
    """File exceeds size limit."""
    pass

class ExtractionError(TransformerException):
    """Text extraction failed."""
    pass

class StorageError(TransformerException):
    """GCS operation failed."""
    pass
```

## Testing Strategy

### Unit Tests

**test_text_handler.py**
- Test PDF extraction with various PDF types (text-based, scanned)
- Test DOCX extraction with tables and formatting
- Test plain text with different encodings (UTF-8, latin-1)
- Test CSV/Excel preservation
- Test error handling for corrupted files

**test_audio_handler.py**
- Test ASR with short audio files (< 60s)
- Test ASR with long audio files (> 60s)
- Test language detection (English, Czech)
- Test audio format conversion
- Test metadata extraction
- Test error handling for invalid audio

**test_archive_handler.py**
- Test ZIP unpacking with various file types
- Test TAR/TAR.GZ unpacking
- Test nested archive handling (depth limit)
- Test sequential naming (file_id_001.txt, etc.)
- Test error handling for corrupted archives
- Test size limit enforcement

**test_storage.py**
- Test file download from GCS
- Test text upload to GCS
- Test streaming for large files
- Test error handling for GCS failures
- Mock GCS client for unit tests

**test_orchestrator.py**
- Test routing to correct handler based on file_category
- Test single file processing flow
- Test archive processing flow (multiple outputs)
- Test Tabular service integration
- Test error handling and cleanup
- Test file size validation

### Integration Tests

**test_transformer_api.py**
- End-to-end test with real PDF file
- End-to-end test with real DOCX file
- End-to-end test with real audio file
- End-to-end test with real archive
- Test with mock GCS and Tabular service
- Test error responses

**test_tabular_integration.py**
- Test successful Tabular call
- Test Tabular timeout handling
- Test Tabular error handling (non-blocking)
- Test authentication headers

### Test Fixtures

```
tests/fixtures/
├── sample.pdf           # 2-page PDF with text
├── sample.docx          # Word doc with table
├── sample.txt           # Plain text file
├── sample.csv           # CSV with headers
├── sample.mp3           # 30-second audio
├── sample_long.mp3      # 90-second audio
├── sample.zip           # Archive with mixed files
├── nested.zip           # Archive with nested archive
├── corrupted.pdf        # Invalid PDF for error testing
└── empty.txt            # Empty file
```

### Test Coverage Goals

- Minimum 80% code coverage
- All error paths tested
- All file format handlers tested
- Integration with GCS and Tabular mocked

## Security

1. **No External APIs**: ASR uses Google Cloud (same project)
2. **File Size Limits**: Prevent resource exhaustion
3. **Temporary File Cleanup**: Delete after processing
4. **Regional Processing**: EU region only
5. **Service Account**: Minimal permissions (GCS read, Speech-to-Text)

