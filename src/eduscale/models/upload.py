"""Upload data models."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


class CreateSessionRequest(BaseModel):
    """Request model for creating upload session."""

    region_id: str
    file_name: str
    file_size_bytes: int
    content_type: str


class CreateSessionResponse(BaseModel):
    """Response model for upload session creation."""

    file_id: str
    upload_method: Literal["direct", "signed_url"]
    signed_url: Optional[str] = None
    target_path: str
    expires_at: Optional[datetime] = None


class CompleteUploadRequest(BaseModel):
    """Request model for completing signed URL upload."""

    file_id: str


class UploadResponse(BaseModel):
    """Response model for file upload."""

    file_id: str
    file_name: str
    storage_backend: str
    storage_path: str
    region_id: str
    content_type: str
    size_bytes: int
    created_at: datetime
