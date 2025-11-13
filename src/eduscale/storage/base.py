"""Abstract storage backend interface."""

from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def get_target_path(self, file_id: str, file_name: str, region_id: str) -> str:
        """Generate target storage path.

        Args:
            file_id: Unique file identifier
            file_name: Original file name
            region_id: Region identifier for organizing files

        Returns:
            Target path for the file
        """
        pass

    @abstractmethod
    async def store_file(
        self, file_id: str, file_name: str, content_type: str, file_data: BinaryIO, region_id: str
    ) -> str:
        """Store uploaded file to backend.

        Args:
            file_id: Unique file identifier
            file_name: Original file name
            content_type: MIME type
            file_data: File content stream
            region_id: Region identifier for organizing files

        Returns:
            Final storage path
        """
        pass

    @abstractmethod
    def get_backend_name(self) -> str:
        """Return backend identifier."""
        pass
