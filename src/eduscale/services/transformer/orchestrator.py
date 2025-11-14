"""Orchestrator for file transformation process."""

import logging
import tempfile
import time
from pathlib import Path
from typing import Any

from eduscale.core.config import settings
from eduscale.services.transformer.storage import StorageClient
from eduscale.services.transformer.exceptions import (
    FileTooLargeError,
    TransformationError,
    StorageError,
    ExtractionError,
    TranscriptionError,
)
from eduscale.services.transformer.handlers.text_handler import extract_text, build_text_frontmatter
from eduscale.services.transformer.handlers.audio_handler import transcribe_audio, build_audio_frontmatter

logger = logging.getLogger(__name__)


async def transform_file(
    file_id: str,
    bucket: str,
    object_name: str,
    content_type: str,
    file_category: str,
    region_id: str | None = None,
) -> dict[str, Any]:
    """Transform a file by extracting text and calling Tabular service.

    Args:
        file_id: Unique identifier for the file
        bucket: GCS bucket name
        object_name: Object path in the bucket
        content_type: MIME type of the file
        file_category: Category of the file (text, audio, image, archive, other)
        region_id: Optional region identifier

    Returns:
        Dictionary with transformation results and metadata

    Raises:
        FileTooLargeError: If file exceeds size limit
        TransformationError: If transformation fails
    """
    storage_client = StorageClient(project_id=settings.GCP_PROJECT_ID or None)
    temp_file_path: Path | None = None

    try:
        logger.info(
            "Starting file transformation",
            extra={
                "file_id": file_id,
                "bucket": bucket,
                "object_name": object_name,
                "content_type": content_type,
                "file_category": file_category,
                "region_id": region_id,
            },
        )

        # Check file size
        file_size_bytes = storage_client.get_file_size(bucket, object_name)
        max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

        if file_size_bytes > max_size_bytes:
            logger.warning(
                "File too large",
                extra={
                    "file_id": file_id,
                    "file_size_mb": file_size_bytes / (1024 * 1024),
                    "max_size_mb": settings.MAX_FILE_SIZE_MB,
                },
            )
            raise FileTooLargeError(
                f"File size {file_size_bytes / (1024 * 1024):.2f}MB exceeds limit "
                f"of {settings.MAX_FILE_SIZE_MB}MB"
            )

        # Download file to temporary location
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(object_name).suffix
        ) as temp_file:
            temp_file_path = Path(temp_file.name)

        logger.info(
            "Downloading file from GCS",
            extra={"file_id": file_id, "temp_path": str(temp_file_path)},
        )
        storage_client.download_file(bucket, object_name, temp_file_path)

        # Extract text based on file category
        extracted_text = ""
        metadata: dict[str, Any] = {}
        frontmatter = ""

        if file_category == "text":
            logger.info("Extracting text from document", extra={"file_id": file_id})
            start_time = time.time()
            try:
                extracted_text, extraction_meta = extract_text(temp_file_path, content_type)
                extraction_duration_ms = int((time.time() - start_time) * 1000)

                metadata = {
                    "extraction_method": extraction_meta.extraction_method,
                    "page_count": extraction_meta.page_count,
                    "sheet_count": extraction_meta.sheet_count,
                    "slide_count": extraction_meta.slide_count,
                    "word_count": extraction_meta.word_count,
                    "character_count": extraction_meta.character_count,
                }

                # Build frontmatter with metadata
                text_uri = f"gs://{bucket}/text/{file_id}.txt"
                frontmatter = build_text_frontmatter(
                    file_id=file_id,
                    region_id=region_id or "unknown",
                    text_uri=text_uri,
                    file_category=file_category,
                    extraction_metadata=extraction_meta,
                    original_filename=Path(object_name).name,
                    original_content_type=content_type,
                    original_size_bytes=file_size_bytes,
                    bucket=bucket,
                    object_path=object_name,
                    extraction_duration_ms=extraction_duration_ms,
                )

            except ExtractionError as e:
                logger.error(
                    "Text extraction failed",
                    extra={"file_id": file_id, "error": str(e)},
                )
                raise TransformationError(f"Text extraction failed: {e}") from e

        elif file_category == "audio":
            logger.info("Transcribing audio file", extra={"file_id": file_id})
            start_time = time.time()
            try:
                # Determine language (default to English, could be configurable)
                language_code = settings.SPEECH_LANGUAGE_EN

                # For long audio, we need the GCS URI
                gcs_uri = f"gs://{bucket}/{object_name}"

                extracted_text, audio_meta = transcribe_audio(
                    temp_file_path,
                    gcs_uri=gcs_uri,
                    language_code=language_code,
                )
                transcription_duration_ms = int((time.time() - start_time) * 1000)

                metadata = {
                    "extraction_method": "google-speech-to-text",
                    "duration_seconds": audio_meta.duration_seconds,
                    "sample_rate": audio_meta.sample_rate,
                    "channels": audio_meta.channels,
                    "confidence": audio_meta.confidence,
                    "language": audio_meta.language,
                }

                # Build frontmatter with metadata
                text_uri = f"gs://{bucket}/text/{file_id}.txt"
                frontmatter = build_audio_frontmatter(
                    file_id=file_id,
                    region_id=region_id or "unknown",
                    text_uri=text_uri,
                    file_category=file_category,
                    audio_metadata=audio_meta,
                    transcript_text=extracted_text,
                    original_filename=Path(object_name).name,
                    original_content_type=content_type,
                    original_size_bytes=file_size_bytes,
                    bucket=bucket,
                    object_path=object_name,
                    transcription_duration_ms=transcription_duration_ms,
                )

            except TranscriptionError as e:
                logger.error(
                    "Audio transcription failed",
                    extra={"file_id": file_id, "error": str(e)},
                )
                raise TransformationError(f"Audio transcription failed: {e}") from e

        elif file_category == "other":
            # Attempt text extraction for unknown types
            logger.info("Attempting text extraction for unknown type", extra={"file_id": file_id})
            start_time = time.time()
            try:
                extracted_text, extraction_meta = extract_text(temp_file_path, content_type)
                extraction_duration_ms = int((time.time() - start_time) * 1000)

                metadata = {
                    "extraction_method": extraction_meta.extraction_method,
                    "word_count": extraction_meta.word_count,
                }

                # Build frontmatter even for "other" category
                text_uri = f"gs://{bucket}/text/{file_id}.txt"
                frontmatter = build_text_frontmatter(
                    file_id=file_id,
                    region_id=region_id or "unknown",
                    text_uri=text_uri,
                    file_category=file_category,
                    extraction_metadata=extraction_meta,
                    original_filename=Path(object_name).name,
                    original_content_type=content_type,
                    original_size_bytes=file_size_bytes,
                    bucket=bucket,
                    object_path=object_name,
                    extraction_duration_ms=extraction_duration_ms,
                )

            except ExtractionError as e:
                logger.warning(
                    "Text extraction failed for unknown type",
                    extra={"file_id": file_id, "error": str(e)},
                )
                # For "other" category, we don't fail completely
                extracted_text = f"[Text extraction not supported for {content_type}]"
                frontmatter = ""
                metadata = {"extraction_method": "none"}

        else:
            logger.warning(
                "Unsupported file category",
                extra={"file_id": file_id, "file_category": file_category},
            )
            extracted_text = f"[Processing not implemented for category: {file_category}]"
            frontmatter = ""
            metadata = {"extraction_method": "none"}

        # Upload extracted text with frontmatter to Cloud Storage using streaming
        text_object_name = f"text/{file_id}.txt"

        def text_chunks_generator():
            """Generator that yields text chunks: frontmatter, separator, then extracted text."""
            if frontmatter:
                yield frontmatter
                yield "\n"  # Separator between frontmatter and text
            yield extracted_text

        logger.info(
            "Uploading extracted text with frontmatter to GCS (streaming)",
            extra={
                "file_id": file_id,
                "text_object_name": text_object_name,
                "has_frontmatter": bool(frontmatter),
                "extracted_text_length": len(extracted_text),
            },
        )

        text_uri = storage_client.upload_text_streaming(
            bucket, text_object_name, text_chunks_generator(), content_type="text/plain"
        )

        logger.info(
            "File transformation completed successfully",
            extra={
                "file_id": file_id,
                "text_uri": text_uri,
                "extracted_text_length": len(extracted_text),
            },
        )

        return {
            "file_id": file_id,
            "status": "transformed",
            "text_uri": text_uri,
            "extracted_text_length": len(extracted_text),
            "metadata": metadata,
        }

    except FileTooLargeError:
        # Re-raise without wrapping
        raise
    except StorageError as e:
        logger.error(
            "Storage operation failed",
            extra={"file_id": file_id, "error": str(e)},
        )
        raise TransformationError(f"Storage error: {e}") from e
    except Exception as e:
        logger.error(
            "Unexpected error during transformation",
            extra={"file_id": file_id, "error": str(e)},
            exc_info=True,
        )
        raise TransformationError(f"Transformation failed: {e}") from e
    finally:
        # Clean up temporary file
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
                logger.debug("Temporary file cleaned up", extra={"temp_path": str(temp_file_path)})
            except Exception as e:
                logger.warning(
                    "Failed to clean up temporary file",
                    extra={"temp_path": str(temp_file_path), "error": str(e)},
                )
