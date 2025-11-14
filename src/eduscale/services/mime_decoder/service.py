"""
MIME Decoder service implementation.

Handles CloudEvent processing and routes files to appropriate transformers.
"""

import asyncio
import json
import logging
import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from eduscale.services.mime_decoder.classifier import classify_mime_type
from eduscale.services.mime_decoder.models import CloudEvent, StorageObjectData, ProcessingRequest, FileSkippedException
from eduscale.services.mime_decoder.clients import call_transformer, update_backend_status
from eduscale.services.mime_decoder.gcs_client import GCSClient
from eduscale.services.mime_decoder.archive_extractor import ArchiveExtractor
from eduscale.core.config import settings

# Configure structured logging for Cloud Logging
logger = logging.getLogger(__name__)


def _convert_gcs_notification_to_cloud_event(gcs_data: Dict[str, Any]) -> CloudEvent:
    """
    Convert a raw GCS notification to CloudEvent format.
    
    GCS notifications are sent when Eventarc is in GCS_NOTIFICATION mode.
    This function normalizes them to the CloudEvent format expected by the service.
    
    Args:
        gcs_data: Raw GCS notification data
        
    Returns:
        CloudEvent object
        
    Raises:
        ValueError: If required fields are missing
    """
    try:
        # Extract required fields from GCS notification
        bucket = gcs_data.get("bucket")
        name = gcs_data.get("name")
        content_type = gcs_data.get("contentType", "application/octet-stream")
        size = gcs_data.get("size", "0")
        time_created = gcs_data.get("timeCreated")
        updated = gcs_data.get("updated")
        generation = gcs_data.get("generation")
        metageneration = gcs_data.get("metageneration")
        event_id = gcs_data.get("id", gcs_data.get("generation", "unknown"))
        
        if not bucket or not name:
            raise ValueError("Missing required fields: bucket and name")
        
        # Create StorageObjectData
        storage_data = StorageObjectData(
            bucket=bucket,
            name=name,
            contentType=content_type,
            size=size,
            timeCreated=time_created or datetime.utcnow().isoformat(),
            updated=updated or datetime.utcnow().isoformat(),
            generation=generation,
            metageneration=metageneration,
        )
        
        # Create CloudEvent wrapper
        cloud_event = CloudEvent(
            specversion="1.0",
            type="google.cloud.storage.object.v1.finalized",
            source=f"//storage.googleapis.com/buckets/{bucket}",
            subject=f"objects/{name}",
            id=event_id,
            time=time_created or datetime.utcnow().isoformat(),
            datacontenttype="application/json",
            data=storage_data,
        )
        
        logger.info(
            "Converted GCS notification to CloudEvent",
            extra={
                "bucket": bucket,
                "object_name": name,
                "event_id": event_id,
            },
        )
        
        return cloud_event
        
    except Exception as e:
        logger.error(
            "Failed to convert GCS notification to CloudEvent",
            extra={
                "error": str(e),
                "gcs_data": json.dumps(gcs_data, default=str),
            },
            exc_info=True,
        )
        raise ValueError(f"Invalid GCS notification format: {str(e)}")


async def process_archive(
    cloud_event: CloudEvent,
    processing_req: ProcessingRequest,
) -> Dict[str, Any]:
    """
    Process an archive file by extracting and processing contents.
    
    Args:
        cloud_event: CloudEvent containing archive metadata
        processing_req: Processing request for the archive
        
    Returns:
        Response dictionary with extraction statistics
    """
    start_time = time.time()
    temp_dir = None
    
    try:
        # Check archive size
        archive_size_bytes = int(cloud_event.data.size)
        if archive_size_bytes > settings.max_archive_size_bytes:
            logger.warning(
                f"Archive exceeds size limit, skipping extraction",
                extra={
                    "event_id": cloud_event.id,
                    "archive_size_mb": archive_size_bytes / (1024 * 1024),
                    "max_size_mb": settings.MAX_ARCHIVE_SIZE_MB
                }
            )
            return {
                "status": "skipped",
                "reason": "archive_too_large",
                "message": f"Archive size {archive_size_bytes} exceeds limit"
            }
        
        # Determine archive type from content type
        content_type = cloud_event.data.contentType.lower()
        if "zip" in content_type:
            archive_type = "zip"
        elif "tar" in content_type:
            archive_type = "tar"
        elif "gzip" in content_type or "x-gzip" in content_type:
            archive_type = "gzip"
        else:
            archive_type = "zip"  # default
        
        logger.info(
            "Starting archive extraction",
            extra={
                "event_id": cloud_event.id,
                "archive_name": cloud_event.data.name,
                "archive_size_mb": archive_size_bytes / (1024 * 1024),
                "archive_type": archive_type
            }
        )
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="archive_")
        archive_path = os.path.join(temp_dir, "archive")
        extract_dir = os.path.join(temp_dir, "extracted")
        
        # Initialize GCS client
        bucket_name = settings.UPLOADS_BUCKET or cloud_event.data.bucket
        gcs_client = GCSClient(bucket_name)
        
        # Download archive from GCS
        await gcs_client.download_file(cloud_event.data.name, archive_path)
        
        # Extract archive
        extractor = ArchiveExtractor(
            max_files=settings.MAX_FILES_PER_ARCHIVE,
            max_file_size_mb=settings.MAX_EXTRACTED_FILE_SIZE_MB
        )
        extracted_files = await extractor.extract_archive(
            archive_path, archive_type, extract_dir
        )
        
        logger.info(
            f"Extracted {len(extracted_files)} files from archive",
            extra={
                "event_id": cloud_event.id,
                "files_extracted": len(extracted_files)
            }
        )
        
        # Process each extracted file
        files_uploaded = 0
        files_processed = 0
        
        # Extract archive ID from the original path
        # uploads/{region_id}/{archive_id}_{original_name}.zip -> archive_id
        archive_name_parts = Path(cloud_event.data.name).stem
        
        for extracted_file in extracted_files:
            try:
                # Generate unique file_id for extracted file
                # Use hyphen to separate archive_id from extracted filename stem
                extracted_file_id = f"{processing_req.file_id}-{Path(extracted_file.filename).stem}"
                
                # Upload extracted file to GCS
                # Pattern: uploads/{region_id}/{file_id}_{filename}
                # For extracted files: file_id contains hyphen (e.g., abc123-document)
                destination_name = f"uploads/{processing_req.region_id}/{extracted_file_id}_{extracted_file.filename}"
                
                await gcs_client.upload_file(
                    extracted_file.local_path,
                    destination_name,
                    extracted_file.mime_type
                )
                files_uploaded += 1
                
                # Classify extracted file
                file_category = classify_mime_type(extracted_file.mime_type)
                
                logger.info(
                    "Processing extracted file",
                    extra={
                        "event_id": cloud_event.id,
                        "file_name": extracted_file.filename,
                        "mime_type": extracted_file.mime_type,
                        "file_category": file_category.value,
                        "size_bytes": extracted_file.size_bytes
                    }
                )
                
                # Don't recursively extract nested archives, but still process them
                if file_category.value == "archive":
                    logger.info(
                        "Found nested archive (will process but not extract)",
                        extra={
                            "event_id": cloud_event.id,
                            "file_name": extracted_file.filename
                        }
                    )
                    # Don't continue - let it be processed by Transformer
                
                # Create processing request for extracted file
                extracted_processing_req = ProcessingRequest(
                    file_id=extracted_file_id,
                    region_id=processing_req.region_id,
                    bucket=bucket_name,
                    object_name=destination_name,
                    content_type=extracted_file.mime_type,
                    size_bytes=str(extracted_file.size_bytes),
                    file_category=file_category.value,
                    timestamp=datetime.utcnow().isoformat()
                )
                
                # Call Transformer service
                await call_transformer(
                    request=extracted_processing_req,
                    transformer_url=settings.TRANSFORMER_SERVICE_URL,
                    timeout=settings.REQUEST_TIMEOUT
                )
                
                # Update Backend status
                asyncio.create_task(
                    update_backend_status(
                        file_id=extracted_processing_req.file_id,
                        region_id=extracted_processing_req.region_id,
                        status="PROCESSING",
                        backend_url=settings.BACKEND_SERVICE_URL,
                        timeout=settings.BACKEND_UPDATE_TIMEOUT
                    )
                )
                
                files_processed += 1
                
            except Exception as e:
                logger.error(
                    f"Failed to process extracted file: {e}",
                    extra={
                        "event_id": cloud_event.id,
                        "extracted_filename": extracted_file.filename,
                        "error": str(e)
                    }
                )
                # Continue with next file
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "Archive extraction completed",
            extra={
                "event_id": cloud_event.id,
                "files_extracted": len(extracted_files),
                "files_uploaded": files_uploaded,
                "files_processed": files_processed,
                "processing_time_ms": processing_time_ms,
                "outcome": "success"
            }
        )
        
        return {
            "status": "success",
            "event_id": cloud_event.id,
            "archive_name": cloud_event.data.name,
            "files_extracted": len(extracted_files),
            "files_uploaded": files_uploaded,
            "files_processed": files_processed,
            "processing_time_ms": processing_time_ms,
            "message": "Archive processed successfully"
        }
        
    except Exception as e:
        logger.error(
            f"Archive processing failed: {e}",
            extra={
                "event_id": cloud_event.id,
                "archive_name": cloud_event.data.name,
                "error": str(e),
                "error_type": type(e).__name__,
                "outcome": "failed"
            },
            exc_info=True
        )
        raise
    
    finally:
        # Cleanup temporary files
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.debug(
                    "Cleaned up temporary directory",
                    extra={"temp_dir": temp_dir}
                )
            except Exception as e:
                logger.warning(
                    f"Failed to cleanup temp directory: {e}",
                    extra={"temp_dir": temp_dir, "error": str(e)}
                )


async def process_cloud_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a CloudEvent from Eventarc.

    Args:
        event_data: Raw CloudEvent data from Eventarc (or GCS notification)

    Returns:
        Response dictionary with status and details

    Raises:
        ValueError: If event data is invalid
        Exception: For unexpected processing errors
    """
    start_time = time.time()
    
    try:
        # Check if this is a raw GCS notification or a CloudEvent
        # GCS notifications have 'kind': 'storage#object'
        # CloudEvents have 'specversion', 'type', 'source', etc.
        if "kind" in event_data and event_data.get("kind") == "storage#object":
            # This is a raw GCS notification, convert it to CloudEvent format
            cloud_event = _convert_gcs_notification_to_cloud_event(event_data)
        else:
            # This is already a CloudEvent
            cloud_event = CloudEvent(**event_data)

        # Log event receipt
        logger.info(
            "CloudEvent received",
            extra={
                "event_id": cloud_event.id,
                "event_type": cloud_event.type,
                "bucket": cloud_event.data.bucket,
                "object_name": cloud_event.data.name,
                "content_type": cloud_event.data.contentType,
                "size_bytes": cloud_event.data.size,
                "timestamp": cloud_event.time.isoformat(),
            },
        )

        # Classify file type
        file_category = classify_mime_type(cloud_event.data.contentType)

        # Create processing request
        processing_req = ProcessingRequest.from_cloud_event(
            cloud_event, file_category.value
        )

        # Log successful classification
        logger.info(
            "File classified successfully",
            extra={
                "event_id": cloud_event.id,
                "file_id": processing_req.file_id,
                "region_id": processing_req.region_id,
                "file_category": file_category.value,
                "content_type": cloud_event.data.contentType,
            },
        )

        # Check if file is an archive and archive extraction is enabled
        if file_category.value == "archive" and settings.ENABLE_ARCHIVE_EXTRACTION:
            logger.info(
                "Processing archive file",
                extra={
                    "event_id": cloud_event.id,
                    "file_id": processing_req.file_id,
                    "archive_name": cloud_event.data.name
                }
            )
            return await process_archive(cloud_event, processing_req)

        # Call Transformer service for non-archive files
        try:
            transformer_response = await call_transformer(
                request=processing_req,
                transformer_url=settings.TRANSFORMER_SERVICE_URL,
                timeout=settings.REQUEST_TIMEOUT
            )

            # Fire-and-forget Backend status update (don't await)
            asyncio.create_task(
                update_backend_status(
                    file_id=processing_req.file_id,
                    region_id=processing_req.region_id,
                    status="PROCESSING",
                    backend_url=settings.BACKEND_SERVICE_URL,
                    timeout=settings.BACKEND_UPDATE_TIMEOUT
                )
            )

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "Event processed successfully",
                extra={
                    "event_id": cloud_event.id,
                    "file_id": processing_req.file_id,
                    "region_id": processing_req.region_id,
                    "processing_time_ms": processing_time_ms,
                    "transformer_status": transformer_response.get("status"),
                    "outcome": "success"
                }
            )

            return {
                "status": "success",
                "event_id": cloud_event.id,
                "file_id": processing_req.file_id,
                "region_id": processing_req.region_id,
                "file_category": file_category.value,
                "processing_time_ms": processing_time_ms,
                "transformer_status": transformer_response.get("status"),
                "message": "Event processed successfully",
            }

        except Exception as transformer_error:
            # Transformer service failed - log error and return success to prevent Eventarc retry
            processing_time_ms = int((time.time() - start_time) * 1000)

            logger.error(
                "Transformer service failed - returning success to prevent retry",
                extra={
                    "event_id": cloud_event.id,
                    "file_id": processing_req.file_id,
                    "region_id": processing_req.region_id,
                    "file_category": file_category.value,
                    "processing_time_ms": processing_time_ms,
                    "error": str(transformer_error),
                    "error_type": type(transformer_error).__name__,
                    "outcome": "failed"
                },
                exc_info=True,
            )

            # Fire-and-forget Backend status update with FAILED status
            asyncio.create_task(
                update_backend_status(
                    file_id=processing_req.file_id,
                    region_id=processing_req.region_id,
                    status="FAILED",
                    backend_url=settings.BACKEND_SERVICE_URL,
                    timeout=settings.BACKEND_UPDATE_TIMEOUT
                )
            )

            return {
                "status": "failed",
                "event_id": cloud_event.id,
                "file_id": processing_req.file_id,
                "region_id": processing_req.region_id,
                "file_category": file_category.value,
                "processing_time_ms": processing_time_ms,
                "error": str(transformer_error),
                "message": "Transformer service failed - event will not be retried",
            }

    except FileSkippedException as e:
        # File is outside the expected directory - return success without processing
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract event metadata for response
        event_id = event_data.get("id", "unknown")
        object_name = event_data.get("data", {}).get("name", event_data.get("name", "unknown"))

        return {
            "status": "skipped",
            "event_id": event_id,
            "object_name": object_name,
            "processing_time_ms": processing_time_ms,
            "message": "File skipped: outside expected directory pattern",
        }

    except ValueError as e:
        # Client error - invalid event data (4xx)
        logger.error(
            "Invalid CloudEvent data",
            extra={
                "error": str(e),
                "error_type": "validation_error",
                "event_data": json.dumps(event_data, default=str),
            },
            exc_info=True,
        )
        raise

    except Exception as e:
        # Server error - unexpected processing error (5xx)
        # Extract event metadata if possible for logging
        event_id = event_data.get("id", "unknown")
        event_type = event_data.get("type", "unknown")
        bucket = event_data.get("data", {}).get("bucket", "unknown")
        object_name = event_data.get("data", {}).get("name", "unknown")
        content_type = event_data.get("data", {}).get("contentType", "unknown")
        size = event_data.get("data", {}).get("size", "unknown")

        # Structured error log with full context for failed events
        logger.error(
            "Failed to process CloudEvent",
            extra={
                "event_id": event_id,
                "event_type": event_type,
                "bucket": bucket,
                "object_name": object_name,
                "content_type": content_type,
                "size_bytes": size,
                "error": str(e),
                "error_type": type(e).__name__,
                "outcome": "failed"
            },
            exc_info=True,
        )
        raise


def log_retry_failure(
    event_id: str,
    bucket: str,
    object_name: str,
    content_type: str,
    size_bytes: str,
    error_message: str,
    retry_count: int,
    initial_timestamp: str,
    final_timestamp: str,
) -> None:
    """
    Log final failure after all retry attempts are exhausted.

    This is called by Eventarc after all retries fail.
    The log entry contains all information needed for manual reprocessing.

    Args:
        event_id: Unique CloudEvent ID
        bucket: Cloud Storage bucket name
        object_name: Object path in bucket
        content_type: MIME type of the file
        size_bytes: File size in bytes
        error_message: Last error message from MIME Decoder
        retry_count: Total number of retry attempts
        initial_timestamp: Timestamp of first attempt
        final_timestamp: Timestamp of final failure
    """
    logger.error(
        "Event processing failed after all retries exhausted",
        extra={
            "severity": "ERROR",
            "event_id": event_id,
            "bucket": bucket,
            "object_name": object_name,
            "content_type": content_type,
            "size_bytes": size_bytes,
            "error_message": error_message,
            "retry_count": retry_count,
            "initial_timestamp": initial_timestamp,
            "final_timestamp": final_timestamp,
            "manual_reprocessing_required": True,
        },
    )
