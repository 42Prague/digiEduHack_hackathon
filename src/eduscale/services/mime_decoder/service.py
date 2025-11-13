"""
MIME Decoder service implementation.

Handles CloudEvent processing and routes files to appropriate transformers.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any

from eduscale.services.mime_decoder.classifier import classify_mime_type
from eduscale.services.mime_decoder.models import CloudEvent, StorageObjectData, ProcessingRequest
from eduscale.services.mime_decoder.clients import call_transformer, update_backend_status
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

        # Call Transformer service
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
                "transformer_status": transformer_response.get("status")
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
