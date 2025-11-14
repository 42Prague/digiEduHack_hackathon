# Requirements Document

## Introduction

The Transformer Service is a processing microservice that converts various file formats into text representation with rich metadata. It receives requests from the MIME Decoder, retrieves files from Cloud Storage, performs format-specific transformations (text extraction, ASR), and saves the extracted text with YAML frontmatter metadata to Cloud Storage. The Tabular service asynchronously discovers and processes these files via GCS Events.

The Transformer operates as part of the pipeline: MIME Decoder → **Transformer** → Cloud Storage → [GCS Event] → Tabular → BigQuery.

## Glossary

- **Transformer Service**: Microservice that converts files to text format
- **PDF Extraction**: Process of extracting text from PDF documents using pdfplumber
- **DOCX Extraction**: Process of extracting text from Word documents (DOCX, DOC) using pandoc
- **Excel Extraction**: Process of extracting text from Excel spreadsheets (XLSX, XLS) using openpyxl/xlrd
- **ODF Extraction**: Process of extracting text from OpenDocument formats (ODT, ODS, ODP) using pandoc
- **Text Extraction**: Process of reading plain text files without any transformation (TXT, CSV, MD, HTML, JSON, XML, RTF are plain text)
- **Pandoc**: Universal document converter that handles DOCX, DOC, ODT, ODS, ODP and other formats
- **ASR**: Automatic Speech Recognition for transcribing audio to text
- **Frontmatter**: YAML metadata block at the beginning of text files with file info, extraction details, and content metrics
- **Streaming Upload**: Memory-efficient approach that writes chunks sequentially without loading entire content
- **Text URI**: Cloud Storage URI pointing to extracted text (e.g., gs://bucket/text/file_id.txt)
- **Tabular Service**: Downstream service that monitors GCS, parses frontmatter, and loads text to BigQuery
- **File Category**: Classification from MIME Decoder (pdf, docx, excel, odf, text, audio, other)

## Requirements

### Requirement 1: File Retrieval from Cloud Storage

**User Story:** As a developer, I want the Transformer to retrieve files from Cloud Storage, so that it can process uploaded files.

#### Acceptance Criteria

1. WHEN a processing request is received, THE Transformer SHALL retrieve the file from Cloud Storage using the provided bucket and object name
2. THE Transformer SHALL use the google-cloud-storage client library for file retrieval
3. WHEN the file size exceeds 100MB, THE Transformer SHALL stream the file instead of loading it entirely into memory
4. WHEN the file cannot be retrieved, THE Transformer SHALL return HTTP 500 with error details
5. THE Transformer SHALL log the file retrieval operation with file size and duration



### Requirement 2: PDF Extraction

**User Story:** As a data engineer, I want text extracted from PDF documents, so that tabular data can be analyzed.

#### Acceptance Criteria

1. WHEN the file category is "pdf", THE Transformer SHALL extract text using pdfplumber
2. WHEN PDF extraction completes, THE Transformer SHALL return lines (number of lines in resulting text file) and page_count (number of PDF pages in source) in metadata
3. WHEN PDF extraction fails, THE Transformer SHALL log the error and return HTTP 500
4. THE Transformer SHALL preserve line breaks and basic formatting in extracted text

### Requirement 3: DOCX Extraction

**User Story:** As a data engineer, I want text extracted from Word documents, so that document content can be analyzed.

#### Acceptance Criteria

1. WHEN the file category is "docx", THE Transformer SHALL extract text from DOCX files using pandoc
2. WHEN the file category is "docx", THE Transformer SHALL extract text from DOC files using pandoc
3. WHEN DOCX extraction completes, THE Transformer SHALL return lines (number of lines in resulting text file) in metadata
4. WHEN the document contains tables, THE Transformer SHALL extract table content as text
5. WHEN DOCX extraction fails, THE Transformer SHALL log the error and return HTTP 500
6. THE Transformer SHALL preserve line breaks and basic formatting in extracted text

### Requirement 4: Excel Extraction

**User Story:** As a data engineer, I want text extracted from Excel spreadsheets, so that tabular data can be analyzed.

#### Acceptance Criteria

1. WHEN the file category is "excel", THE Transformer SHALL extract text from XLSX files using openpyxl or pandas
2. WHEN the file category is "excel", THE Transformer SHALL extract text from XLS files using xlrd or pandas
3. WHEN Excel extraction completes, THE Transformer SHALL extract text from all sheets
4. WHEN Excel extraction completes, THE Transformer SHALL return lines (number of lines in resulting text file), sheet_count (number of sheets in source), and row_count (total data rows in source) in metadata
5. THE Transformer SHALL format output with sheet names as headers
6. WHEN Excel extraction fails, THE Transformer SHALL log the error and return HTTP 500

### Requirement 5: ODF Extraction

**User Story:** As a data engineer, I want text extracted from OpenDocument formats, so that content can be analyzed.

#### Acceptance Criteria

1. WHEN the file category is "odf", THE Transformer SHALL extract text from ODT files using pandoc
2. WHEN the file category is "odf", THE Transformer SHALL extract text from ODS files using pandoc
3. WHEN the file category is "odf", THE Transformer SHALL extract text from ODP files using pandoc
4. WHEN ODF extraction completes for ODS files, THE Transformer SHALL extract text from all sheets
5. WHEN ODF extraction completes for ODP files, THE Transformer SHALL extract text from all slides
6. WHEN ODF extraction completes, THE Transformer SHALL return lines (number of lines in resulting text file) in metadata
7. WHEN ODF extraction fails, THE Transformer SHALL log the error and return HTTP 500
8. THE Transformer SHALL preserve basic text structure in extracted content

### Requirement 6: Text Extraction

**User Story:** As a data engineer, I want text extracted from plain text files, so that content can be analyzed by AI.

#### Acceptance Criteria

1. WHEN the file category is "text", THE Transformer SHALL read the file as UTF-8 text (TXT, CSV, MD, HTML, JSON, XML, RTF)
2. WHEN the file is plain text, THE Transformer SHALL NOT perform any transformation or parsing
3. THE Transformer SHALL save the raw text with frontmatter to Cloud Storage for downstream processing
4. WHEN UTF-8 decoding fails, THE Transformer SHALL try latin-1 as fallback
5. THE Transformer SHALL return lines (number of lines in resulting text file) and row_count (number of lines in source) in metadata
6. WHEN text reading fails, THE Transformer SHALL log the error and return HTTP 500

### Requirement 7: ASR for Audio Files

**User Story:** As a data engineer, I want audio transcribed to text, so that spoken content can be analyzed.

#### Acceptance Criteria

1. WHEN the file category is "audio", THE Transformer SHALL use speech recognition to transcribe audio to text
2. THE Transformer SHALL support common audio formats (MP3, WAV, M4A, OGG)
3. THE Transformer SHALL use Google Cloud Speech-to-Text API or similar service
4. WHEN transcription is performed, THE Transformer SHALL specify language (English or Czech)
5. WHEN the audio contains no speech, THE Transformer SHALL return empty text with a warning
6. WHEN ASR fails, THE Transformer SHALL log the error and return HTTP 500
7. THE Transformer SHALL include audio metadata (duration, format) in logs

### Requirement 8: Unsupported File Categories

**User Story:** As a system architect, I want unsupported file types handled gracefully, so that the system doesn't crash on unexpected inputs.

#### Acceptance Criteria

1. WHEN the file category is "other", THE Transformer SHALL return HTTP 400 with error message "Unsupported file type"
2. WHEN the file category is "other", THE Transformer SHALL log a warning with file_id, content_type, and category
3. WHEN the file category is not one of (pdf, docx, excel, odf, text, audio), THE Transformer SHALL return HTTP 400
4. THE Transformer SHALL NOT attempt to process files with unsupported categories
5. THE response SHALL include clear error message indicating which file types are supported

### Requirement 9: Text Storage with Frontmatter to Cloud Storage

**User Story:** As a system architect, I want extracted text with rich metadata saved to Cloud Storage, so that downstream services have full context for AI processing.

#### Acceptance Criteria

1. WHEN text extraction completes, THE Transformer SHALL build YAML frontmatter with comprehensive metadata
2. THE frontmatter SHALL include: file_id, region_id, event_id, text_uri, original file info, extraction details, content metrics, and document-specific metadata
3. THE Transformer SHALL stream the frontmatter + extracted text to Cloud Storage using memory-efficient approach
4. THE text file SHALL be saved to gs://{bucket}/text/{file_id}.txt
5. THE Transformer SHALL use UTF-8 encoding for all text files
6. THE streaming upload SHALL yield frontmatter first, then separator, then extracted text
7. WHEN saving fails, THE Transformer SHALL log the error and return HTTP 500
8. THE Transformer SHALL return the text_uri in the response
9. THE Transformer SHALL use streaming upload to avoid loading large texts into memory

### Requirement 10: Decoupled Tabular Service Integration

**User Story:** As a system architect, I want the Transformer decoupled from the Tabular service, so that the system is more scalable and resilient.

#### Acceptance Criteria

1. WHEN text with frontmatter is saved to Cloud Storage, THE Transformer SHALL complete its processing and return success
2. THE Transformer SHALL NOT make direct HTTP calls to the Tabular service
3. THE Tabular service SHALL independently monitor the `text/` prefix in Cloud Storage via GCS Events (Eventarc)
4. WHEN a new text file is created, GCS SHALL emit an event that triggers the Tabular service
5. THE Tabular service SHALL download the file, parse the YAML frontmatter, and process the text
6. THE Transformer SHALL include ALL relevant metadata in the frontmatter for AI processing
7. THE decoupled architecture SHALL allow Tabular to reprocess files independently of Transformer
8. THE Transformer response SHALL NOT include Tabular service status (async processing)

### Requirement 11: Error Handling and Logging

**User Story:** As a DevOps engineer, I want comprehensive error logging, so that I can debug transformation failures.

#### Acceptance Criteria

1. WHEN any error occurs, THE Transformer SHALL log the error with full context (file_id, region_id, file_category, error message, stack trace)
2. THE Transformer SHALL use structured logging with JSON format
3. THE Transformer SHALL log at appropriate levels (INFO for success, WARNING for partial failures, ERROR for complete failures)
4. WHEN a file cannot be processed, THE Transformer SHALL return HTTP 500 to trigger MIME Decoder retry
5. THE Transformer SHALL include processing duration in all logs
6. THE Transformer SHALL include correlation IDs for request tracing
7. WHEN returning HTTP 4xx error, THE Transformer SHALL log at WARN level with error details
8. WHEN returning HTTP 5xx error, THE Transformer SHALL log at ERROR level with error details and stack trace
9. THE logging SHALL be mandatory for ALL HTTP error responses (4xx and 5xx), with no exceptions

### Requirement 12: Health Check and Monitoring

**User Story:** As a DevOps engineer, I want health check endpoints, so that Cloud Run can monitor service health.

#### Acceptance Criteria

1. THE Transformer SHALL expose a GET /health endpoint
2. WHEN the service is healthy, THE /health endpoint SHALL return HTTP 200 with status "healthy"
3. THE /health endpoint SHALL check connectivity to Cloud Storage
4. WHEN Cloud Storage is unavailable, THE /health endpoint SHALL return HTTP 503
5. THE /health endpoint SHALL respond within 10 seconds

### Requirement 13: Configuration Management

**User Story:** As a DevOps engineer, I want configuration via environment variables, so that I can deploy to different environments.

#### Acceptance Criteria

1. THE Transformer SHALL read GCP_PROJECT_ID, GCP_REGION, and GCS_BUCKET_NAME from environment variables
2. THE Transformer SHALL read MAX_FILE_SIZE_MB with default 100MB
3. THE Transformer SHALL read LOG_LEVEL from environment variables with default "INFO"
4. THE Transformer SHALL read SPEECH_LANGUAGE_EN and SPEECH_LANGUAGE_CS for audio transcription
5. THE configuration SHALL be validated at startup and log errors for missing required variables

### Requirement 14: Cloud Run Deployment

**User Story:** As a DevOps engineer, I want the Transformer deployed on Cloud Run, so that it scales with processing load.

#### Acceptance Criteria

1. THE Transformer SHALL be deployed as a Cloud Run service in the EU region
2. THE Cloud Run service SHALL be configured with 2GB memory minimum (for document processing and ASR)
3. THE Cloud Run service SHALL be configured with 2 vCPUs
4. THE Cloud Run service SHALL scale from 0 to 20 instances based on request load
5. THE Cloud Run service SHALL have a request timeout of 900 seconds (15 minutes for large files)
6. THE Cloud Run service SHALL require authentication for invocation
