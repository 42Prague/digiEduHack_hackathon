"""Abstract storage backend interface."""

from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def get_target_path(self, file_id: str, file_name: str) -> str:
        """Generate target storage path.

        Returns:
            Target path for the file
        """
        pass

    @abstractmethod
    async def store_file(
        self, file_id: str, file_name: str, content_type: str, file_data: BinaryIO
    ) -> str:
        """Store uploaded file to backend.

        Returns:
            Final storage path
        """
        pass

    @abstractmethod
    def get_backend_name(self) -> str:
        """Return backend identifier."""
        pass
