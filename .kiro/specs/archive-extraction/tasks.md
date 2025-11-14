# Implementation Plan: Archive Extraction

- [x] 1. Add dependencies and configuration
  - Add google-cloud-storage to requirements.txt
  - Add archive extraction config to Settings in config.py
  - Add ENABLE_ARCHIVE_EXTRACTION, MAX_ARCHIVE_SIZE_MB, MAX_FILES_PER_ARCHIVE, MAX_EXTRACTED_FILE_SIZE_MB, UPLOADS_BUCKET
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 2. Create GCS client module
  - Create src/eduscale/services/mime_decoder/gcs_client.py
  - Implement GCSClient class with __init__, download_file, upload_file, get_file_size methods
  - Add retry logic with exponential backoff (3 retries)
  - Use google.cloud.storage library
  - Handle authentication via default credentials
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 3. Create archive extractor module
  - Create src/eduscale/services/mime_decoder/archive_extractor.py
  - Define ExtractedFile dataclass
  - Implement ArchiveExtractor class with extract_archive method
  - Support ZIP format using zipfile module
  - Support TAR format using tarfile module
  - Support GZIP format using gzip module
  - Implement file count limit (MAX_FILES_PER_ARCHIVE)
  - Implement file size limit (MAX_EXTRACTED_FILE_SIZE_MB)
  - Add path traversal protection
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 4. Implement archive processing in service
  - Create process_archive function in service.py
  - Download archive from GCS using GCSClient
  - Extract files using ArchiveExtractor
  - Upload extracted files to GCS with pattern uploads/{region_id}/{archive_id}/{filename}
  - Detect MIME type for each extracted file
  - Classify each extracted file
  - Call Transformer for each file
  - Update Backend status for each file
  - Cleanup temporary files after processing
  - _Requirements: 2.1, 3.1, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 5. Integrate archive processing into main flow
  - Update process_cloud_event in service.py
  - Check if file category is ARCHIVE and ENABLE_ARCHIVE_EXTRACTION is true
  - Call process_archive instead of call_transformer for archives
  - Add comprehensive logging for archive processing
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 6. Update deployment configuration
  - Add archive extraction environment variables to infra/mime-decoder-config.yaml
  - Add ENABLE_ARCHIVE_EXTRACTION, MAX_ARCHIVE_SIZE_MB, MAX_FILES_PER_ARCHIVE, MAX_EXTRACTED_FILE_SIZE_MB
  - Add UPLOADS_BUCKET environment variable
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x]* 7. Write unit tests for GCS client
  - Create tests/test_gcs_client.py
  - Test download_file with mocked GCS
  - Test upload_file with mocked GCS
  - Test retry logic
  - Test error handling
  - _Requirements: 2.1, 2.2, 2.3_

- [x]* 8. Write unit tests for archive extractor
  - Create tests/test_archive_extractor.py
  - Test ZIP extraction
  - Test TAR extraction
  - Test GZIP extraction
  - Test file count limit enforcement
  - Test file size limit enforcement
  - Test path traversal protection
  - _Requirements: 3.1, 3.2, 3.3, 3.6, 3.7_

- [ ]* 9. Write integration tests for archive processing
  - Create tests/test_archive_processing.py
  - Test end-to-end archive processing with test bucket
  - Test with various archive types
  - Test error scenarios (corrupted archive, password protected)
  - _Requirements: 3.4, 3.5, 6.3, 6.4_m
ents.txt
  - Add archive extraction config to Settings in config.py
  - Add ENABLE_ARCHIVE_EXTRACTION, MAX