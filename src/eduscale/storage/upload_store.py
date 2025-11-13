"""Upload record tracking store."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


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
    created_at: datetime


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

    def list_all(self) -> list[UploadRecord]:
        """List all upload records."""
        return list(self._uploads.values())


# Singleton instance
upload_store = UploadStore()
