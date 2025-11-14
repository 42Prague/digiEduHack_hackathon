# Implementation Plan

- [x] 1. Update path validation to reject invalid paths
  - [x] 1.1 Modify ProcessingRequest.from_cloud_event() in models.py
    - Replace fallback logic (lines 95-103) that sets `region_id = "unknown"` with ValueError raise
    - Add structured error logging with event_id, object_path, and expected_pattern fields
    - Include clear error message in ValueError: "Invalid object path: {path}. Expected pattern: uploads/{region_id}/{file_id}_{filename}"
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Add retry logic to Transformer calls
  - [x] 2.1 Implement retry mechanism in call_transformer() function
    - Add constants: MAX_ATTEMPTS = 3, RETRY_DELAY_SECONDS = 2
    - Wrap HTTP call in for loop with attempt counter (1 to MAX_ATTEMPTS)
    - Add asyncio.sleep(RETRY_DELAY_SECONDS) between attempts
    - Track last_error and raise it after final attempt fails
    - _Requirements: 2.1, 2.2, 2.3, 2.6_
  
  - [x] 2.2 Add structured logging for retry attempts
    - Log each attempt with: file_id, attempt number, max_attempts
    - Log warnings for failed attempts with: status_code, error_type
    - Log error after all attempts exhausted with: total_attempts, final_error, final_status_code
    - Log success with: attempt number that succeeded
    - _Requirements: 2.6, 3.1, 3.4_

- [x] 3. Enhance logging for observability
  - [x] 3.1 Add outcome field to success logs in service.py
    - Update "Event processed successfully" log to include outcome="success"
    - Add transformer_attempts field to track retry count
    - _Requirements: 3.2_
  
  - [x] 3.2 Add outcome field to error logs in service.py
    - Update "Failed to process CloudEvent" log to include outcome="failed"
    - Ensure error_type is included in all error logs
    - _Requirements: 3.2_
  
  - [x] 3.3 Add structured fields to path validation error logs
    - Ensure event_id, object_path, expected_pattern are logged
    - Add outcome="invalid_path" to error log
    - _Requirements: 3.3_

- [x] 4. Deploy and verify changes
  - [x] 4.1 Deploy code changes to MIME Decoder service
    - Commit and push code changes to mime_decoder service
    - Trigger GitHub Actions deployment workflow
    - Monitor deployment logs for successful completion
    - Verify service health endpoint returns 200
  
  - [x] 4.2 Verify fix in production
    - Upload test file to uploads/ folder and verify processing succeeds
    - Check Cloud Logging for proper outcome tracking (outcome="success")
    - Verify no retry loops occur (check for repeated event_id in logs)
    - Monitor for HTTP 400 responses (should be zero if all paths are valid)
    - Monitor for HTTP 429 responses from Transformer (should be handled with retries)
