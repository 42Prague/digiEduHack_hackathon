"""Health check endpoint for EduScale Engine."""

from fastapi import APIRouter

from eduscale.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint.
    
    Returns service status, name, and version information.
    This endpoint is optimized for fast response to avoid timeout issues.
    
    Returns:
        dict: Health status response with status, service, and version fields
    """
    # Simple, fast response without any heavy operations
    # This ensures health checks complete quickly even during startup
    return {
        "status": "ok",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
    }
