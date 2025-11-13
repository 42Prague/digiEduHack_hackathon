"""Upload API routes."""

import logging
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from eduscale.core.config import settings
from eduscale.models.upload import UploadResponse
from eduscale.storage.factory import get_storage_backend
from eduscale.storage.upload_store import UploadRecord, upload_store

router = APIRouter(prefix="/api/v1", tags=["upload"])
ui_router = APIRouter()
templates = Jinja2Templates(directory="src/eduscale/ui/templates")
logger = logging.getLogger(__name__)



@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...), region_id: str = Form(...)
) -> UploadResponse:
    """Upload a file with metadata."""
    try:
        # Validate region_id
        if not region_id or not region_id.strip():
            raise HTTPException(status_code=400, detail="region_id is required")

        # Validate file size
        file.file.seek(0, 2)  # Seek to end
        size_bytes = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if size_bytes > settings.max_upload_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_MB}MB",
            )

        # Validate MIME type if configured
        if settings.allowed_mime_types:
            if file.content_type not in settings.allowed_mime_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Content type {file.content_type} not allowed",
                )

        # Generate file_id
        file_id = str(uuid4())

        # Get storage backend
        try:
            backend = get_storage_backend()
        except ValueError as e:
            logger.error(f"Storage backend configuration error: {e}")
            raise HTTPException(status_code=500, detail="Storage configuration error")

        # Stream file to storage backend
        try:
            storage_path = await backend.store_file(
                file_id=file_id,
                file_name=file.filename or "unnamed",
                content_type=file.content_type or "application/octet-stream",
                file_data=file.file,
            )
        except Exception as e:
            logger.error(f"Failed to store file: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to store file")

        # Create upload record
        created_at = datetime.utcnow()
        record = UploadRecord(
            file_id=file_id,
            region_id=region_id.strip(),
            file_name=file.filename or "unnamed",
            content_type=file.content_type or "application/octet-stream",
            size_bytes=size_bytes,
            storage_backend=backend.get_backend_name(),
            storage_path=storage_path,
            created_at=created_at,
        )
        upload_store.create(record)

        # Log upload completion
        logger.info(
            f"Upload completed: file_id={file_id}, region_id={region_id}, "
            f"backend={backend.get_backend_name()}, size={size_bytes}"
        )

        # Return response
        return UploadResponse(
            file_id=file_id,
            file_name=file.filename or "unnamed",
            storage_backend=backend.get_backend_name(),
            storage_path=storage_path,
            region_id=region_id.strip(),
            content_type=file.content_type or "application/octet-stream",
            size_bytes=size_bytes,
            created_at=created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")



@ui_router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Serve the upload UI page."""
    return templates.TemplateResponse("upload.html", {"request": request})
