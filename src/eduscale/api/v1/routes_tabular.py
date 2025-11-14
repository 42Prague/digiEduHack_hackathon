"""Tabular ingestion API endpoints for CloudEvents and direct API calls."""

import logging
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from eduscale.core.config import settings
from eduscale.services.transformer.storage import StorageClient
from eduscale.tabular.pipeline import process_tabular_text

logger = logging.getLogger(__name__)

router = APIRouter()


class CloudEventData(BaseModel):
    """CloudEvent data structure from Eventarc."""

    bucket: str
    name: str  # object_name
    contentType: str | None = None
    size: str | None = None


class TabularRequest(BaseModel):
    """Direct API request for tabular analysis (testing)."""

    file_id: str
    region_id: str
    text_uri: str
    original_content_type: str | None = None
    extraction_metadata: dict[str, Any] | None = None


class TabularResponse(BaseModel):
    """Response for tabular analysis."""

    file_id: str
    status: str  # INGESTED or FAILED
    table_type: str | None
    rows_loaded: int | None
    bytes_processed: int | None
    cache_hit: bool | None
    error_message: str | None
    warnings: list[str]
    processing_time_ms: int


@router.post("/")
async def handle_cloud_event(request: Request) -> dict[str, str]:
    """Handle CloudEvents from Eventarc for text file processing.

    This endpoint receives CloudEvents when text files are created in GCS
    and triggers the tabular ingestion pipeline.
    
    Supports both CloudEvent format and raw GCS notifications (when Eventarc
    is in GCS_NOTIFICATION mode).

    Args:
        request: FastAPI request containing CloudEvent or GCS notification

    Returns:
        dict: Success response with status

    Raises:
        HTTPException: 400 for invalid events, 500 for processing errors
    """
    try:
        # Parse event data
        event_data = await request.json()

        # Check if this is a raw GCS notification or a CloudEvent
        # GCS notifications have 'kind': 'storage#object'
        # CloudEvents have 'specversion', 'type', 'source', etc.
        if "kind" in event_data and event_data.get("kind") == "storage#object":
            # This is a raw GCS notification, extract data directly
            logger.info(
                "Received GCS notification (raw format)",
                extra={"kind": event_data.get("kind")},
            )
            bucket = event_data.get("bucket")
            object_name = event_data.get("name")
            event_id = event_data.get("id", event_data.get("generation", "unknown"))
            event_type = "google.cloud.storage.object.v1.finalized"
        else:
            # This is a CloudEvent
            event_id = event_data.get("id", "unknown")
            event_type = event_data.get("type", "")
            data = event_data.get("data", {})

            logger.info(
                f"Received CloudEvent: event_id={event_id}, type={event_type}",
                extra={"event_id": event_id, "event_type": event_type},
            )

            # Validate event type
            if event_type != "google.cloud.storage.object.v1.finalized":
                logger.warning(f"Unsupported event type: {event_type}")
                return {"status": "skipped", "reason": "unsupported_event_type"}

            # Extract bucket and object name from CloudEvent data
            bucket = data.get("bucket")
            object_name = data.get("name")

        if not bucket or not object_name:
            logger.error("Missing bucket or object_name in CloudEvent data")
            raise HTTPException(
                status_code=400, detail="Missing bucket or object_name in event data"
            )

        # Filter for text/*.txt pattern
        # Note: Eventarc trigger fires for ALL files in bucket (GCS direct events
        # only support 'type' and 'bucket' filtering). We filter by path here.
        if not object_name.startswith("text/") or not object_name.endswith(".txt"):
            logger.info(f"Skipping non-text file: {object_name}")
            return {"status": "skipped", "reason": "not_text_file"}

        # Extract file_id from object_name (text/{file_id}.txt)
        file_id = object_name.replace("text/", "").replace(".txt", "")

        logger.info(
            f"Processing text file: bucket={bucket}, object={object_name}, file_id={file_id}",
            extra={"event_id": event_id, "file_id": file_id, "bucket": bucket},
        )

        # Download text content from GCS
        storage_client = StorageClient(project_id=settings.GCP_PROJECT_ID)

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=True) as tmp_file:
            # Download file
            storage_client.download_file(
                bucket_name=bucket,
                object_name=object_name,
                destination=Path(tmp_file.name),
            )

            # Read content
            tmp_file.seek(0)
            text_content = tmp_file.read()

        logger.info(
            f"Downloaded text file: {len(text_content)} characters",
            extra={"event_id": event_id, "file_id": file_id},
        )

        # Process through tabular pipeline
        result = process_tabular_text(text_content)

        logger.info(
            f"Pipeline completed: file_id={result.file_id}, "
            f"status={result.status}, "
            f"table_type={result.table_type}, "
            f"rows={result.rows_loaded}",
            extra={
                "event_id": event_id,
                "file_id": result.file_id,
                "status": result.status,
                "table_type": result.table_type,
            },
        )

        # Log pipeline completion
        logger.info(
            f"Pipeline completed: file_id={result.file_id}, status={result.status}",
            extra={"event_id": event_id, "file_id": result.file_id},
        )

        # Return success to Eventarc
        return {
            "status": "success",
            "file_id": result.file_id,
            "table_type": result.table_type or "unknown",
            "rows_loaded": str(result.rows_loaded or 0),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"CloudEvent processing failed: {e}",
            exc_info=True,
            extra={"event_id": event_id if "event_id" in locals() else "unknown"},
        )
        # Return 500 to trigger Eventarc retry
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/api/v1/tabular/analyze")
async def analyze_tabular_direct(request: TabularRequest) -> TabularResponse:
    """Direct API endpoint for tabular analysis (testing/manual triggering).

    This endpoint allows direct API calls for testing without Eventarc.

    Args:
        request: TabularRequest with text_uri and metadata

    Returns:
        TabularResponse with status and metrics

    Raises:
        HTTPException: 400 for invalid requests, 500 for processing errors
    """
    try:
        logger.info(
            f"Direct API call: file_id={request.file_id}, text_uri={request.text_uri}",
            extra={"file_id": request.file_id, "text_uri": request.text_uri},
        )

        # Parse bucket and object from text_uri
        # Format: gs://bucket/object_name
        if not request.text_uri.startswith("gs://"):
            raise HTTPException(status_code=400, detail="Invalid text_uri format")

        uri_parts = request.text_uri.replace("gs://", "").split("/", 1)
        if len(uri_parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid text_uri format")

        bucket, object_name = uri_parts

        # Download text content from GCS
        storage_client = StorageClient(project_id=settings.GCP_PROJECT_ID)

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=True) as tmp_file:
            # Download file
            storage_client.download_file(
                bucket_name=bucket,
                object_name=object_name,
                destination=Path(tmp_file.name),
            )

            # Read content
            tmp_file.seek(0)
            text_content = tmp_file.read()

        logger.info(
            f"Downloaded text file: {len(text_content)} characters",
            extra={"file_id": request.file_id},
        )

        # Process through tabular pipeline
        result = process_tabular_text(text_content)

        logger.info(
            f"Pipeline completed: file_id={result.file_id}, status={result.status}",
            extra={"file_id": result.file_id, "status": result.status},
        )

        # Return response
        return TabularResponse(
            file_id=result.file_id,
            status=result.status,
            table_type=result.table_type,
            rows_loaded=result.rows_loaded,
            bytes_processed=result.bytes_processed,
            cache_hit=result.cache_hit,
            error_message=result.error_message,
            warnings=result.warnings,
            processing_time_ms=result.processing_time_ms,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Direct API processing failed: {e}",
            exc_info=True,
            extra={"file_id": request.file_id},
        )
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/health/tabular")
async def health_check() -> dict[str, Any]:
    """Health check endpoint for Tabular service.

    Returns service status and model loading status.

    Returns:
        dict: Health status with service info and model status
    """
    # TODO: Check if embedding model is loaded
    # TODO: Check if LLM is available

    return {
        "status": "ok",
        "service": "tabular-service",
        "version": settings.SERVICE_VERSION,
        "models": {
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
            "llm_model": settings.FEATHERLESS_LLM_MODEL,
            "llm_enabled": settings.LLM_ENABLED,
        },
    }
