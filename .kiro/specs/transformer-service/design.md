# Design Document

## Overview

The Transformer Service converts various file formats into text representation. It receives requests from the MIME Decoder, retrieves files from Cloud Storage, performs format-specific transformations (text extraction, ASR, document decoding), and saves extracted text with rich YAML frontmatter metadata to Cloud Storage. The Tabular service independently monitors GCS for new text files and processes them asynchronously.

### Key Design Principles

1. **Format-Specific Processing**: Different handlers for PDF, DOCX, Excel, ODF, text, and audio
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
  - PDF Handler (PDF) → pdfplumber
  - DOCX Handler (DOCX, DOC) → python-docx / antiword
  - Excel Handler (XLSX, XLS) → openpyxl / pandas
  - ODF Handler (ODT, ODS, ODP) → odfpy
  - Text Handler (TXT, CSV, MD, HTML, JSON, XML, RTF) → plain text
  - Audio Handler (MP3, WAV, M4A) → ASR
  - Other → Return 400 error (unsupported, includes PPTX/PPT)
    ↓
Build YAML frontmatter with rich metadata:
  - File identifiers (file_id, region_id, event_id)
  - Original file info (filename, content_type, size, bucket, path, upload time)
  - Extraction details (method, timestamp, duration)
  - Content metrics (text_length, word_count, character_count)
  - Document-specific metadata (page_count, sheet_count, slide_count)
  - Audio-specific metadata (duration, sample_rate, channels, confidence, language)
    ↓
Stream frontmatter + extracted text to Cloud Storage (text/{file_id}.txt)
    ↓
Return status to MIME Decoder
    ↓
[Async] Tabular service detects new file via GCS Event
    ↓
[Async] Tabular reads file, parses frontmatter, processes text
```

### Module Structure

```
src/eduscale/
├── transformer/
│   ├── __init__.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── pdf_handler.py       # PDF extraction
│   │   ├── docx_handler.py      # DOCX, DOC extraction
│   │   ├── excel_handler.py     # XLSX, XLS extraction
│   │   ├── odf_handler.py       # ODT, ODS, ODP extraction
│   │   ├── text_handler.py      # Plain text (TXT, CSV, MD, HTML, JSON, XML, RTF)
│   │   └── audio_handler.py     # ASR for audio files
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
    file_category: Literal["pdf", "docx", "excel", "odf", "text", "audio", "other"]
    size: int = Field(..., description="File size in bytes")

class TransformResponse(BaseModel):
    status: Literal["INGESTED", "FAILED"]
    text_uri: str
    processing_time_ms: int
    metadata: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

class ExtractionMetadata(BaseModel):
    """Metadata for logging purposes only. Not sent to Tabular service."""
    lines: int | None = None  # Number of lines in resulting text file
    page_count: int | None = None  # PDF: number of pages in source
    row_count: int | None = None  # Excel/CSV: number of data rows in source
    sheet_count: int | None = None  # Excel: number of sheets in source
    duration_seconds: float | None = None  # Audio: duration in seconds
    confidence: float | None = None  # ASR: transcription confidence score (0-1)
    language: str | None = None  # Audio: language code (en-US, cs-CZ)
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
    text_uri: str
    processing_time_ms: int
    metadata: dict

@router.post("/api/v1/transformer/transform")
async def transform_file(request: TransformRequest) -> TransformResponse:
    """Transform file to text with frontmatter metadata."""
```

### 2. Storage Client (storage.py)

**Purpose**: Handle Cloud Storage operations with memory-efficient streaming

**Interface**:
```python
async def download_file(bucket: str, object_name: str, local_path: str) -> None:
    """Download file from Cloud Storage."""

async def upload_text_streaming(
    bucket: str,
    object_name: str,
    text_chunks: Iterator[str],
    content_type: str = "text/plain"
) -> str:
    """Upload text to Cloud Storage using streaming approach.

    Memory-efficient upload that writes chunks sequentially without
    loading entire content into memory. Ideal for large documents.

    Args:
        text_chunks: Iterator/generator yielding text chunks (frontmatter, then content)
    """

async def stream_large_file(bucket: str, object_name: str) -> AsyncIterator[bytes]:
    """Stream large file from Cloud Storage."""
```



### 3. PDF Handler (handlers/pdf_handler.py)

**Purpose**: Extract text from PDF documents

**Interface**:
```python
async def extract_text_from_pdf(file_path: str) -> tuple[str, dict]:
    """Extract text from PDF using pdfplumber."""
```

**Implementation Details**:
- Use pdfplumber for better text extraction quality
- Extract text from all pages
- Preserve line breaks and basic formatting
- Return metadata (for logging only, not sent to Tabular):
  - `lines`: Number of lines in resulting text file
  - `page_count`: Number of PDF pages in source

**Libraries**:
- pdfplumber for PDF extraction

### 4. DOCX Handler (handlers/docx_handler.py)

**Purpose**: Extract text from Word documents

**Interface**:
```python
async def extract_text_from_word(file_path: str) -> tuple[str, dict]:
    """Extract text from DOCX or DOC using pandoc."""
```

**Implementation Details**:
- Use pandoc for both DOCX and DOC formats (universal converter)
- Pandoc automatically detects format and converts to plain text
- Preserves table structure and basic formatting
- Return metadata (for logging only, not sent to Tabular):
  - `lines`: Number of lines in resulting text file

**Libraries**:
- pypandoc (Python wrapper for pandoc)

### 5. Excel Handler (handlers/excel_handler.py)

**Purpose**: Extract text from Excel spreadsheets

**Interface**:
```python
async def extract_text_from_xlsx(file_path: str) -> tuple[str, dict]:
    """Extract text from XLSX using openpyxl or pandas."""

async def extract_text_from_xls(file_path: str) -> tuple[str, dict]:
    """Extract text from XLS using xlrd or pandas."""
```

**Implementation Details**:
- XLSX: Use openpyxl or pandas to extract from all sheets
- XLS: Use xlrd or pandas for legacy format
- Format output with sheet names as headers
- Count total rows across all sheets (excluding headers)
- Return metadata (for logging only, not sent to Tabular):
  - `lines`: Number of lines in resulting text file
  - `sheet_count`: Number of sheets in source workbook
  - `row_count`: Total data rows in source (across all sheets)

**Libraries**:
- openpyxl or pandas for Excel spreadsheets (XLSX)
- xlrd or pandas for legacy Excel (XLS)

### 6. Text Handler (handlers/text_handler.py)

**Purpose**: Read plain text files without any transformation

**Interface**:
```python
async def read_plain_text(file_path: str) -> tuple[str, dict]:
    """Read plain text file (TXT, CSV, MD, HTML, JSON, XML, RTF) with UTF-8 encoding.

    No transformation or parsing. Returns raw text for AI analysis.
    Fallback to latin-1 if UTF-8 fails.
    """
```

**Implementation Details**:
- Simple `file.read()` with UTF-8 encoding
- Fallback to latin-1 if UTF-8 decoding fails
- No transformation or parsing - pass raw text to downstream services
- Count lines in source file
- Return metadata (for logging only, not sent to Tabular):
  - `lines`: Number of lines in resulting text file (same as source for plain text)
  - `row_count`: Number of lines in source (for CSV/TXT context)

**Supported Formats**:
- TXT: Plain text files
- CSV: Comma-separated values (no parsing, just raw text)
- MD: Markdown files
- HTML: HTML files (no rendering, just source)
- JSON: JSON files (no parsing, just raw text)
- XML: XML files (no parsing, just raw text)
- RTF: Rich Text Format (as plain text, no escape sequence processing)

**Libraries**:
- Built-in file I/O only (no external dependencies)

### 7. ODF Handler (handlers/odf_handler.py)

**Purpose**: Extract text from OpenDocument Format files

**Interface**:
```python
async def extract_text_from_odf(file_path: str, content_type: str) -> tuple[str, dict]:
    """Extract text from ODT, ODS, or ODP using pandoc."""
```

**Implementation Details**:
- Use pandoc for all OpenDocument formats (universal converter)
- ODT: Extract text from paragraphs and tables
- ODS: Extract text from all sheets
- ODP: Extract text from all slides
- Pandoc automatically handles ZIP structure and XML parsing
- Preserve basic text structure
- Return metadata (for logging only, not sent to Tabular):
  - `lines`: Number of lines in resulting text file

**Libraries**:
- pypandoc (Python wrapper for pandoc)

### 8. Audio Handler (handlers/audio_handler.py)

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
- Return metadata (for logging only, not sent to Tabular):
  - `lines`: Number of lines in resulting text file
  - `duration_seconds`: Audio duration in source
  - `confidence`: ASR confidence score (0-1)
  - `language`: Language code used (en-US, cs-CZ)

**Libraries**:
- google-cloud-speech for ASR
- pydub for audio format conversion
- mutagen for metadata extraction


### 8. Orchestrator (orchestrator.py)

**Purpose**: Coordinate transformation flow

**Interface**:
```python
async def transform_file(request: TransformRequest) -> TransformResponse:
    """Main orchestration function."""

async def route_to_handler(
    file_path: str,
    file_category: str,
    content_type: str
) -> tuple[str, dict]:
    """Route file to appropriate handler based on category."""
```

**Implementation Details**:
- Validate request parameters
- Check file size limits before processing
- Download file to temporary location
- Route based on file_category:
  - "pdf" → pdf_handler
  - "docx" → docx_handler
  - "excel" → excel_handler
  - "odf" → odf_handler
  - "text" → text_handler
  - "audio" → audio_handler
  - "other" → return 400 error (unsupported, includes PPTX/PPT)
- Build YAML frontmatter with comprehensive metadata
- Stream frontmatter + extracted text to Cloud Storage
- Aggregate results and return response
- Clean up temporary files in finally block

**Algorithm**:
1. Validate request (file_id, bucket, object_name)
2. Check file size against MAX_FILE_SIZE_MB
3. Download file from GCS to /tmp/{file_id}_{ext}
4. Route to handler based on file_category
5. Extract text and metadata
6. Build YAML frontmatter with all available metadata
7. Stream to gs://{bucket}/text/{file_id}.txt:
   a. Yield frontmatter
   b. Yield separator (\n)
   c. Yield extracted text
8. Return TransformResponse with status and text_uri
9. Clean up temporary files

**Error Handling**:
- Wrap in try/except with detailed logging
- Return 500 for retryable errors (GCS, extraction)
- Return 400 for permanent errors (invalid format, too large)
- **MANDATORY**: Log ALL errors before returning HTTP response
  - 4xx errors → WARN level with error details
  - 5xx errors → ERROR level with error details and stack trace
- Log all errors with full context (file_id, region_id, operation, duration_ms, http_status)
- Include stack trace for all 5xx errors
- Ensure cleanup in finally block
- Use structured JSON logging format

### 9. Frontmatter Builder

**Purpose**: Generate YAML frontmatter with comprehensive metadata for AI processing

**Interface**:
```python
def build_text_frontmatter(
    file_id: str,
    region_id: str,
    text_uri: str,
    file_category: str,
    extraction_metadata: ExtractionMetadata,
    original_filename: str | None = None,
    original_content_type: str | None = None,
    original_size_bytes: int | None = None,
    bucket: str | None = None,
    object_path: str | None = None,
    event_id: str | None = None,
    uploaded_at: str | None = None,
    extraction_duration_ms: int | None = None,
) -> str:
    """Build YAML frontmatter for text documents."""

def build_audio_frontmatter(
    file_id: str,
    region_id: str,
    text_uri: str,
    file_category: str,
    audio_metadata: AudioMetadata,
    transcript_text: str,
    # ... same optional parameters as above
) -> str:
    """Build YAML frontmatter for audio transcriptions."""
```

**Frontmatter Format**:
```yaml
---
file_id: "abc123"
region_id: "region-cz-01"
event_id: "cloudevent-xyz"
text_uri: "gs://bucket/text/abc123.txt"

original:
  filename: "document.pdf"
  content_type: "application/pdf"
  size_bytes: 123456
  bucket: "bucket-name"
  object_path: "uploads/region/abc123.pdf"
  uploaded_at: "2025-01-14T10:30:00Z"

file_category: "text"

extraction:
  method: "pdfplumber"
  timestamp: "2025-01-14T10:31:00Z"
  duration_ms: 1234
  success: true

content:
  text_length: 5432
  word_count: 987
  character_count: 5432

document:
  page_count: 15
---
```

**How it works**:
1. Transformer builds frontmatter with ALL available metadata
2. Frontmatter is streamed to GCS before the extracted text
3. Tabular service monitors GCS `text/` prefix via Eventarc/GCS Events
4. Tabular receives notification when new file is created
5. Tabular downloads file, parses YAML frontmatter, processes text
6. All metadata is available to Tabular for AI-enhanced processing

**Benefits**:
- Decoupled architecture: Transformer doesn't wait for Tabular
- Retry resilience: Tabular can reprocess files independently
- Rich context: AI has full metadata about original file
- Scalable: GCS Events handle notification delivery

## Configuration

### Environment Variables

```python
class TransformerSettings(BaseSettings):
    # Required
    GCP_PROJECT_ID: str
    GCS_BUCKET_NAME: str

    # Optional with defaults
    GCP_REGION: str = "europe-west1"
    MAX_FILE_SIZE_MB: int = 100
    LOG_LEVEL: str = "INFO"

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
- `storage.objects.create` - Write extracted text with frontmatter to GCS
- `speech.recognize` - Use Speech-to-Text API

### Docker Configuration

```dockerfile
FROM python:3.11-slim

# Install system dependencies for audio/document processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    pandoc \
    poppler-utils \
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
pypandoc>=1.12
openpyxl==3.1.2
xlrd==2.0.1

# Audio processing
pydub==0.25.1
mutagen==1.47.0

# Metadata format
PyYAML>=6.0.1

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

| Error Type | HTTP Status | Log Level | Action | Retry |
|------------|-------------|-----------|--------|-------|
| File not found in GCS | 500 | ERROR | Log with stack trace and return error | Yes (transient) |
| File too large | 400 | WARN | Log error details and return error | No (permanent) |
| Invalid file format | 400 | WARN | Log error details and return error | No (permanent) |
| Unsupported file category | 400 | WARN | Log warning and return error | No (permanent) |
| Extraction failed | 500 | ERROR | Log with stack trace and details | Yes (may succeed) |
| GCS upload failed | 500 | ERROR | Log with stack trace and return error | Yes (transient) |
| Frontmatter build failed | 500 | ERROR | Log with stack trace and return error | Yes (should succeed) |
| Invalid request params | 400 | WARN | Log validation error and return error | No (bad input) |

### Retry Strategy

- Transformer returns 500 for retryable errors (GCS, extraction, frontmatter)
- MIME Decoder will retry via Eventarc (exponential backoff)
- Tabular processes files asynchronously via GCS Events (decoupled)
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
- `http_status` - HTTP status code for error responses

**Log Levels**:
- INFO: Successful operations, processing milestones
- WARNING: Partial failures (Tabular errors, skipped files in archives), **ALL 4xx errors**
- ERROR: Complete failures (extraction failed, GCS errors), **ALL 5xx errors**

**Mandatory Logging for HTTP Errors**:
- EVERY 4xx response MUST be logged at WARN level with error details
- EVERY 5xx response MUST be logged at ERROR level with error details and stack trace
- No exceptions - all HTTP errors must have corresponding log entries
- Logs MUST use structured JSON format for Cloud Logging integration

**Example Log Entry (Success)**:
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

**Example Log Entry (4xx Error)**:
```json
{
  "timestamp": "2024-01-15T10:31:12.456Z",
  "level": "WARNING",
  "message": "File size exceeds maximum allowed limit",
  "file_id": "def456",
  "region_id": "region-cz-02",
  "file_category": "pdf",
  "content_type": "application/pdf",
  "operation": "validate_file_size",
  "duration_ms": 12,
  "http_status": 400,
  "error": "File size 157286400 bytes exceeds limit of 104857600 bytes",
  "file_size_bytes": 157286400,
  "max_size_bytes": 104857600
}
```

**Example Log Entry (5xx Error)**:
```json
{
  "timestamp": "2024-01-15T10:32:30.789Z",
  "level": "ERROR",
  "message": "Failed to extract text from PDF",
  "file_id": "ghi789",
  "region_id": "region-cz-03",
  "file_category": "pdf",
  "content_type": "application/pdf",
  "operation": "extract_pdf",
  "duration_ms": 5432,
  "http_status": 500,
  "error": "PDFSyntaxError: PDF file is corrupted or encrypted",
  "stack_trace": "Traceback (most recent call last):\n  File \"pdf_handler.py\", line 42, in extract_text_from_pdf\n    ...",
  "retry_count": 0
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

**test_pdf_handler.py**
- Test PDF extraction with various PDF types (text-based)
- Test page count and word count extraction
- Test error handling for corrupted PDFs

**test_docx_handler.py**
- Test DOCX extraction with tables and formatting using pandoc
- Test DOC extraction using pandoc
- Test word count and character count extraction
- Test error handling for corrupted DOCX files
- Mock pypandoc for unit tests

**test_excel_handler.py**
- Test XLSX extraction from multiple sheets
- Test XLS extraction with xlrd
- Test sheet count and row count extraction
- Test error handling for corrupted Excel files

**test_text_handler.py**
- Test plain text reading (TXT, CSV, MD, HTML, JSON, XML, RTF)
- Test UTF-8 and latin-1 fallback
- Test that plain text is NOT transformed or parsed
- Test word count and character count extraction
- Test error handling for unreadable files

**test_odf_handler.py**
- Test ODT extraction with paragraphs and tables using pandoc
- Test ODS extraction from multiple sheets using pandoc
- Test ODP extraction from multiple slides using pandoc
- Test word count and character count extraction
- Test error handling for corrupted ODF files
- Mock pypandoc for unit tests

**test_audio_handler.py**
- Test ASR with short audio files (< 60s)
- Test ASR with long audio files (> 60s)
- Test language detection (English, Czech)
- Test audio format conversion
- Test metadata extraction
- Test error handling for invalid audio

**test_storage.py**
- Test file download from GCS
- Test text upload to GCS
- Test streaming for large files
- Test error handling for GCS failures
- Mock GCS client for unit tests

**test_orchestrator.py**
- Test routing to correct handler based on file_category (pdf, docx, excel, odf, text, audio)
- Test file processing flow with frontmatter generation
- Test "other" category returns 400 error (includes PPTX/PPT)
- Test frontmatter is correctly built and streamed
- Test streaming upload to GCS
- Test error handling and cleanup
- Test file size validation

### Integration Tests

**test_transformer_api.py**
- End-to-end test with real PDF file
- End-to-end test with real DOCX file
- End-to-end test with real audio file
- Test with mock GCS
- Test frontmatter is included in uploaded file
- Verify YAML frontmatter can be parsed
- Test error responses

### Test Fixtures

```
tests/fixtures/
├── sample.pdf           # 2-page PDF with text
├── sample.docx          # Word doc with table
├── sample.txt           # Plain text file
├── sample.csv           # CSV with headers
├── sample.mp3           # 30-second audio
├── sample_long.mp3      # 90-second audio
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

