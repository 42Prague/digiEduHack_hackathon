"""HTTP clients for calling Transformer and Backend services."""

import asyncio
import logging
from typing import Dict, Any

import httpx

from .models import ProcessingRequest

logger = logging.getLogger(__name__)


async def call_transformer(
    request: ProcessingRequest,
    transformer_url: str,
    timeout: int = 300
) -> Dict[str, Any]:
    """
    Call the Transformer service with file processing request.
    
    Args:
        request: Processing request with file metadata
        transformer_url: Base URL of Transformer service
        timeout: Request timeout in seconds (default 300s)
        
    Returns:
        Response dict with status and any additional data
        
    Raises:
        httpx.HTTPError: If request fails
        httpx.TimeoutException: If request times out
    """
    payload = {
        "file_id": request.file_id,
        "region_id": request.region_id,
        "bucket": request.bucket,
        "object_name": request.object_name,
        "content_type": request.content_type,
        "file_category": request.file_category,
        "size_bytes": request.size_bytes,
        "event_id": request.event_id,
        "timestamp": request.timestamp.isoformat()
    }
    
    logger.info(
        f"Calling Transformer service",
        extra={
            "file_id": request.file_id,
            "region_id": request.region_id,
            "category": request.file_category,
            "transformer_url": transformer_url
        }
    )
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(
                f"{transformer_url}/process",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            logger.info(
                f"Transformer service responded successfully",
                extra={
                    "file_id": request.file_id,
                    "status": result.get("status"),
                    "status_code": response.status_code
                }
            )
            
            return result
            
        except httpx.TimeoutException as e:
            logger.error(
                f"Transformer service timeout",
                extra={
                    "file_id": request.file_id,
                    "timeout": timeout,
                    "error": str(e)
                }
            )
            raise
            
        except httpx.HTTPError as e:
            logger.error(
                f"Transformer service HTTP error",
                extra={
                    "file_id": request.file_id,
                    "error": str(e),
                    "status_code": getattr(e.response, "status_code", None) if hasattr(e, "response") else None
                }
            )
            raise


async def update_backend_status(
    file_id: str,
    region_id: str,
    status: str,
    backend_url: str,
    timeout: int = 5
) -> None:
    """
    Update Backend service with processing status (fire-and-forget).
    
    This function is designed to be called with asyncio.create_task() and not awaited.
    Errors are logged but don't propagate to the caller.
    
    Args:
        file_id: File identifier
        region_id: Region identifier
        status: Processing status to report
        backend_url: Base URL of Backend service
        timeout: Request timeout in seconds (default 5s)
    """
    payload = {
        "file_id": file_id,
        "region_id": region_id,
        "status": status
    }
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{backend_url}/api/files/status",
                json=payload
            )
            response.raise_for_status()
            
            logger.info(
                f"Backend status updated successfully",
                extra={
                    "file_id": file_id,
                    "region_id": region_id,
                    "status": status
                }
            )
            
    except httpx.TimeoutException:
        logger.warning(
            f"Backend status update timeout (non-critical)",
            extra={
                "file_id": file_id,
                "region_id": region_id,
                "timeout": timeout
            }
        )
        
    except httpx.HTTPError as e:
        logger.warning(
            f"Backend status update failed (non-critical)",
            extra={
                "file_id": file_id,
                "region_id": region_id,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None) if hasattr(e, "response") else None
            }
        )
        
    except Exception as e:
        logger.warning(
            f"Backend status update unexpected error (non-critical)",
            extra={
                "file_id": file_id,
                "region_id": region_id,
                "error": str(e)
            }
        )
