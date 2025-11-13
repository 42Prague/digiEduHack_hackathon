"""Storage backend factory."""

from eduscale.core.config import settings
from eduscale.storage.base import StorageBackend
from eduscale.storage.gcs import gcs_backend
from eduscale.storage.local import local_backend


def get_storage_backend() -> StorageBackend:
    """Return the configured storage backend."""
    if settings.STORAGE_BACKEND == "gcs":
        return gcs_backend
    elif settings.STORAGE_BACKEND == "local":
        return local_backend
    else:
        raise ValueError(f"Unknown storage backend: {settings.STORAGE_BACKEND}")
