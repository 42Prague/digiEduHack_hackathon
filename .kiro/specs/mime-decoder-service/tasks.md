# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Create src/eduscale/services/mime_decoder/ directory (DONE)
  - Add dependencies to requirements.txt (httpx for async HTTP, pydantic for validation)
  - Create __init__.py files for package structure (DONE)
  - _Requirements: 9.1_

- [ ] 2. Extend configuration for MIME Decoder
  - Update src/eduscale/core/config.py with MIME Decoder settings
  - Add TRANSFORMER_SERVICE_URL, BACKEND_SERVICE_URL
  - Add REQUEST_TIMEOUT, BACKEND_UPDATE_TIMEOUT, LOG_LEVEL
  - Validate required environment variables at startup
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [x] 3. Implement MIME type classifier
  - Create src/eduscale/services/mime_decoder/classifier.py (DONE)
  - Define MIME_CATEGORIES mapping (DONE)
  - Implement classify_mime_type() function (DONE)
  - Handle text/*, audio/*, archive types (DONE)
  - Classify image/* as "image" category (DONE)
  - Return "other" for unrecognized types (DONE)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [ ] 4. Enhance metadata extraction in models.py
  - Update ProcessingRequest.from_cloud_event() method in models.py
  - Parse object path pattern: uploads/{region_id}/{file_id}.{ext}
  - Extract file_id and region_id from path using regex or split
  - Handle invalid path formats with warnings and default values
  - Add region_id field to ProcessingRequest model
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 5. Implement HTTP clients
  - Create src/eduscale/services/mime_decoder/clients.py
  - Implement call_transformer() async function with httpx.AsyncClient
  - Set timeout to REQUEST_TIMEOUT (300s) for Transformer calls
  - Build request payload with file metadata and category
  - Parse response and extract status from Transformer
  - Implement update_backend_status() async function
  - Use fire-and-forget pattern with asyncio.create_task() for Backend updates
  - Set short timeout (5s) for Backend calls
  - Log errors but don't fail the request if Backend update fails
  - Handle timeouts and HTTP errors appropriately
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 6. Enhance service orchestration
  - Update src/eduscale/services/mime_decoder/service.py
  - Import and use clients.py functions (call_transformer, update_backend_status)
  - After classification, call Transformer service with ProcessingRequest
  - Fire-and-forget Backend status update (don't await)
  - Measure processing time
  - Return detailed response with status and timing
  - Remove TODO comment about routing to Transformer
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1_

- [x] 7. Implement CloudEvents handler endpoint
  - CloudEvents handler already exists in main.py (DONE)
  - POST / endpoint receives CloudEvents from Eventarc (DONE)
  - Parses CloudEvents payload from request body (DONE)
  - Validates required fields via Pydantic models (DONE)
  - Returns 400 for validation errors, 500 for processing errors (DONE)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [x] 8. Implement error handling and logging
  - Structured logging already configured (DONE)
  - Correlation IDs from CloudEvents event ID in logs (DONE)
  - Logs at appropriate levels (INFO/WARNING/ERROR) (DONE)
  - Full context in error logs (file_id, error, stack trace) (DONE)
  - Distinguishes between 400 (no retry) and 500 (retry) errors (DONE)
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 9. Implement health check endpoint
  - GET /health endpoint exists in main.py (DONE)
  - Returns 200 with status "healthy" (DONE)
  - Simple health check without dependency checks (DONE)
  - _Requirements: 7.1, 7.2, 7.5_


- [ ]* 10. Write unit tests for classifier
  - Create tests/test_mime_classifier.py
  - Test classification for text/*, audio/*, archive types
  - Test PDF classified as "text"
  - Test Office documents classified as "text"
  - Test image/* classified as "image"
  - Test unknown types return "other"
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [ ]* 11. Write unit tests for metadata extraction
  - Create tests/test_mime_models.py
  - Test ProcessingRequest.from_cloud_event() with valid paths
  - Test parsing: uploads/region-cz-01/abc123.pdf
  - Test extracting file_id and region_id correctly
  - Test handling invalid path formats with defaults
  - Test with various file extensions
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ]* 12. Write unit tests for service orchestration
  - Create tests/test_mime_service.py
  - Mock Transformer and Backend clients
  - Test successful processing flow
  - Test error handling when Transformer fails
  - Test that Backend failures don't fail the request
  - Verify processing time is measured
  - _Requirements: 4.1, 4.2, 4.3, 5.4, 5.5_

- [ ]* 13. Write integration tests for CloudEvents
  - Create tests/test_mime_integration.py
  - Create fixture CloudEvents payloads
  - Test parsing valid CloudEvents
  - Test validation errors for missing fields
  - Test end-to-end flow with mocked Transformer
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [x] 14. Create Cloud Run deployment configuration
  - infra/mime-decoder-config.yaml already exists (DONE)
  - Memory: 512MB, CPU: 1 vCPU configured (DONE)
  - Autoscaling: min 0, max 10 configured (DONE)
  - Timeout: 300 seconds configured (DONE)
  - Need to add TRANSFORMER_SERVICE_URL and BACKEND_SERVICE_URL env vars
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] 15. Create Dockerfile for MIME Decoder
  - docker/Dockerfile.mime-decoder already exists (DONE)
  - Python 3.11 slim base image (DONE)
  - Multi-stage build for optimization (DONE)
  - Runs uvicorn with mime_decoder main.py (DONE)
  - _Requirements: 9.1_

- [x] 16. MIME Decoder is standalone service
  - MIME Decoder runs as separate Cloud Run service (DONE)
  - Has its own FastAPI app in main.py (DONE)
  - Not integrated into main eduscale app (DONE)
  - _Requirements: 1.1, 7.1_

- [ ] 17. Add missing environment variables to deployment config
  - Update infra/mime-decoder-config.yaml
  - Add TRANSFORMER_SERVICE_URL environment variable
  - Add BACKEND_SERVICE_URL environment variable
  - Add REQUEST_TIMEOUT with default 300
  - Add BACKEND_UPDATE_TIMEOUT with default 5
  - _Requirements: 8.1, 8.2, 8.5_
