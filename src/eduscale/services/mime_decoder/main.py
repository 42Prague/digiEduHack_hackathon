"""
MIME Decoder Cloud Run service entry point.

FastAPI application that receives CloudEvents from Eventarc.
"""

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


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy", "service": "mime-decoder"}


@app.post("/")
async def handle_cloud_event(request: Request):
    """
    Handle CloudEvent from Eventarc.

    Eventarc sends CloudEvents as HTTP POST requests to the root path.
    The CloudEvent data is in the request body as JSON.

    Returns:
        200: Event processed successfully
        400: Invalid event data (client error, no retry)
        500: Processing error (server error, will retry)
    """
    try:
        # Parse CloudEvent from request body
        event_data = await request.json()

        # Log request headers for debugging
        logger.debug(
            "Received CloudEvent request",
            extra={
                "headers": dict(request.headers),
                "client_host": request.client.host if request.client else "unknown",
            },
        )

        # Process the event
        result = process_cloud_event(event_data)

        # Return success response
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result,
        )

    except ValueError as e:
        # Client error - invalid event data (4xx)
        # Eventarc will NOT retry 4xx errors
        logger.warning(
            "Invalid CloudEvent data",
            extra={
                "error": str(e),
                "error_type": "validation_error",
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CloudEvent data: {str(e)}",
        )

    except Exception as e:
        # Server error - unexpected processing error (5xx)
        # Eventarc WILL retry 5xx errors with exponential backoff
        logger.error(
            "Failed to process CloudEvent",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process event: {str(e)}",
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
