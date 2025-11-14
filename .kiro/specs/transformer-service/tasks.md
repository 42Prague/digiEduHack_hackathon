# Implementation Plan

- [ ] 1. Set up project structure and core configuration
  - Create transformer module directory structure
  - Extend core/config.py with Transformer settings
  - Add new dependencies to requirements.txt
  - Verify configuration loads correctly
  - _Requirements: 10_

- [ ] 1.1 Create transformer module structure
  - Create src/eduscale/transformer/ directory
  - Create src/eduscale/transformer/__init__.py
  - Create src/eduscale/transformer/handlers/ directory
  - Create src/eduscale/transformer/handlers/__init__.py
  - _Requirements: 10_

- [x] 1.2 Extend configuration settings
  - Add TransformerSettings class to src/eduscale/core/config.py
  - Include MAX_FILE_SIZE_MB, MAX_ARCHIVE_SIZE_MB
  - Include SPEECH_LANGUAGE_EN, SPEECH_LANGUAGE_CS settings
  - Add configuration validation at startup
  - _Requirements: 10, 13_

- [x] 1.3 Update requirements.txt with new dependencies
  - Add pdfplumber>=0.10.3 for PDF extraction
  - Add pypandoc>=1.12 for universal document conversion (DOCX, DOC, ODT, ODS, ODP)
  - Add openpyxl>=3.1.2 for Excel spreadsheets
  - Add xlrd>=2.0.1 for legacy Excel format
  - Add google-cloud-speech>=2.21.0 for ASR
  - Add pydub>=0.25.1 for audio processing
  - Add mutagen>=1.47.0 for audio metadata
  - Add PyYAML>=6.0.1 for frontmatter generation
  - Add structlog>=23.2.0 for structured logging
  - _Requirements: 9, 10_

- [ ] 1.4 Test configuration loading
  - Create tests/test_transformer_config.py
  - Test TransformerSettings loads with valid environment variables
  - Test configuration validation catches missing required variables
  - Test default values are applied correctly
  - Run tests to verify configuration works
  - _Requirements: 10_

- [ ] 2. Implement Cloud Storage operations
  - Create storage.py module with GCS client
  - Implement file download from Cloud Storage
  - Implement text upload to Cloud Storage
  - Implement streaming for large files
  - Test storage operations with mocked GCS
  - _Requirements: 1, 5_

- [x] 2.1 Create storage client module
  - Create src/eduscale/transformer/storage.py
  - Initialize google-cloud-storage client
  - Implement download_file() function for downloading files from GCS
  - Implement upload_text_streaming() function for streaming text with frontmatter to GCS
  - Implement stream_large_file() for files > 100MB
  - Implement get_file_size() for checking file size
  - _Requirements: 1, 9_

- [ ] 2.2 Add error handling for storage operations
  - Handle GCS exceptions (NotFound, Forbidden, etc.)
  - Add retry logic for transient failures
  - Log all storage operations with duration
  - _Requirements: 1, 5, 7_

- [x] 2.3 Test storage operations
  - Create tests/transformer/test_storage.py
  - Mock google-cloud-storage client
  - Test download_file() with valid file
  - Test upload_text_streaming() saves text correctly with streaming
  - Test get_file_size() returns correct size
  - Test error handling for NotFound and other GCS exceptions
  - Test retry logic for transient failures
  - Run tests to verify storage operations work
  - _Requirements: 1, 9, 11_

- [ ] 3. Implement Text Handler for document extraction
  - Create text_handler.py module
  - Implement PDF text extraction
  - Implement DOCX text extraction
  - Implement plain text reading
  - Create test fixtures and verify extraction works
  - _Requirements: 2_

- [ ] 3.1 Create text handler module
  - Create src/eduscale/transformer/handlers/text_handler.py
  - Implement extract_text_from_pdf() using pdfplumber
  - Implement extract_text_from_docx() using python-docx
  - Implement extract_text_from_plain() with UTF-8 and latin-1 fallback
  - Implement extract_text() router function based on content_type
  - _Requirements: 2_

- [ ] 3.1.1 Implement Office document extractors for modern formats
  - Implement extract_text_from_xlsx() using openpyxl to extract from all sheets
  - Implement extract_text_from_pptx() using python-pptx to extract from all slides
  - Include slide notes and shapes text in PPTX extraction
  - Format XLSX output with sheet names as headers
  - _Requirements: 2_

- [ ] 3.1.2 Implement OpenDocument format extractors
  - Implement extract_text_from_odt() using odfpy for text documents
  - Implement extract_text_from_ods() using odfpy for spreadsheets
  - Implement extract_text_from_odp() using odfpy for presentations
  - Parse XML content from OpenDocument ZIP structure
  - _Requirements: 2_

- [ ] 3.1.3 Implement legacy Office format extractors
  - Implement extract_text_from_doc() using antiword system command
  - Implement extract_text_from_ppt() using textract library
  - Implement extract_text_from_rtf() using striprtf library
  - Add fallback to textract if antiword fails for DOC files
  - Handle encoding issues in legacy formats
  - _Requirements: 2_

- [ ] 3.2 Add metadata extraction for text files
  - Extract page count from PDF files
  - Extract word count from all text
  - Return ExtractionMetadata with extraction_method
  - _Requirements: 2_

- [x] 3.2.1 Implement YAML frontmatter builder for text files
  - Create build_text_frontmatter() function in text_handler.py
  - Include file identifiers (file_id, region_id, event_id)
  - Include original file info (filename, content_type, size_bytes, bucket, object_path, uploaded_at)
  - Include extraction details (extracted_at, file_category, extraction_method, extraction_duration_ms)
  - Include content metrics (lines, page_count for PDFs, sheet_count for Excel, row_count for CSV)
  - Include document-specific metadata based on file type
  - Format as YAML with --- delimiters
  - _Requirements: 9_

- [ ] 3.3 Create test fixtures and test text extraction
  - Create tests/fixtures/ directory
  - Create tests/fixtures/sample.pdf (simple 2-page PDF with text)
  - Create tests/fixtures/sample.docx (Word doc with paragraphs)
  - Create tests/fixtures/sample.txt (plain text UTF-8)
  - Create tests/fixtures/sample_latin1.txt (latin-1 encoded text)
  - Create tests/fixtures/corrupted.pdf (invalid PDF for error testing)
  - _Requirements: 2_

- [ ] 3.3.1 Create Office document test fixtures
  - Create tests/fixtures/sample.xlsx (Excel file with 2 sheets and data)
  - Create tests/fixtures/sample.pptx (PowerPoint with 3 slides)
  - Create tests/fixtures/sample.odt (OpenDocument text with formatting)
  - Create tests/fixtures/sample.ods (OpenDocument spreadsheet with 2 sheets)
  - Create tests/fixtures/sample.odp (OpenDocument presentation with 2 slides)
  - Create tests/fixtures/sample.doc (Legacy Word document)
  - Create tests/fixtures/sample.ppt (Legacy PowerPoint)
  - Create tests/fixtures/sample.rtf (Rich Text Format document)
  - _Requirements: 2_

- [ ] 3.4 Test text handler functionality
  - Create tests/test_text_handler.py
  - Test extract_text_from_pdf() with sample.pdf
  - Test extract_text_from_docx() with sample.docx
  - Test extract_text_from_plain() with UTF-8 and latin-1 files
  - Test metadata extraction (page count, word count)
  - Test error handling with corrupted.pdf
  - Run tests to verify text extraction works
  - _Requirements: 2_

- [ ] 3.4.1 Test Office document extractors
  - Add tests for extract_text_from_xlsx() with sample.xlsx
  - Verify all sheets are extracted and properly formatted
  - Add tests for extract_text_from_pptx() with sample.pptx
  - Verify slide text and notes are extracted
  - Add tests for OpenDocument formats (ODT, ODS, ODP)
  - Add tests for legacy formats (DOC, PPT, RTF)
  - Test error handling for corrupted office files
  - Verify metadata includes sheet/slide counts
  - Run tests to verify all office format extractors work
  - _Requirements: 2_

- [ ] 4. Implement Audio Handler for ASR transcription
  - Create audio_handler.py module
  - Implement Google Cloud Speech-to-Text integration
  - Handle short and long audio files
  - Extract audio metadata
  - Test with mocked Speech-to-Text API
  - _Requirements: 3_

- [ ] 4.1 Create audio handler module
  - Create src/eduscale/transformer/handlers/audio_handler.py
  - Implement transcribe_audio() using google-cloud-speech
  - Support synchronous recognition for files < 60 seconds
  - Support long-running recognition for files > 60 seconds
  - Handle language selection (en-US, cs-CZ)
  - _Requirements: 3_

- [ ] 4.2 Implement audio format conversion
  - Use pydub to convert audio to LINEAR16 if needed
  - Implement get_audio_metadata() using mutagen
  - Extract duration, format, sample rate
  - Return metadata with confidence scores
  - _Requirements: 3_

- [x] 4.2.1 Implement YAML frontmatter builder for audio files
  - Create build_audio_frontmatter() function in audio_handler.py
  - Include file identifiers (file_id, region_id, event_id)
  - Include original file info (filename, content_type, size_bytes, bucket, object_path, uploaded_at)
  - Include extraction details (extracted_at, file_category, extraction_method, extraction_duration_ms)
  - Include audio metadata (duration_seconds, sample_rate, channels, audio_format)
  - Include transcription metrics (lines, confidence, language)
  - Format as YAML with --- delimiters
  - _Requirements: 9_

- [ ] 4.3 Create audio test fixtures
  - Create tests/fixtures/sample_short.mp3 (30-second audio file)
  - Create tests/fixtures/sample_long.mp3 (90-second audio file)
  - Create tests/fixtures/sample.wav (WAV format)
  - _Requirements: 3_

- [ ] 4.4 Test audio handler functionality
  - Create tests/test_audio_handler.py
  - Mock google-cloud-speech client
  - Test transcribe_audio() with short audio (synchronous)
  - Test transcribe_audio() with long audio (long-running)
  - Test get_audio_metadata() extracts duration and format
  - Test language selection (en-US, cs-CZ)
  - Test error handling for invalid audio files
  - Run tests to verify audio processing works
  - _Requirements: 3_

- [ ] 5. Implement Orchestrator for main processing flow
  - Create orchestrator.py module
  - Implement transform_file() main function
  - Implement routing logic to handlers
  - Test orchestration with mocked dependencies
  - _Requirements: 1, 2, 3, 5, 6_

- [ ] 5.1 Create orchestrator module
  - Create src/eduscale/transformer/orchestrator.py
  - Implement transform_file() function
  - Validate request parameters (file_id, bucket, object_name)
  - Check file size against MAX_FILE_SIZE_MB
  - _Requirements: 1, 2, 3, 5_

- [ ] 5.2 Implement handler routing logic
  - Implement route_to_handler() based on file_category
  - Route "text" → text_handler
  - Route "audio" → audio_handler
  - Route "other" → attempt text extraction
  - _Requirements: 2, 3_

- [x] 5.3 Implement frontmatter generation and streaming upload
  - Download file from GCS to temporary location
  - Call appropriate handler to extract text or transcribe audio
  - Build YAML frontmatter with comprehensive metadata
  - Create generator that yields frontmatter, separator, then extracted text
  - Stream upload to gs://{bucket}/text/{file_id}.txt using upload_text_streaming()
  - Clean up temporary files in finally block
  - _Requirements: 9, 10_

- [ ] 5.4 Test orchestrator functionality
  - Create tests/test_orchestrator.py
  - Mock storage and handlers
  - Test transform_file() with text file category
  - Test transform_file() with audio file category
  - Test file size validation
  - Test error handling and cleanup
  - Test frontmatter is correctly generated and included in upload
  - Run tests to verify orchestration works
  - _Requirements: 1, 2, 3, 9, 10_

- [ ] 6. Implement FastAPI endpoints
  - Create routes_transformer.py module
  - Define request/response models
  - Implement /api/v1/transformer/transform endpoint
  - Implement /health endpoint
  - Test API endpoints with FastAPI TestClient
  - _Requirements: 12_

- [x] 6.1 Create API endpoint module
  - Create src/eduscale/api/v1/routes_transformer.py
  - Define TransformRequest and TransformResponse Pydantic models
  - Define ExtractionMetadata model
  - Implement POST /api/v1/transformer/transform endpoint
  - Response includes text_uri and extraction_metadata (no tabular_result)
  - _Requirements: 1, 2, 3, 9, 10_

- [x] 6.2 Implement health check endpoint
  - Implement GET /health endpoint
  - Check connectivity to Cloud Storage
  - Return 200 if healthy, 503 if Cloud Storage unavailable
  - Respond within 10 seconds
  - _Requirements: 12_

- [ ] 6.3 Register routes in main application
  - Import routes_transformer in src/eduscale/main.py
  - Register transformer router with FastAPI app
  - _Requirements: 12_

- [x] 6.4 Test API endpoints
  - Create tests/transformer/test_api.py
  - Use FastAPI TestClient
  - Mock orchestrator.transform_file()
  - Test POST /api/v1/transformer/transform with valid request
  - Test request validation (invalid file_id, missing fields)
  - Test GET /health endpoint returns 200 when healthy
  - Test GET /health endpoint returns 503 when Cloud Storage unavailable
  - Test error responses (400, 500)
  - Run tests to verify API endpoints work
  - _Requirements: 12_

- [ ] 7. Implement error handling and logging
  - Define custom exception classes
  - Implement structured logging
  - Add error handling to all components
  - _Requirements: 11_

- [ ] 7.1 Define custom exceptions
  - Create TransformerException base class
  - Create FileTooLargeError exception
  - Create ExtractionError exception
  - Create StorageError exception
  - _Requirements: 11_

- [ ] 7.2 Implement structured logging
  - Use structlog for JSON logging
  - Include file_id, region_id, file_category in all logs
  - Include operation and duration_ms in logs
  - Include http_status in error logs
  - Log at appropriate levels (INFO, WARNING, ERROR)
  - _Requirements: 11_

- [ ] 7.2.1 Implement mandatory HTTP error logging
  - Create error logging middleware/decorator
  - Ensure ALL 4xx responses are logged at WARN level
  - Ensure ALL 5xx responses are logged at ERROR level with stack trace
  - Include error details: file_id, region_id, operation, duration_ms, http_status, error message
  - Verify no HTTP error can be returned without corresponding log entry
  - _Requirements: 11_

- [ ] 7.3 Add error handling to orchestrator
  - Wrap transform_file() in try/except
  - Return 500 for retryable errors (GCS, extraction)
  - Return 400 for permanent errors (invalid format, too large)
  - Log all errors with full context and stack trace
  - Ensure cleanup in finally block
  - _Requirements: 11_

- [ ] 7.4 Test error handling and logging
  - Create tests/test_error_handling.py
  - Test custom exceptions are raised correctly
  - Test structured logging includes all required fields
  - Test error responses (400 vs 500)
  - Test cleanup happens even on errors
  - Verify log output format is JSON
  - **Test ALL 4xx responses produce WARN level logs**
  - **Test ALL 5xx responses produce ERROR level logs with stack trace**
  - **Verify no HTTP error response can be returned without a log entry**
  - Test log includes http_status field for all errors
  - Run tests to verify error handling works
  - _Requirements: 11_

- [ ] 8. Create Docker configuration
  - Create Dockerfile for Transformer service
  - Install system dependencies (ffmpeg, libmagic1)
  - Configure container for Cloud Run deployment
  - _Requirements: 14_

- [x] 8.1 Create Dockerfile
  - Create docker/Dockerfile.transformer
  - Use python:3.11-slim base image
  - Install ffmpeg and libmagic1 for audio/document processing
  - Install pandoc for universal document conversion (DOCX, DOC, ODT, ODS, ODP)
  - Install poppler-utils for PDF processing utilities
  - Copy requirements.txt and install dependencies
  - Copy source code
  - Set CMD to run uvicorn
  - _Requirements: 14_

- [ ] 8.2 Test Docker build
  - Build Docker image locally
  - Verify all dependencies are installed
  - Test container starts successfully
  - Verify health endpoint is accessible
  - _Requirements: 14_

- [ ] 9. Create deployment configuration
  - Create Cloud Run service configuration
  - Document environment variables
  - Create deployment script
  - _Requirements: 14_

- [x] 9.1 Create Cloud Run configuration
  - Create infra/transformer-config.yaml
  - Configure memory: 2Gi, cpu: 2, timeout: 900s
  - Set max-instances: 20, min-instances: 0
  - Set concurrency: 10, ingress: internal
  - Environment variables: GCP_PROJECT_ID, GCP_REGION, GCS_BUCKET_NAME, MAX_FILE_SIZE_MB, SPEECH_LANGUAGE_EN, SPEECH_LANGUAGE_CS
  - _Requirements: 13, 14_

- [ ] 9.2 Document deployment steps
  - Add deployment instructions to README.md
  - Document required environment variables
  - Document service account permissions needed (storage.objects.get, storage.objects.create)
  - _Requirements: 13, 14_
