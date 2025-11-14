"""
Transformer Cloud Run service entry point.

FastAPI application that receives file transformation requests.
"""

import logging
import os
import sys
from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from eduscale.services.transformer.orchestrator import transform_file
from eduscale.services.transformer.exceptions import FileTooLargeError, TransformationError
from eduscale.services.transformer.storage import StorageClient
from eduscale.core.config import settings

# Configure JSON logging for Cloud Run
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
    title="Transformer Service",
    description="Extracts text from documents and audio files",
    version="0.1.0",
)


class TransformRequest(BaseModel):
    """Request model for file transformation."""

    file_id: str = Field(..., description="Unique identifier for the file")
    bucket: str = Field(..., description="GCS bucket name")
    object_name: str = Field(..., description="Object path in the bucket")
    content_type: str = Field(..., description="MIME type of the file")
    file_category: str = Field(
        ...,
        description="Category of the file (text, audio, image, archive, other)",
    )
    region_id: str | None = Field(None, description="Optional region identifier")


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint for Cloud Run."""
    try:
        health_status = {
            "service": "transformer",
            "status": "healthy",
            "dependencies": {},
        }

        # Check Cloud Storage connectivity
        try:
            storage_client = StorageClient(project_id=settings.GCP_PROJECT_ID or None)
            # Simple check - just initialize client
            health_status["dependencies"]["cloud_storage"] = "healthy"
        except Exception as e:
            logger.error("Cloud Storage health check failed", extra={"error": str(e)})
            health_status["dependencies"]["cloud_storage"] = "unhealthy"
            health_status["status"] = "degraded"

        # Return 503 if any critical dependency is unhealthy
        if health_status["dependencies"].get("cloud_storage") == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service unavailable: Cloud Storage unhealthy",
            )

        return health_status

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Health check failed", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health check failed",
        )


@app.post("/process")
async def process_file(request: TransformRequest) -> dict[str, Any]:
    """
    Process a file by extracting text with metadata frontmatter.

    Args:
        request: Transformation request with file details

    Returns:
        Transformation response with results

    Raises:
        HTTPException: 400 for client errors, 500 for server errors
    """
    try:
        logger.info(
            "Received transformation request",
            extra={
                "file_id": request.file_id,
                "bucket": request.bucket,
                "object_name": request.object_name,
                "content_type": request.content_type,
                "file_category": request.file_category,
                "region_id": request.region_id,
            },
        )

        # Validate request
        if not request.file_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="file_id is required",
            )

        if not request.bucket:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="bucket is required",
            )

        if not request.object_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="object_name is required",
            )

        # Transform file
        result = await transform_file(
            file_id=request.file_id,
            bucket=request.bucket,
            object_name=request.object_name,
            content_type=request.content_type,
            file_category=request.file_category,
            region_id=request.region_id,
        )

        logger.info(
            "Transformation completed successfully",
            extra={
                "file_id": request.file_id,
                "status": "transformed",
            },
        )

        return result

    except FileTooLargeError as e:
        logger.warning(
            "File too large",
            extra={
                "file_id": request.file_id,
                "error": str(e),
                "http_status": 400,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except TransformationError as e:
        logger.error(
            "Transformation failed",
            extra={
                "file_id": request.file_id,
                "error": str(e),
                "http_status": 500,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transformation failed: {str(e)}",
        )

    except Exception as e:
        logger.error(
            "Unexpected error during transformation",
            extra={
                "file_id": request.file_id,
                "error": str(e),
                "http_status": 500,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@app.on_event("startup")
async def startup_event():
    """Log service startup."""
    logger.info(
        "Transformer service started",
        extra={
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "gcp_project": os.getenv("GCP_PROJECT_ID", "unknown"),
            "gcp_region": os.getenv("GCP_REGION", "unknown"),
        },
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Log service shutdown."""
    logger.info("Transformer service shutting down")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
