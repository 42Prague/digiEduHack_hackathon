# Design Document: Archive Extraction in MIME Decoder

## Overview

This design adds archive extraction capabilities to the MIME Decoder service. When an archive file (ZIP, TAR, GZIP) is detected, the service will:
1. Download the archive from Cloud Storage
2. Extract all files from the archive
3. Upload extracted files back to Cloud Storage
4. Process each extracted file through the normal classification pipeline

This enables users to upload archives containing multiple files and have each file processed individually.

## Architecture

### High-Level Flow

```
CloudEvent (archive) → MIME Decoder
  ↓
Classify as "archive"
  ↓
Download from GCS
  ↓
Extract files to temp directory
  ↓
For each extracted file:
  - Detect MIME type
  - Upload to GCS (new path)
  - Classify file
  - Call Transformer
  - Update Backend
  ↓
Cleanup temp files
  ↓
Return success response
```

### Components

1. **archive_extractor.py** - Core extraction logic
2. **gcs_client.py** - Google Cloud Storage operations
3. **service.py** - Updated to handle archive files
4. **config.py** - Archive extraction configuration

## Component Design

### 1. GCS Client (gcs_client.py)

**Purpose**: Handle Google Cloud Storage operations for downloading and uploading files

**Interface**:
```python
class GCSClient:
    def __init__(self, bucket_name: str):
        """Initialize GCS client with bucket name."""
        
    async def download_file(self, object_name: str, destination_path: str) -> None:
        """Download file from GCS to local path."""
        
    async def upload_file(
        self, 
        source_path: str, 
        destination_name: str,
        content_type: str
    ) -> None:
        """Upload file from local path to GCS."""
        
    def get_file_size(self, object_name: str) -> int:
        """Get file size in bytes without downloading."""
```

**Implementation Notes**:
- Use `google-cloud-storage` library
- Implement retry logic with exponential backoff (3 retries)
- Use async/await for non-blocking operations
- Handle authentication via default credentials

### 2. Archive Extractor (archive_extractor.py)

**Purpose**: Extract files from various archive formats

**Interface**:
```python
@dataclass
class ExtractedFile:
    """Metadata for an extracted file."""
    filename: str
    size_bytes: int
    mime_type: str
    local_path: str

class ArchiveExtractor:
    def __init__(
        self,
        max_files: int = 100,
        max_file_size_mb: int = 50
    ):
        """Initialize extractor with limits."""
        
    async def extract_archive(
        self,
        archive_path: str,
        archive_type: str,
        extract_dir: str
    ) -> List[ExtractedFile]:
        """
        Extract archive and return list of extracted files.
        
        Args:
            archive_path: Path to archive file
            archive_type: Type of archive (zip, tar, gzip)
            extract_dir: Directory to extract files to
            
        Returns:
            List of ExtractedFile objects
            
        Raises:
            ArchiveExtractionError: If extraction fails
        """
```

**Supported Formats**:
- **ZIP**: Use `zipfile` module
- **TAR**: Use `tarfile` module (supports .tar, .tar.gz, .tar.bz2)
- **GZIP**: Use `gzip` module (single file compression)

**Safety Measures**:
- Check for path traversal attacks (../ in filenames)
- Limit number of files extracted
- Limit individual file sizes
- Skip password-protected archives
- Validate archive integrity before extraction

### 3. Archive Processing Service (service.py updates)

**New Function**:
```python
async def process_archive(
    cloud_event: CloudEvent,
    processing_req: ProcessingRequest,
    gcs_client: GCSClient,
    extractor: ArchiveExtractor
) -> Dict[str, Any]:
    """
    Process an archive file by extracting and processing contents.
    
    Flow:
    1. Download archive from GCS
    2. Extract files
    3. Upload extracted files to GCS
    4. Process each file through classifier
    5. Cleanup temporary files
    
    Returns:
        Response with extraction statistics
    """
```

**Integration with Existing Flow**:
```python
async def process_cloud_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    # ... existing code ...
    
    # After classification
    if file_category == FileCategory.ARCHIVE and settings.ENABLE_ARCHIVE_EXTRACTION:
        return await process_archive(cloud_event, processing_req, gcs_client, extractor)
    else:
        # Existing transformer call
        transformer_response = await call_transformer(...)
```

## Data Models

### Configuration (config.py)

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Archive Extraction Configuration
    ENABLE_ARCHIVE_EXTRACTION: bool = True
    MAX_ARCHIVE_SIZE_MB: int = 500
    MAX_FILES_PER_ARCHIVE: int = 100
    MAX_EXTRACTED_FILE_SIZE_MB: int = 50
    UPLOADS_BUCKET: str = ""  # GCS bucket name
```

### Extracted File Path Pattern

```
Original archive: uploads/{region_id}/{archive_id}.zip
Extracted files:  uploads/{region_id}/{archive_id}/{filename}

Example:
  Archive:   uploads/region-cz-01/abc123.zip
  File 1:    uploads/region-cz-01/abc123/document.pdf
  File 2:    uploads/region-cz-01/abc123/data.csv
```

## Error Handling

### Error Types

1. **Download Errors**
   - Network failures → Retry with backoff
   - File not found → Log error, return 404
   - Permission denied → Log error, return 403

2. **Extraction Errors**
   - Corrupted archive → Log error, skip archive
   - Password protected → Log warning, skip archive
   - Path traversal attempt → Log security warning, skip file

3. **Upload Errors**
   - Network failures → Retry with backoff
   - Permission denied → Log error, continue with next file
   - Quota exceeded → Log error, stop processing

### Logging Strategy

```python
# Start extraction
logger.info(
    "Starting archive extraction",
    extra={
        "event_id": event_id,
        "archive_name": object_name,
        "archive_size_mb": size_mb,
        "archive_type": archive_type
    }
)

# Extraction complete
logger.info(
    "Archive extraction completed",
    extra={
        "event_id": event_id,
        "files_extracted": len(extracted_files),
        "files_uploaded": upload_count,
        "processing_time_ms": processing_time
    }
)

# Individual file processing
logger.info(
    "Processing extracted file",
    extra={
        "event_id": event_id,
        "filename": filename,
        "mime_type": mime_type,
        "category": category
    }
)
```

## Testing Strategy

### Unit Tests

1. **test_archive_extractor.py**
   - Test ZIP extraction
   - Test TAR extraction
   - Test GZIP extraction
   - Test file limit enforcement
   - Test size limit enforcement
   - Test path traversal protection

2. **test_gcs_client.py**
   - Test file download
   - Test file upload
   - Test retry logic
   - Test error handling

### Integration Tests

1. **test_archive_processing.py**
   - Test end-to-end archive processing
   - Test with real GCS (using test bucket)
   - Test with various archive types
   - Test error scenarios

## Security Considerations

1. **Path Traversal Prevention**
   - Validate all extracted filenames
   - Reject files with ../ or absolute paths
   - Use `os.path.normpath()` and verify paths stay within extract directory

2. **Resource Limits**
   - Enforce maximum archive size
   - Enforce maximum number of files
   - Enforce maximum individual file size
   - Set extraction timeout

3. **Malicious Archives**
   - Zip bombs: Check compression ratio
   - Symlink attacks: Skip symlinks during extraction
   - Infinite recursion: Don't extract nested archives

## Performance Considerations

1. **Async Processing**
   - Use async/await for I/O operations
   - Process files concurrently where possible
   - Don't block main request thread

2. **Temporary Storage**
   - Use `/tmp` directory (Cloud Run provides 512MB)
   - Clean up immediately after processing
   - Monitor disk usage

3. **Memory Usage**
   - Stream large files instead of loading into memory
   - Process files one at a time
   - Limit concurrent operations

## Deployment

### Dependencies

Add to `requirements.txt`:
```
google-cloud-storage>=2.10.0
```

### Environment Variables

Update `infra/mime-decoder-config.yaml`:
```yaml
- name: ENABLE_ARCHIVE_EXTRACTION
  value: 'true'
- name: MAX_ARCHIVE_SIZE_MB
  value: '500'
- name: MAX_FILES_PER_ARCHIVE
  value: '100'
- name: MAX_EXTRACTED_FILE_SIZE_MB
  value: '50'
- name: UPLOADS_BUCKET
  value: BUCKET_NAME_PLACEHOLDER
```

### IAM Permissions

MIME Decoder service account needs:
- `storage.objects.get` - Download archives
- `storage.objects.create` - Upload extracted files
- `storage.objects.list` - List bucket contents (optional)

## Monitoring

### Metrics to Track

1. Archives processed per hour
2. Average extraction time
3. Average files per archive
4. Extraction failure rate
5. Storage usage for temp files

### Alerts

1. High extraction failure rate (>10%)
2. Extraction timeout (>5 minutes)
3. Disk space usage (>80% of /tmp)
4. Large archives (>400MB)

## Future Enhancements

1. Support for RAR and 7z formats
2. Recursive archive extraction (archives within archives)
3. Parallel file processing
4. Streaming extraction for very large archives
5. Archive content preview before extraction
