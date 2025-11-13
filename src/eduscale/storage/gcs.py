"""Google Cloud Storage backend."""

import re
from typing import BinaryIO, Optional
from datetime import timedelta

from google.cloud import storage

from eduscale.core.config import settings
from eduscale.storage.base import StorageBackend


class GCSStorageBackend(StorageBackend):
    """Google Cloud Storage backend."""

    def __init__(self):
        self._client: Optional[storage.Client] = None
        self._bucket: Optional[storage.Bucket] = None

    def _get_bucket(self) -> storage.Bucket:
        """Lazy-load and cache GCS bucket."""
        if self._bucket is None:
            if not settings.GCS_BUCKET_NAME:
                raise ValueError("GCS_BUCKET_NAME not configured")

            self._client = storage.Client(project=settings.GCP_PROJECT_ID)
            self._bucket = self._client.bucket(settings.GCS_BUCKET_NAME)

        return self._bucket

    def get_target_path(self, file_id: str, file_name: str) -> str:
        """Generate GCS target path."""
        safe_name = self._sanitize_filename(file_name)
        blob_path = f"raw/{file_id}/{safe_name}"
        return f"gs://{settings.GCS_BUCKET_NAME}/{blob_path}"

    def generate_signed_upload_url(
        self,
        file_id: str,
        file_name: str,
        content_type: str,
        size_bytes: int,
        expiration_minutes: int = 15,
    ) -> tuple[str, str]:
        """Generate V4 signed URL for direct upload using IAM signBlob API.

        Returns:
            Tuple of (signed_url, blob_path)
        """
        from google.auth import compute_engine
        from google.auth.transport import requests as auth_requests
        
        bucket = self._get_bucket()

        safe_name = self._sanitize_filename(file_name)
        blob_path = f"raw/{file_id}/{safe_name}"
        blob = bucket.blob(blob_path)

        # Use compute engine credentials with IAM-based signing
        # This uses the IAM signBlob API instead of requiring a private key
        credentials = compute_engine.Credentials()
        
        # Refresh credentials to get the service account email
        auth_request = auth_requests.Request()
        credentials.refresh(auth_request)
        
        # Generate V4 signed URL for PUT using IAM signing
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="PUT",
            content_type=content_type,
            headers={"Content-Type": content_type},
            credentials=credentials,
            service_account_email=credentials.service_account_email,
        )

        return signed_url, blob_path

    def check_file_exists(self, file_id: str, file_name: str) -> bool:
        """Check if file exists in GCS."""
        bucket = self._get_bucket()
        safe_name = self._sanitize_filename(file_name)
        blob_path = f"raw/{file_id}/{safe_name}"
        blob = bucket.blob(blob_path)
        return blob.exists()

    async def store_file(
        self, file_id: str, file_name: str, content_type: str, file_data: BinaryIO
    ) -> str:
        """Upload file to GCS."""
        bucket = self._get_bucket()

        safe_name = self._sanitize_filename(file_name)
        blob_path = f"raw/{file_id}/{safe_name}"
        blob = bucket.blob(blob_path)

        # Stream upload in chunks
        blob.content_type = content_type
        blob.upload_from_file(file_data, rewind=True)

        return f"gs://{settings.GCS_BUCKET_NAME}/{blob_path}"

    def get_backend_name(self) -> str:
        return "gcs"

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Remove path traversal and dangerous characters."""
        safe = filename.replace("../", "").replace("..\\", "")
        safe = safe.replace("/", "_").replace("\\", "_")
        safe = re.sub(r"[^a-zA-Z0-9._-]", "_", safe)
        return safe[:255]


# Singleton instance
gcs_backend = GCSStorageBackend()
