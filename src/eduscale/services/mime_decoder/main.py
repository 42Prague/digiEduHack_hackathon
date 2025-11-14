"""
MIME Decoder Cloud Run service entry point.

FastAPI application that receives CloudEvents from Eventarc.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse

from eduscale.services.mime_decoder.service import process_cloud_event

# Configure JSON logging for Cloud Run
# Import CloudLoggingFormatter from core.logging
from eduscale.core.logging import CloudLoggingFormatter

# Setup logging with JSON formatter
log_level = logging.INFO
env = os.getenv("ENVIRONMENT", "cloud")

handler = logging.StreamHandler(sys.stdout)
if env == "local":
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
else:
    formatter = CloudLoggingFormatter()
handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(log_level)
root_logger.handlers.clear()
root_logger.addHandler(handler)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MIME Decoder Service",
    description="Receives Cloud Storage events from Eventarc and routes files for processing",
    version="0.1.0",
)


async def _process_event_in_background(event_data: Dict[str, Any], event_id: str) -> None:
    """
    Process CloudEvent in background task.

    This function is executed asynchronously after returning 200 OK to Eventarc.
    All exceptions are caught and logged to prevent task failures.

    Args:
        event_data: CloudEvent data from request
        event_id: Unique event identifier for tracking
    """
    try:
        logger.info(
            "Starting background event processing",
            extra={"event_id": event_id}
        )

        result = await process_cloud_event(event_data)

        logger.info(
            "Background event processing completed",
            extra={
                "event_id": event_id,
                "result_status": result.get("status"),
            }
        )

    except Exception as e:
        # Log error but don't raise - background task should not fail
        logger.error(
            "Background event processing failed",
            extra={
                "event_id": event_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy", "service": "mime-decoder"}


@app.post("/")
async def handle_cloud_event(request: Request):
    """
    Handle CloudEvent from Eventarc.

    This endpoint immediately returns 200 OK to Eventarc and processes
    the event asynchronously in the background. This prevents timeout issues
    and allows Eventarc to acknowledge receipt quickly.

    Returns:
        200: Event accepted for processing (always)
        400: Invalid JSON in request body
    """
    try:
        # Parse CloudEvent from request body
        event_data = await request.json()

        # Extract event ID for tracking (use different fields as fallback)
        event_id = (
            event_data.get("id") or
            event_data.get("data", {}).get("generation") or
            "unknown"
        )

        # Log request receipt
        logger.info(
            "CloudEvent received, scheduling background processing",
            extra={
                "event_id": event_id,
                "event_type": event_data.get("type", "unknown"),
            },
        )

        # Schedule background processing (fire-and-forget)
        asyncio.create_task(_process_event_in_background(event_data, event_id))

        # Return 200 OK immediately
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "accepted",
                "event_id": event_id,
                "message": "Event accepted for background processing"
            },
        )

    except Exception as e:
        # Only fail if we can't parse the request body
        # This prevents Eventarc retries for malformed requests
        logger.warning(
            "Failed to parse CloudEvent request",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}",
        )


@app.on_event("startup")
async def startup_event():
    """Log service startup."""
    logger.info(
        "MIME Decoder service started",
        extra={
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "gcp_project": os.getenv("GCP_PROJECT_ID", "unknown"),
            "gcp_region": os.getenv("GCP_REGION", "unknown"),
            "uploads_bucket": os.getenv("UPLOADS_BUCKET", "unknown"),
        },
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Log service shutdown."""
    logger.info("MIME Decoder service shutting down")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
