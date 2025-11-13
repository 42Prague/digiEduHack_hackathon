"""Upload data models."""

from pydantic import BaseModel
from datetime import datetime


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
