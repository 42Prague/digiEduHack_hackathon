"""Upload record tracking store."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
from enum import Enum


class UploadStatus(str, Enum):
    """Upload status enumeration."""

    PENDING = "pending"  # Session created, awaiting file upload
    COMPLETED = "completed"  # File uploaded and verified


@dataclass
class UploadRecord:
    """Upload record metadata."""

    file_id: str
    region_id: str
    file_name: str
    content_type: str
    size_bytes: int
    storage_backend: str
    storage_path: str
    status: UploadStatus
    created_at: datetime
    completed_at: Optional[datetime] = None


class UploadStore:
    """In-memory store for upload records."""

    def __init__(self):
        self._uploads: Dict[str, UploadRecord] = {}

    def create(self, record: UploadRecord) -> None:
        """Store a new upload record."""
        self._uploads[record.file_id] = record

    def get(self, file_id: str) -> Optional[UploadRecord]:
        """Retrieve an upload record by file_id."""
        return self._uploads.get(file_id)

    def update_status(
        self, file_id: str, status: UploadStatus, completed_at: Optional[datetime] = None
    ) -> None:
        """Update upload record status."""
        if file_id in self._uploads:
            self._uploads[file_id].status = status
            if completed_at:
                self._uploads[file_id].completed_at = completed_at

    def list_all(self) -> list[UploadRecord]:
        """List all upload records."""
        return list(self._uploads.values())


# Singleton instance
upload_store = UploadStore()
