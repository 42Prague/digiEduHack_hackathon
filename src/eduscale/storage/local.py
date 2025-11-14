"""Local filesystem storage backend."""

import re
from pathlib import Path
from typing import BinaryIO

from eduscale.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self):
        self.base_path = Path("data/uploads")

    def get_target_path(self, file_id: str, file_name: str, region_id: str) -> str:
        """Generate local target path with region_id structure."""
        safe_name = self._sanitize_filename(file_name)
        # Use uploads/{region_id}/{file_id}_{filename} pattern
        # This preserves original filename while allowing MIME Decoder to extract region_id from path
        target_path = self.base_path / region_id / f"{file_id}_{safe_name}"
        return str(target_path)

    async def store_file(
        self, file_id: str, file_name: str, content_type: str, file_data: BinaryIO, region_id: str
    ) -> str:
        """Write file to local filesystem with region_id in path structure."""
        safe_name = self._sanitize_filename(file_name)
        # Use uploads/{region_id}/{file_id}_{filename} pattern
        # This preserves original filename while allowing MIME Decoder to extract region_id from path
        target_path = self.base_path / region_id / f"{file_id}_{safe_name}"

        # Create directory if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Stream write in chunks
        with open(target_path, "wb") as f:
            while chunk := file_data.read(65536):  # 64KB chunks
                f.write(chunk)

        return str(target_path)

    def get_backend_name(self) -> str:
        return "local"

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Remove path traversal and dangerous characters."""
        safe = filename.replace("../", "").replace("..\\", "")
        safe = safe.replace("/", "_").replace("\\", "_")
        safe = re.sub(r"[^a-zA-Z0-9._-]", "_", safe)
        return safe[:255]


# Singleton instance
local_backend = LocalStorageBackend()
