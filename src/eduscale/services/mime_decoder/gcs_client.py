"""Google Cloud Storage client for archive extraction."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from google.cloud import storage
from google.api_core import retry
from google.api_core.exceptions import GoogleAPIError, NotFound

logger = logging.getLogger(__name__)


class GCSClient:
    """Client for Google Cloud Storage operations with retry logic."""

    def __init__(self, bucket_name: str):
        """Initialize GCS client with bucket name.
        
        Args:
            bucket_name: Name of the GCS bucket
        """
        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        
        # Configure retry with exponential backoff (3 retries)
        self.retry_policy = retry.Retry(
            initial=1.0,
            maximum=10.0,
            multiplier=2.0,
            deadline=60.0,
            predicate=retry.if_exception_type(GoogleAPIError)
        )

    async def download_file(self, object_name: str, destination_path: str) -> None:
        """Download file from GCS to local path.
        
        Args:
            object_name: Name of the object in GCS
            destination_path: Local path to save the file
            
        Raises:
            NotFound: If the object doesn't exist
            GoogleAPIError: If download fails after retries
        """
        try:
            blob = self.bucket.blob(object_name)
            
            # Run blocking operation in thread pool
            await asyncio.to_thread(
                blob.download_to_filename,
                destination_path,
                retry=self.retry_policy
            )
            
            logger.info(
                f"Downloaded {object_name} to {destination_path}",
                extra={"object_name": object_name, "destination": destination_path}
            )
        except NotFound:
            logger.error(
                f"Object not found: {object_name}",
                extra={"object_name": object_name, "bucket": self.bucket_name}
            )
            raise
        except GoogleAPIError as e:
            logger.error(
                f"Failed to download {object_name}: {e}",
                extra={"object_name": object_name, "error": str(e)}
            )
            raise

    async def upload_file(
        self,
        source_path: str,
        destination_name: str,
        content_type: str
    ) -> None:
        """Upload file from local path to GCS.
        
        Args:
            source_path: Local path of the file to upload
            destination_name: Name for the object in GCS
            content_type: MIME type of the file
            
        Raises:
            GoogleAPIError: If upload fails after retries
        """
        try:
            blob = self.bucket.blob(destination_name)
            
            # Run blocking operation in thread pool
            await asyncio.to_thread(
                blob.upload_from_filename,
                source_path,
                content_type=content_type,
                retry=self.retry_policy
            )
            
            logger.info(
                f"Uploaded {source_path} to {destination_name}",
                extra={
                    "source": source_path,
                    "destination": destination_name,
                    "content_type": content_type
                }
            )
        except GoogleAPIError as e:
            logger.error(
                f"Failed to upload {source_path}: {e}",
                extra={"source": source_path, "error": str(e)}
            )
            raise

    def get_file_size(self, object_name: str) -> int:
        """Get file size in bytes without downloading.
        
        Args:
            object_name: Name of the object in GCS
            
        Returns:
            File size in bytes
            
        Raises:
            NotFound: If the object doesn't exist
        """
        try:
            blob = self.bucket.blob(object_name)
            blob.reload()
            return blob.size
        except NotFound:
            logger.error(
                f"Object not found: {object_name}",
                extra={"object_name": object_name, "bucket": self.bucket_name}
            )
            raise
