# Implementation Plan

- [x] 1. Extend configuration system
  - Add STORAGE_BACKEND, GCS_BUCKET_NAME, MAX_UPLOAD_MB, and ALLOWED_UPLOAD_MIME_TYPES settings to Settings class
  - Implement allowed_mime_types and max_upload_bytes properties for parsing
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Create data models and upload store
  - [x] 2.1 Create UploadResponse Pydantic model in src/eduscale/models/upload.py
    - Define fields: file_id, file_name, storage_backend, storage_path, region_id, content_type, size_bytes, created_at
    - _Requirements: 2.8_
  
  - [x] 2.2 Create UploadRecord dataclass and UploadStore in src/eduscale/storage/upload_store.py
    - Implement UploadRecord with all metadata fields
    - Implement UploadStore with create(), get(), and list_all() methods
    - Create singleton upload_store instance
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 3. Implement storage backend system
  - [x] 3.1 Create abstract StorageBackend interface in src/eduscale/storage/base.py
    - Define get_target_path() abstract method
    - Define store_file() abstract method
    - Define get_backend_name() abstract method
    - _Requirements: 3.1, 3.2, 3.4_
  
  - [x] 3.2 Implement LocalStorageBackend in src/eduscale/storage/local.py
    - Implement get_target_path() to generate local file paths
    - Implement store_file() with chunked streaming to filesystem
    - Implement _sanitize_filename() static method
    - Create directory structure if needed
    - Create singleton local_backend instance
    - _Requirements: 3.2, 3.3, 3.4, 6.1, 6.2_
  
  - [x] 3.3 Implement GCSStorageBackend in src/eduscale/storage/gcs.py
    - Implement lazy-loaded _get_bucket() method
    - Implement get_target_path() to generate GCS blob paths
    - Implement store_file() with streaming upload to GCS
    - Implement _sanitize_filename() static method
    - Create singleton gcs_backend instance
    - _Requirements: 3.1, 3.4, 3.6, 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 3.4 Create storage factory in src/eduscale/storage/factory.py
    - Implement get_storage_backend() function that returns appropriate backend based on settings
    - Handle invalid backend configuration
    - _Requirements: 3.1, 3.2_

- [x] 4. Implement upload API endpoint
  - [x] 4.1 Create upload router in src/eduscale/api/v1/routes_upload.py
    - Create FastAPI router with /api/v1 prefix and "upload" tag
    - Import required dependencies
    - _Requirements: 2.1_
  
  - [x] 4.2 Implement POST /upload endpoint
    - Accept file (UploadFile) and region_id (Form) parameters
    - Validate region_id is not empty
    - Validate file size against MAX_UPLOAD_MB
    - Validate content type against ALLOWED_UPLOAD_MIME_TYPES if configured
    - Generate UUID4 file_id
    - Get storage backend from factory
    - Stream file to storage backend
    - Create UploadRecord in upload_store
    - Return UploadResponse with HTTP 201
    - Log upload completion at info level
    - Handle errors with appropriate HTTP status codes and logging
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 3.1, 3.2, 3.4, 3.5, 4.3, 6.3, 6.4, 6.5, 6.6_
  
  - [x] 4.3 Register upload router in src/eduscale/main.py
    - Import routes_upload router
    - Include router in FastAPI app
    - _Requirements: 2.1_

- [x] 5. Create upload UI
  - [x] 5.1 Set up Jinja2 templates
    - Create src/eduscale/ui/templates directory
    - Configure Jinja2Templates in main.py or separate UI router
    - _Requirements: 5.1_
  
  - [x] 5.2 Create upload.html template in src/eduscale/ui/templates/
    - Add HTML form with region_id select input (predefined options: eu-west, us-east, asia-pacific)
    - Add file input element
    - Add submit button
    - Add status display area
    - Implement JavaScript to handle form submission
    - Create FormData with file and region_id
    - POST to /api/v1/upload with fetch
    - Display upload progress, success message with file_id, or error messages
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_
  
  - [x] 5.3 Create GET /upload route
    - Create router for UI routes (can be in routes_upload.py or separate file)
    - Implement GET /upload endpoint that renders upload.html template
    - Register UI router in main.py
    - _Requirements: 5.1_

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

- [ ] 8. Write tests
  - [x] 8.1 Create tests/test_upload.py
    - Test POST /api/v1/upload with valid file and region_id in local mode
    - Test validation errors (empty region_id, oversized file, invalid MIME type)
    - Test response structure
    - Mock storage backends
    - Verify upload record creation
  
  - [x] 8.2 Create tests/test_storage_backends.py
    - Test filename sanitization for both backends
    - Test path generation
    - Mock GCS client for GCS backend tests
    - Test local file writing with temporary directory
  
  - [x] 8.3 Create tests/test_upload_store.py
    - Test UploadRecord creation and retrieval
    - Test list_all() method
    - Test missing record handling
