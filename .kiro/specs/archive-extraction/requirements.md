# Requirements Document: Archive Extraction in MIME Decoder

## Introduction

This feature adds archive extraction capabilities to the MIME Decoder service. When an archive file (ZIP, TAR, GZIP, etc.) is uploaded, the service will extract its contents, classify each file, and process them individually through the appropriate transformers.

## Glossary

- **MIME Decoder**: The service that classifies uploaded files by MIME type
- **Archive**: A compressed file containing one or more files (ZIP, TAR, GZIP, etc.)
- **Extraction**: The process of unpacking files from an archive
- **Cloud Storage**: Google Cloud Storage bucket where files are stored
- **Transformer Service**: Downstream service that processes files based on their category

## Requirements

### Requirement 1: Detect Archive Files

**User Story:** As a system, I want to detect when an uploaded file is an archive, so that I can extract and process its contents

#### Acceptance Criteria

1. WHEN a CloudEvent is received with content type "application/zip", THE MIME Decoder SHALL classify the file as category "archive"
2. WHEN a CloudEvent is received with content type "application/x-tar", THE MIME Decoder SHALL classify the file as category "archive"
3. WHEN a CloudEvent is received with content type "application/gzip", THE MIME Decoder SHALL classify the file as category "archive"
4. WHEN a CloudEvent is received with content type "application/x-7z-compressed", THE MIME Decoder SHALL classify the file as category "archive"
5. WHEN a CloudEvent is received with content type "application/x-rar-compressed", THE MIME Decoder SHALL classify the file as category "archive"

### Requirement 2: Download Archive from Cloud Storage

**User Story:** As a MIME Decoder service, I want to download archive files from Cloud Storage, so that I can extract their contents

#### Acceptance Criteria

1. WHEN an archive file is detected, THE MIME Decoder SHALL download the file from Cloud Storage using the bucket and object_name from the CloudEvent
2. WHEN downloading fails due to network error, THE MIME Decoder SHALL retry up to 3 times with exponential backoff
3. WHEN downloading fails after all retries, THE MIME Decoder SHALL log an error and return HTTP 500
4. WHEN the file size exceeds 500MB, THE MIME Decoder SHALL log a warning and skip extraction
5. THE MIME Decoder SHALL download files to a temporary directory that is cleaned up after processing

### Requirement 3: Extract Archive Contents

**User Story:** As a MIME Decoder service, I want to extract files from archives, so that I can process each file individually

#### Acceptance Criteria

1. WHEN a ZIP archive is downloaded, THE MIME Decoder SHALL extract all files using Python zipfile module
2. WHEN a TAR archive is downloaded, THE MIME Decoder SHALL extract all files using Python tarfile module
3. WHEN a GZIP archive is downloaded, THE MIME Decoder SHALL extract the compressed file using Python gzip module
4. WHEN extraction encounters a password-protected archive, THE MIME Decoder SHALL log a warning and skip the archive
5. WHEN extraction encounters a corrupted archive, THE MIME Decoder SHALL log an error and skip the archive
6. THE MIME Decoder SHALL limit extraction to maximum 100 files per archive
7. THE MIME Decoder SHALL skip files larger than 50MB during extraction

### Requirement 4: Upload Extracted Files to Cloud Storage

**User Story:** As a MIME Decoder service, I want to upload extracted files back to Cloud Storage, so that they can be processed individually

#### Acceptance Criteria

1. WHEN files are extracted from an archive, THE MIME Decoder SHALL upload each file to Cloud Storage in the path pattern "uploads/{region_id}/{original_archive_id}/{extracted_filename}"
2. WHEN uploading an extracted file, THE MIME Decoder SHALL detect the MIME type using Python mimetypes module
3. WHEN uploading an extracted file, THE MIME Decoder SHALL preserve the original filename
4. WHEN uploading fails, THE MIME Decoder SHALL log an error and continue with the next file
5. THE MIME Decoder SHALL upload files with appropriate content-type metadata

### Requirement 5: Process Extracted Files

**User Story:** As a MIME Decoder service, I want to classify and process extracted files, so that each file is handled according to its type

#### Acceptance Criteria

1. WHEN an extracted file is uploaded to Cloud Storage, THE MIME Decoder SHALL classify the file using the existing classifier
2. WHEN an extracted file is classified, THE MIME Decoder SHALL call the Transformer service with the file metadata
3. WHEN an extracted file is an archive, THE MIME Decoder SHALL NOT recursively extract it
4. WHEN processing extracted files, THE MIME Decoder SHALL update the Backend service with status for each file
5. THE MIME Decoder SHALL process extracted files asynchronously without blocking the original request

### Requirement 6: Error Handling and Logging

**User Story:** As a developer, I want comprehensive error handling and logging for archive extraction, so that I can troubleshoot issues

#### Acceptance Criteria

1. WHEN archive extraction starts, THE MIME Decoder SHALL log the archive filename, size, and number of files
2. WHEN extraction completes, THE MIME Decoder SHALL log the number of successfully extracted files
3. WHEN extraction fails, THE MIME Decoder SHALL log the error with full context including archive path and error message
4. WHEN an individual file extraction fails, THE MIME Decoder SHALL log the error and continue with remaining files
5. THE MIME Decoder SHALL include the original event_id in all logs for correlation

### Requirement 7: Configuration

**User Story:** As an operator, I want to configure archive extraction behavior, so that I can control resource usage

#### Acceptance Criteria

1. THE MIME Decoder SHALL read an ENABLE_ARCHIVE_EXTRACTION environment variable (default: true)
2. THE MIME Decoder SHALL read a MAX_ARCHIVE_SIZE_MB environment variable (default: 500)
3. THE MIME Decoder SHALL read a MAX_FILES_PER_ARCHIVE environment variable (default: 100)
4. THE MIME Decoder SHALL read a MAX_EXTRACTED_FILE_SIZE_MB environment variable (default: 50)
5. WHERE ENABLE_ARCHIVE_EXTRACTION is false, THE MIME Decoder SHALL skip archive extraction and process archives as regular files
