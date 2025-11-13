"""Google Cloud Storage backend."""

import re
from typing import BinaryIO, Optional
from datetime import timedelta

from google.cloud import storage
from google.oauth2 import service_account

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

    def get_target_path(self, file_id: str, file_name: str, region_id: str) -> str:
        """Generate GCS target path with region_id in path structure."""
        safe_name = self._sanitize_filename(file_name)
        # Use uploads/{region_id}/{file_id}.{ext} pattern for MIME Decoder compatibility
        blob_path = f"uploads/{region_id}/{file_id}.{safe_name.split('.')[-1] if '.' in safe_name else 'bin'}"
        return f"gs://{settings.GCS_BUCKET_NAME}/{blob_path}"

    def generate_signed_upload_url(
        self,
        file_id: str,
        file_name: str,
        content_type: str,
        size_bytes: int,
        region_id: str,
        expiration_minutes: int = 15,
    ) -> tuple[str, str]:
        """Generate V4 signed URL for direct upload using IAM signBlob API.

        Returns:
            Tuple of (signed_url, blob_path)
        """
        from google.auth import iam
        from google.auth.transport import requests as auth_requests
        from google.auth import compute_engine

        bucket = self._get_bucket()

        safe_name = self._sanitize_filename(file_name)
        # Use uploads/{region_id}/{file_id}.{ext} pattern for MIME Decoder compatibility
        extension = safe_name.split('.')[-1] if '.' in safe_name else 'bin'
        blob_path = f"uploads/{region_id}/{file_id}.{extension}"
        blob = bucket.blob(blob_path)

        # Use compute engine credentials (works in Cloud Run / GCE / GKE)
        # This assumes your prod service is running as a service account.
        credentials = compute_engine.Credentials()

        # Create auth request for IAM operations
        auth_request = auth_requests.Request()

        # Refresh to get service account email
        credentials.refresh(auth_request)
        service_account_email = credentials.service_account_email

        # Create IAM signer that uses the signBlob API (no private key file needed)
        # The service account must have roles/iam.serviceAccountTokenCreator on itself.
        signer = iam.Signer(
            request=auth_request,
            credentials=credentials,
            service_account_email=service_account_email,
        )

        # Wrap the IAM signer into a Credentials object that the storage library
        # recognizes as having signing capability.
        signing_creds = service_account.Credentials(
            signer=signer,
            service_account_email=service_account_email,
            # Use the default Google OAuth2 token endpoint; we only need this
            # because the constructor requires a token_uri, but signing itself
            # is done via the IAM Signer above.
            token_uri="https://oauth2.googleapis.com/token",
        )

        # Generate V4 signed URL for PUT using IAM signing
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="PUT",
            content_type=content_type,
            headers={"Content-Type": content_type},
            credentials=signing_creds,
            service_account_email=service_account_email,
        )

        return signed_url, blob_path

    def check_file_exists(self, file_id: str, file_name: str, region_id: str) -> bool:
        """Check if file exists in GCS."""
        bucket = self._get_bucket()
        safe_name = self._sanitize_filename(file_name)
        extension = safe_name.split('.')[-1] if '.' in safe_name else 'bin'
        blob_path = f"uploads/{region_id}/{file_id}.{extension}"
        blob = bucket.blob(blob_path)
        return blob.exists()

    async def store_file(
        self, file_id: str, file_name: str, content_type: str, file_data: BinaryIO, region_id: str
    ) -> str:
        """Upload file to GCS with region_id in path structure."""
        bucket = self._get_bucket()

        safe_name = self._sanitize_filename(file_name)
        # Use uploads/{region_id}/{file_id}.{ext} pattern for MIME Decoder compatibility
        extension = safe_name.split('.')[-1] if '.' in safe_name else 'bin'
        blob_path = f"uploads/{region_id}/{file_id}.{extension}"
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
