# Design Document

## Overview

This design addresses the retry storm issue in the MIME Decoder service by fixing the root cause (Eventarc trigger misconfiguration) and adding defensive measures (path validation, retry logic, improved logging).

The solution focuses on simplicity and minimal code changes to quickly resolve the production issue.

## Architecture

### Current Flow (Problematic)

```
User uploads file → GCS (uploads/region-01/abc123_file.pdf)
  ↓
Eventarc storage_trigger (listens to ALL files in bucket)
  ↓
MIME Decoder → validates path → calls Transformer
  ↓
Transformer processes → uploads result to GCS (text/abc123.txt)
  ↓
Eventarc storage_trigger (triggers again! ❌)
  ↓
MIME Decoder → path validation fails → continues anyway → calls Transformer
  ↓
Transformer returns 429 (rate limited)
  ↓
MIME Decoder returns 500
  ↓
Eventarc retries → LOOP! 🔄
```

### Fixed Flow

```
User uploads file → GCS (uploads/region-01/abc123_file.pdf)
  ↓
Eventarc storage_trigger (listens ONLY to uploads/* ✅)
  ↓
MIME Decoder → validates path → calls Transformer (with retry)
  ↓
Transformer processes → uploads result to GCS (text/abc123.txt)
  ↓
Eventarc text_trigger (separate trigger for text/* ✅)
  ↓
Tabular Service (not MIME Decoder!)
```

## Components and Interfaces

### 1. Path Validation (MIME Decoder)

**File**: `src/eduscale/services/mime_decoder/models.py`

**Changes**:
- Modify `ProcessingRequest.from_cloud_event()` method
- Raise `ValueError` instead of logging warning when path doesn't match
- Remove fallback logic that continues processing with `region_id = "unknown"`

**Path Consistency Verification**:
All file uploads use the pattern `uploads/{region_id}/{file_id}_{filename}`:
- ✅ GCS Backend (`src/eduscale/storage/gcs.py`): All methods use correct pattern
- ✅ Archive Extraction (`src/eduscale/services/mime_decoder/service.py`): Uses correct pattern
- ✅ Transformer output (`text/{file_id}.txt`): Different pattern, but will be filtered by Eventarc

After Eventarc filter is applied, MIME Decoder will only receive files from `uploads/` folder, which all follow the expected pattern.

**Current Code** (lines 82-103):
```python
if match:
    region_id = match.group(1)
    file_id = match.group(2)
    original_filename = match.group(3)
    logger.info(...)
else:
    # Fallback: use defaults if path doesn't match expected pattern
    logger.warning(...)
    filename = object_path.split("/")[-1]
    file_id = filename.split("_")[0] if "_" in filename else filename.split(".")[0]
    region_id = "unknown"  # ❌ This allows invalid paths to continue
```

**New Code**:
```python
if match:
    region_id = match.group(1)
    file_id = match.group(2)
    original_filename = match.group(3)
    logger.info(...)
else:
    # Reject invalid paths immediately
    logger.error(
        "Object path does not match expected pattern",
        extra={
            "object_path": object_path,
            "expected_pattern": "uploads/{region_id}/{file_id}_{filename}"
        }
    )
    raise ValueError(
        f"Invalid object path: {object_path}. "
        f"Expected pattern: uploads/{{region_id}}/{{file_id}}_{{filename}}"
    )
```

**Impact**:
- Invalid paths will raise `ValueError`
- `process_cloud_event()` catches `ValueError` and returns HTTP 400
- Eventarc will NOT retry 400 errors

### 2. Retry Logic for Transformer Calls (MIME Decoder)

**File**: `src/eduscale/services/mime_decoder/clients.py`

**Changes**:
- Add retry logic to `call_transformer()` function
- 3 total attempts (1 initial + 2 retries)
- 2 second delay between attempts
- Retry on all HTTP errors (including 429)
- Log each attempt

**Current Code** (lines 35-70):
```python
async with httpx.AsyncClient(timeout=timeout) as client:
    try:
        response = await client.post(...)
        response.raise_for_status()
        result = response.json()
        logger.info(...)
        return result
    except httpx.HTTPError as e:
        logger.error(...)
        raise  # ❌ Immediately fails, no retry
```

**New Code**:
```python
import asyncio

MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2

async with httpx.AsyncClient(timeout=timeout) as client:
    last_error = None
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            logger.info(
                f"Calling Transformer service (attempt {attempt}/{MAX_ATTEMPTS})",
                extra={
                    "file_id": request.file_id,
                    "attempt": attempt,
                    "max_attempts": MAX_ATTEMPTS
                }
            )
            
            response = await client.post(...)
            response.raise_for_status()
            result = response.json()
            
            logger.info(
                f"Transformer service responded successfully",
                extra={
                    "file_id": request.file_id,
                    "status": result.get("status"),
                    "status_code": response.status_code,
                    "attempt": attempt
                }
            )
            
            return result
            
        except httpx.HTTPError as e:
            last_error = e
            status_code = getattr(e.response, "status_code", None) if hasattr(e, "response") else None
            
            logger.warning(
                f"Transformer service error (attempt {attempt}/{MAX_ATTEMPTS})",
                extra={
                    "file_id": request.file_id,
                    "attempt": attempt,
                    "max_attempts": MAX_ATTEMPTS,
                    "error": str(e),
                    "status_code": status_code
                }
            )
            
            # If this was the last attempt, raise the error
            if attempt == MAX_ATTEMPTS:
                logger.error(
                    f"Transformer service failed after {MAX_ATTEMPTS} attempts",
                    extra={
                        "file_id": request.file_id,
                        "total_attempts": MAX_ATTEMPTS,
                        "final_error": str(e),
                        "final_status_code": status_code
                    }
                )
                raise
            
            # Wait before retrying
            await asyncio.sleep(RETRY_DELAY_SECONDS)
```

**Impact**:
- Temporary failures (network issues, 429 rate limiting) will be retried
- 2 second delay prevents immediate retry storm
- After 3 failed attempts, returns 500 to trigger Eventarc retry (with exponential backoff)

### 3. Enhanced Logging (MIME Decoder)

**File**: `src/eduscale/services/mime_decoder/service.py`

**Changes**:
- Add processing outcome to all log entries
- Include total processing time
- Add structured fields for monitoring

**Key Log Points**:

1. **Event Receipt** (already exists, line 237):
```python
logger.info(
    "CloudEvent received",
    extra={
        "event_id": cloud_event.id,
        "bucket": cloud_event.data.bucket,
        "object_name": cloud_event.data.name,
        # ... existing fields ...
    }
)
```

2. **Path Validation Failure** (new, in models.py):
```python
logger.error(
    "Object path does not match expected pattern",
    extra={
        "event_id": event.id,
        "object_path": object_path,
        "expected_pattern": "uploads/{region_id}/{file_id}_{filename}",
        "outcome": "invalid_path"
    }
)
```

3. **Transformer Retry** (new, in clients.py):
```python
logger.warning(
    f"Transformer service error (attempt {attempt}/{MAX_ATTEMPTS})",
    extra={
        "event_id": request.event_id,
        "file_id": request.file_id,
        "attempt": attempt,
        "status_code": status_code,
        "error_type": type(e).__name__
    }
)
```

4. **Final Success** (update existing, line 295):
```python
logger.info(
    "Event processed successfully",
    extra={
        "event_id": cloud_event.id,
        "file_id": processing_req.file_id,
        "processing_time_ms": processing_time_ms,
        "outcome": "success",
        "transformer_attempts": 1  # or actual attempt count
    }
)
```

5. **Final Failure** (update existing, line 318):
```python
logger.error(
    "Failed to process CloudEvent",
    extra={
        "event_id": event_id,
        "object_name": object_name,
        "error": str(e),
        "error_type": type(e).__name__,
        "outcome": "failed"
    }
)
```

## Data Models

No changes to data models. Existing models are sufficient.

## Error Handling

### Error Types and HTTP Status Codes

| Error Type | HTTP Status | Eventarc Behavior | Example |
|------------|-------------|-------------------|---------|
| Invalid path (ValueError) | 400 | No retry | `text/abc123.txt` |
| Transformer failure after retries | 500 | Retry with backoff | Network error, 429 after 3 attempts |
| Storage error | 500 | Retry with backoff | GCS unavailable |
| Unexpected error | 500 | Retry with backoff | Code bug |

### Error Flow

```
CloudEvent received
  ↓
Path validation
  ├─ Valid → Continue
  └─ Invalid → ValueError → HTTP 400 → No retry ✅
  ↓
Call Transformer (with retry)
  ├─ Success → HTTP 200 ✅
  ├─ Retry 1 → Wait 2s → Retry 2 → Wait 2s → Retry 3
  └─ All failed → HTTPError → HTTP 500 → Eventarc retry ✅
```

## Testing Strategy

### Unit Tests

1. **Path Validation Tests** (`tests/test_mime_decoder_models.py`):
   - Valid path: `uploads/region-01/abc123_file.pdf` → Success
   - Invalid path: `text/abc123.txt` → ValueError
   - Invalid path: `uploads/region-01/abc123.pdf` (missing underscore) → ValueError
   - Invalid path: `other/file.pdf` → ValueError

2. **Retry Logic Tests** (`tests/test_mime_decoder.py`):
   - Mock Transformer to return 429 on first 2 attempts, 200 on 3rd → Success
   - Mock Transformer to return 429 on all 3 attempts → HTTPError raised
   - Mock Transformer to return 500 on first attempt, 200 on 2nd → Success
   - Verify 2 second delay between retries

3. **Error Handling Tests** (`tests/test_mime_decoder.py`):
   - Invalid path → HTTP 400 response
   - Transformer failure after retries → HTTP 500 response
   - Valid processing → HTTP 200 response

### Integration Tests

1. **Eventarc Filter Test** (manual):
   - Upload file to `uploads/region-01/test_file.pdf`
   - Verify MIME Decoder is triggered
   - Upload file to `text/test_file.txt`
   - Verify MIME Decoder is NOT triggered
   - Verify Tabular service IS triggered for `text/` files

2. **End-to-End Test** (manual):
   - Upload file → MIME Decoder → Transformer → text output
   - Verify no retry loop occurs
   - Check logs for proper outcome tracking

### Load Testing

1. **Archive Extraction Test**:
   - Upload archive with 50 files
   - Monitor Transformer service for 429 errors
   - Verify retry logic handles rate limiting gracefully

2. **Concurrent Upload Test**:
   - Upload 10 files simultaneously
   - Verify no retry storms
   - Check processing time and success rate

## Deployment Plan

### Phase 1: Terraform Changes (Immediate)

1. Update `infra/terraform/eventarc.tf`
2. Run `terraform plan` to verify changes
3. Run `terraform apply` to update Eventarc trigger
4. Verify trigger configuration in GCP Console

**Expected Impact**: Immediate reduction in retry storm as `text/` files no longer trigger MIME Decoder

### Phase 2: Code Changes (Next)

1. Update `src/eduscale/services/mime_decoder/models.py` (path validation)
2. Update `src/eduscale/services/mime_decoder/clients.py` (retry logic)
3. Update `src/eduscale/services/mime_decoder/service.py` (logging)
4. Run unit tests
5. Deploy to staging environment
6. Test manually
7. Deploy to production

**Expected Impact**: Defensive measures prevent future issues

### Rollback Plan

If issues occur after deployment:

1. **Terraform rollback**: Remove `matching_criteria` block from `storage_trigger`
2. **Code rollback**: Revert to previous deployment via GitHub Actions
3. **Verification**: Check Cloud Logging for errors and retry patterns

## Security Considerations

No security changes. Existing authentication and authorization remain unchanged.

## Performance Considerations

### Expected Improvements

1. **Reduced load on MIME Decoder**: ~50% reduction (no more `text/` file events)
2. **Reduced load on Transformer**: No more retry storms from invalid events
3. **Slightly increased latency**: 2-4 seconds added for retries (only on failures)

### Resource Usage

- **CPU**: Minimal increase (retry logic is lightweight)
- **Memory**: No change
- **Network**: Potential increase during retries (acceptable tradeoff)

## Open Questions

None. Design is straightforward and addresses root cause.

## Alternatives Considered

### Alternative 1: Circuit Breaker Pattern

**Pros**: Prevents cascading failures
**Cons**: Complex implementation, overkill for this issue
**Decision**: Not needed. Eventarc filter solves root cause.

### Alternative 2: Rate Limiting in MIME Decoder

**Pros**: Prevents overwhelming Transformer
**Cons**: Adds complexity, doesn't solve root cause
**Decision**: Not needed. Retry logic is sufficient.

### Alternative 3: Async Processing with Queue

**Pros**: Decouples services, better scalability
**Cons**: Major architecture change, high complexity
**Decision**: Not needed for current scale. Consider for future.

## Conclusion

This design provides a simple, effective solution to the retry storm issue by:

1. **Fixing root cause**: Eventarc filter prevents `text/` files from triggering MIME Decoder
2. **Adding defensive measures**: Path validation and retry logic prevent future issues
3. **Improving observability**: Enhanced logging enables better monitoring

The solution requires minimal code changes and can be deployed quickly to resolve the production issue.
