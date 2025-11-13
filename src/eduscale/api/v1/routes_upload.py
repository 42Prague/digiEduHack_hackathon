"""Upload API routes."""

import logging
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Body, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from eduscale.core.config import settings
from eduscale.models.upload import (
    CompleteUploadRequest,
    CreateSessionRequest,
    CreateSessionResponse,
    UploadResponse,
)
from eduscale.storage.factory import get_storage_backend
from eduscale.storage.gcs import gcs_backend
from eduscale.storage.upload_store import UploadRecord, UploadStatus, upload_store

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

        # Create upload record with COMPLETED status
        created_at = datetime.utcnow()
        record = UploadRecord(
            file_id=file_id,
            region_id=region_id.strip(),
            file_name=file.filename or "unnamed",
            content_type=file.content_type or "application/octet-stream",
            size_bytes=size_bytes,
            storage_backend=backend.get_backend_name(),
            storage_path=storage_path,
            status=UploadStatus.COMPLETED,
            created_at=created_at,
            completed_at=created_at,
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



@router.post("/upload/sessions", response_model=CreateSessionResponse, status_code=201)
async def create_upload_session(
    request: CreateSessionRequest = Body(...)
) -> CreateSessionResponse:
    """Create upload session for large files (>31 MB)."""
    try:
        # Validate region_id
        if not request.region_id or not request.region_id.strip():
            raise HTTPException(status_code=400, detail="region_id is required")

        # Validate file_size_bytes
        if request.file_size_bytes > settings.max_upload_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_MB}MB",
            )

        # Validate content_type if configured
        if settings.allowed_mime_types:
            if request.content_type not in settings.allowed_mime_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Content type {request.content_type} not allowed",
                )

        # Generate file_id
        file_id = str(uuid4())

        # Check if file size requires signed URL
        if request.file_size_bytes <= settings.direct_upload_threshold_bytes:
            # Return direct upload method
            backend = get_storage_backend()
            target_path = backend.get_target_path(file_id, request.file_name)
            return CreateSessionResponse(
                file_id=file_id,
                upload_method="direct",
                target_path=target_path,
            )

        # Generate signed URL for large files (GCS only)
        if settings.STORAGE_BACKEND != "gcs":
            raise HTTPException(
                status_code=400,
                detail=f"Large file uploads (>{settings.DIRECT_UPLOAD_SIZE_THRESHOLD_MB}MB) require GCS backend. Current backend: {settings.STORAGE_BACKEND}",
            )

        try:
            logger.info(f"Attempting to generate signed URL for file_id={file_id}, bucket={settings.GCS_BUCKET_NAME}")
            signed_url, blob_path = gcs_backend.generate_signed_upload_url(
                file_id=file_id,
                file_name=request.file_name,
                content_type=request.content_type,
                size_bytes=request.file_size_bytes,
                expiration_minutes=15,
            )
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to generate signed URL: {str(e)}")

        # Create pending upload record
        created_at = datetime.utcnow()
        upload_record = UploadRecord(
            file_id=file_id,
            region_id=request.region_id.strip(),
            file_name=request.file_name,
            content_type=request.content_type,
            size_bytes=request.file_size_bytes,
            storage_backend="gcs",
            storage_path=f"gs://{settings.GCS_BUCKET_NAME}/{blob_path}",
            status=UploadStatus.PENDING,
            created_at=created_at,
        )
        upload_store.create(upload_record)

        expires_at = datetime.utcnow() + timedelta(minutes=15)

        logger.info(
            f"Upload session created: file_id={file_id}, region_id={request.region_id}, "
            f"size={request.file_size_bytes}, method=signed_url"
        )

        return CreateSessionResponse(
            file_id=file_id,
            upload_method="signed_url",
            signed_url=signed_url,
            target_path=f"gs://{settings.GCS_BUCKET_NAME}/{blob_path}",
            expires_at=expires_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during session creation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/upload/complete", response_model=UploadResponse, status_code=200)
async def complete_upload(
    request: CompleteUploadRequest = Body(...)
) -> UploadResponse:
    """Complete signed URL upload and verify file exists."""
    try:
        # Validate file_id
        if not request.file_id or not request.file_id.strip():
            raise HTTPException(status_code=400, detail="file_id is required")

        # Get upload record from store
        record = upload_store.get(request.file_id)

        # Check if record exists
        if not record:
            raise HTTPException(status_code=404, detail="Upload record not found")

        # Verify file exists in GCS
        try:
            file_exists = gcs_backend.check_file_exists(record.file_id, record.file_name)
        except Exception as e:
            logger.error(f"Failed to check file existence: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to verify file")

        if not file_exists:
            raise HTTPException(
                status_code=400, detail="File does not exist in storage"
            )

        # Update status to COMPLETED
        completed_at = datetime.utcnow()
        upload_store.update_status(
            request.file_id, UploadStatus.COMPLETED, completed_at=completed_at
        )

        logger.info(
            f"Upload completed: file_id={request.file_id}, region_id={record.region_id}"
        )

        # Return upload metadata
        return UploadResponse(
            file_id=record.file_id,
            file_name=record.file_name,
            storage_backend=record.storage_backend,
            storage_path=record.storage_path,
            region_id=record.region_id,
            content_type=record.content_type,
            size_bytes=record.size_bytes,
            created_at=record.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during upload completion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@ui_router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Serve the upload UI page."""
    return templates.TemplateResponse("upload.html", {"request": request})
