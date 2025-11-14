"""Cloud Storage operations for Transformer service."""

import logging
from pathlib import Path
from typing import BinaryIO, Iterator

from google.cloud import storage
from google.cloud.exceptions import NotFound, Forbidden
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from eduscale.services.transformer.exceptions import StorageError

logger = logging.getLogger(__name__)


class StorageClient:
    """Client for Google Cloud Storage operations."""

    def __init__(self, project_id: str | None = None):
        """Initialize GCS client.

        Args:
            project_id: GCP project ID. If None, uses default credentials.
        """
        self.client = storage.Client(project=project_id)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    def download_file(self, bucket_name: str, object_name: str, destination: Path) -> None:
        """Download a file from Cloud Storage.

        Args:
            bucket_name: Name of the GCS bucket
            object_name: Path to the object in the bucket
            destination: Local file path to save the downloaded file

        Raises:
            StorageError: If download fails
        """
        try:
            logger.info(
                "Downloading file from GCS",
                extra={
                    "bucket": bucket_name,
                    "object_name": object_name,
                    "destination": str(destination),
                },
            )
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_name)

            # Create parent directories if they don't exist
            destination.parent.mkdir(parents=True, exist_ok=True)

            blob.download_to_filename(str(destination))

            logger.info(
                "File downloaded successfully",
                extra={
                    "bucket": bucket_name,
                    "object_name": object_name,
                    "size_bytes": destination.stat().st_size,
                },
            )
        except NotFound as e:
            logger.error(
                "File not found in GCS",
                extra={"bucket": bucket_name, "object_name": object_name},
            )
            raise StorageError(f"File not found: gs://{bucket_name}/{object_name}") from e
        except Forbidden as e:
            logger.error(
                "Access forbidden to GCS file",
                extra={"bucket": bucket_name, "object_name": object_name},
            )
            raise StorageError(f"Access denied: gs://{bucket_name}/{object_name}") from e
        except Exception as e:
            logger.error(
                "Failed to download file from GCS",
                extra={
                    "bucket": bucket_name,
                    "object_name": object_name,
                    "error": str(e),
                },
            )
            raise StorageError(f"Failed to download file: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    def upload_text_streaming(
        self,
        bucket_name: str,
        object_name: str,
        text_chunks: Iterator[str],
        content_type: str = "text/plain"
    ) -> str:
        """Upload text content to Cloud Storage using streaming approach.

        This method is more memory-efficient for large texts as it writes chunks
        sequentially without loading the entire content into memory.

        Args:
            bucket_name: Name of the GCS bucket
            object_name: Path to store the object in the bucket
            text_chunks: Iterator/generator yielding text chunks to upload
            content_type: MIME type of the content

        Returns:
            GCS URI of the uploaded file (gs://bucket/object)

        Raises:
            StorageError: If upload fails
        """
        try:
            logger.info(
                "Uploading text to GCS (streaming)",
                extra={
                    "bucket": bucket_name,
                    "object_name": object_name,
                },
            )
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_name)
            blob.content_type = content_type

            # Use blob.open() for streaming writes
            total_bytes = 0
            with blob.open("w", encoding="utf-8") as f:
                for chunk in text_chunks:
                    f.write(chunk)
                    total_bytes += len(chunk.encode("utf-8"))

            gcs_uri = f"gs://{bucket_name}/{object_name}"
            logger.info(
                "Text uploaded successfully (streaming)",
                extra={"gcs_uri": gcs_uri, "size_bytes": total_bytes},
            )
            return gcs_uri
        except Exception as e:
            logger.error(
                "Failed to upload text to GCS (streaming)",
                extra={
                    "bucket": bucket_name,
                    "object_name": object_name,
                    "error": str(e),
                },
            )
            raise StorageError(f"Failed to upload text (streaming): {e}") from e

    def stream_large_file(self, bucket_name: str, object_name: str) -> BinaryIO:
        """Stream a large file from Cloud Storage without downloading entirely.

        Args:
            bucket_name: Name of the GCS bucket
            object_name: Path to the object in the bucket

        Returns:
            Binary stream of the file content

        Raises:
            StorageError: If streaming fails
        """
        try:
            logger.info(
                "Streaming large file from GCS",
                extra={"bucket": bucket_name, "object_name": object_name},
            )
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_name)

            return blob.open("rb")
        except NotFound as e:
            logger.error(
                "File not found for streaming",
                extra={"bucket": bucket_name, "object_name": object_name},
            )
            raise StorageError(f"File not found: gs://{bucket_name}/{object_name}") from e
        except Exception as e:
            logger.error(
                "Failed to stream file from GCS",
                extra={
                    "bucket": bucket_name,
                    "object_name": object_name,
                    "error": str(e),
                },
            )
            raise StorageError(f"Failed to stream file: {e}") from e

    def get_file_size(self, bucket_name: str, object_name: str) -> int:
        """Get the size of a file in Cloud Storage.

        Args:
            bucket_name: Name of the GCS bucket
            object_name: Path to the object in the bucket

        Returns:
            File size in bytes

        Raises:
            StorageError: If operation fails
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_name)
            blob.reload()
            return blob.size
        except NotFound as e:
            logger.error(
                "File not found when checking size",
                extra={"bucket": bucket_name, "object_name": object_name},
            )
            raise StorageError(f"File not found: gs://{bucket_name}/{object_name}") from e
        except Exception as e:
            logger.error(
                "Failed to get file size",
                extra={
                    "bucket": bucket_name,
                    "object_name": object_name,
                    "error": str(e),
                },
            )
            raise StorageError(f"Failed to get file size: {e}") from e
