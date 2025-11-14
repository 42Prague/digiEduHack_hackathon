# Implementation Plan

- [ ] 1. Extend configuration system for dual-path upload
  - Add DIRECT_UPLOAD_SIZE_THRESHOLD_MB setting to Settings class (default: 31)
  - Implement direct_upload_threshold_bytes property
  - Update existing STORAGE_BACKEND, GCS_BUCKET_NAME, MAX_UPLOAD_MB, ALLOWED_UPLOAD_MIME_TYPES settings
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 9.1_

- [ ] 2. Update data models and upload store for signed URL support
  - [ ] 2.1 Add new Pydantic models in src/eduscale/models/upload.py
    - Create CreateSessionRequest model with region_id, file_name, file_size_bytes, content_type
    - Create CreateSessionResponse model with file_id, upload_method, signed_url, target_path, expires_at
    - Create CompleteUploadRequest model with file_id
    - Update existing UploadResponse model
    - _Requirements: 8.2, 8.11, 10.2_
  
  - [ ] 2.2 Update UploadRecord and UploadStore in src/eduscale/storage/upload_store.py
    - Add UploadStatus enum with PENDING and COMPLETED values
    - Add status field to UploadRecord dataclass
    - Add completed_at optional field to UploadRecord
    - Implement update_status() method in UploadStore
    - Update existing create(), get(), and list_all() methods
    - _Requirements: 4.1, 4.2, 4.3, 10.5_

- [ ] 3. Extend storage backend system with signed URL support
  - [ ] 3.1 Update GCSStorageBackend in src/eduscale/storage/gcs.py
    - Add generate_signed_upload_url() method for V4 signed URL generation
    - Include 15-minute expiration, content-type constraint, and size constraint
    - Add check_file_exists() method to verify file presence in GCS
    - Keep existing get_target_path(), store_file(), and _sanitize_filename() methods
    - _Requirements: 8.7, 8.8, 8.9, 8.10, 10.7, 7.1, 7.2, 7.3_
  
  - [ ] 3.2 Keep LocalStorageBackend unchanged in src/eduscale/storage/local.py
    - No changes needed for local backend (signed URLs only for GCS)
    - _Requirements: 9.2_

- [ ] 4. Implement upload API endpoints with dual-path routing
  - [ ] 4.1 Update POST /upload endpoint in src/eduscale/api/v1/routes_upload.py
    - Keep existing direct upload logic for small files
    - Set upload record status to COMPLETED for direct uploads
    - Validate file size against MAX_UPLOAD_MB
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 9.2, 9.3_
  
  - [ ] 4.2 Implement POST /upload/sessions endpoint
    - Accept CreateSessionRequest with region_id, file_name, file_size_bytes, content_type
    - Validate region_id, file_size_bytes, and content_type
    - Generate UUID4 file_id
    - Check if file size exceeds direct_upload_threshold_bytes (31 MB)
    - If file ≤31 MB, return upload_method="direct" without signed URL
    - If file >31 MB and GCS backend, generate signed URL with 15-minute expiration
    - If file >31 MB and local backend, return HTTP 400 error
    - Create pending upload record in upload_store with status=PENDING
    - Return CreateSessionResponse with file_id, upload_method, signed_url, target_path, expires_at
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11, 8.12, 9.1, 9.4_
  
  - [ ] 4.3 Implement POST /upload/complete endpoint
    - Accept CompleteUploadRequest with file_id
    - Validate file_id is not empty
    - Retrieve upload record from upload_store
    - Return HTTP 404 if record not found
    - Verify file exists in GCS using check_file_exists()
    - Return HTTP 400 if file doesn't exist
    - Update upload record status to COMPLETED with completed_at timestamp
    - Return UploadResponse with upload metadata
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

- [ ] 5. Update upload UI with automatic routing logic
  - [ ] 5.1 Update upload.html template in src/eduscale/ui/templates/
    - Add file size display with upload method indicator
    - Implement JavaScript constant DIRECT_UPLOAD_THRESHOLD (31 MB)
    - Add directUpload() function for small files (existing logic)
    - Add signedUrlUpload() function for large files with three steps:
      - Step 1: POST to /api/v1/upload/sessions to create session
      - Step 2: PUT file directly to signed_url from response
      - Step 3: POST to /api/v1/upload/complete to finalize
    - Implement automatic routing in form submit handler based on file.size
    - Display appropriate status messages for each step
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 9.1, 9.3, 9.4, 9.5, 9.6_

- [x] 6. Provision GCS infrastructure
  - [x] 6.1 Add GCS bucket to Terraform configuration
    - Enable Cloud Storage API in infra/terraform/main.tf
    - Create google_storage_bucket resource with lifecycle rules
    - Add IAM binding for Cloud Run service account
    - Add bucket name output
    - _Requirements: 7.6, 7.7_
  
  - [x] 6.2 Add GCS environment variables to Cloud Run
    - Update Cloud Run service in infra/terraform/main.tf to include STORAGE_BACKEND, GCS_BUCKET_NAME, MAX_UPLOAD_MB, and ALLOWED_UPLOAD_MIME_TYPES
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 7. Add Python dependencies
  - Add google-cloud-storage>=2.10.0 to requirements.txt
  - Add jinja2>=3.1.0 to requirements.txt
  - Add python-multipart>=0.0.6 to requirements.txt
  - _Requirements: 7.1_

- [ ]* 8. Write tests for signed URL functionality
  - [ ]* 8.1 Update tests/test_upload.py
    - Test POST /api/v1/upload/sessions with valid metadata
    - Test POST /api/v1/upload/sessions returns direct method for small files
    - Test POST /api/v1/upload/sessions returns signed_url method for large files
    - Test POST /api/v1/upload/sessions returns error for large files with local backend
    - Test POST /api/v1/upload/complete with valid file_id
    - Test POST /api/v1/upload/complete returns 404 for missing file_id
    - Test POST /api/v1/upload/complete returns 400 when file doesn't exist in GCS
    - Mock GCS signed URL generation and file existence checks
    - Verify upload record status transitions (PENDING → COMPLETED)
  
  - [ ]* 8.2 Update tests/test_storage_backends.py
    - Test generate_signed_upload_url() method in GCS backend
    - Test check_file_exists() method in GCS backend
    - Verify signed URL includes correct expiration and constraints
    - Mock GCS blob.generate_signed_url() and blob.exists()
  
  - [ ]* 8.3 Update tests/test_upload_store.py
    - Test UploadRecord creation with status field
    - Test update_status() method
    - Test status transitions from PENDING to COMPLETED
    - Test completed_at timestamp setting
