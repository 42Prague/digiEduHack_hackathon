"""Orchestrator for file transformation process."""

import logging
import tempfile
import time
from pathlib import Path
from typing import Any

from eduscale.core.config import settings
from eduscale.services.transformer.storage import StorageClient
from eduscale.services.transformer.exceptions import (
    TransformationError,
    StorageError,
    ExtractionError,
    TranscriptionError,
)
from eduscale.services.transformer.handlers.text_handler import (
    extract_text_from_plain,
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_doc,
    extract_text_from_xlsx,
    extract_text_from_odt,
    extract_text_from_ods,
    extract_text_from_odp,
    build_text_frontmatter,
)
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

        # Get file size for metadata
        file_size_bytes = storage_client.get_file_size(bucket, object_name)

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
            # Plain text files - just read as-is
            logger.info("Reading plain text file", extra={"file_id": file_id})
            start_time = time.time()
            try:
                extracted_text, extraction_meta = extract_text_from_plain(temp_file_path)
                extraction_duration_ms = int((time.time() - start_time) * 1000)

                metadata = {
                    "extraction_method": extraction_meta.extraction_method,
                    "word_count": extraction_meta.word_count,
                    "character_count": extraction_meta.character_count,
                }

                text_uri = f"gs://{bucket}/text/{file_id}.txt"
                frontmatter = build_text_frontmatter(
                    file_id=file_id,
                    region_id=region_id or "unknown",
                    text_uri=text_uri,
                    file_category=file_category,
                    extraction_metadata=extraction_meta,
                    original_filename=object_name,
                    original_content_type=content_type,
                    original_size_bytes=file_size_bytes,
                    bucket=bucket,
                    object_path=object_name,
                    extraction_duration_ms=extraction_duration_ms,
                )

            except ExtractionError as e:
                logger.error(
                    "Plain text extraction failed, skipping file",
                    extra={"file_id": file_id, "error": str(e), "file_category": file_category},
                )
                return {
                    "file_id": file_id,
                    "status": "skipped",
                    "reason": f"Extraction failed: {str(e)}",
                    "metadata": {"extraction_method": "none", "file_category": file_category},
                }

        elif file_category == "pdf":
            # PDF files
            logger.info("Extracting text from PDF", extra={"file_id": file_id})
            start_time = time.time()
            try:
                extracted_text, extraction_meta = extract_text_from_pdf(temp_file_path)
                extraction_duration_ms = int((time.time() - start_time) * 1000)

                metadata = {
                    "extraction_method": extraction_meta.extraction_method,
                    "page_count": extraction_meta.page_count,
                    "word_count": extraction_meta.word_count,
                    "character_count": extraction_meta.character_count,
                }

                text_uri = f"gs://{bucket}/text/{file_id}.txt"
                frontmatter = build_text_frontmatter(
                    file_id=file_id,
                    region_id=region_id or "unknown",
                    text_uri=text_uri,
                    file_category=file_category,
                    extraction_metadata=extraction_meta,
                    original_filename=object_name,
                    original_content_type=content_type,
                    original_size_bytes=file_size_bytes,
                    bucket=bucket,
                    object_path=object_name,
                    extraction_duration_ms=extraction_duration_ms,
                )

            except ExtractionError as e:
                logger.error(
                    "PDF extraction failed, skipping file",
                    extra={"file_id": file_id, "error": str(e), "file_category": file_category},
                )
                return {
                    "file_id": file_id,
                    "status": "skipped",
                    "reason": f"Extraction failed: {str(e)}",
                    "metadata": {"extraction_method": "none", "file_category": file_category},
                }

        elif file_category == "docx":
            # Word documents (.docx or .doc)
            logger.info("Extracting text from Word document", extra={"file_id": file_id, "content_type": content_type})
            start_time = time.time()
            try:
                if content_type == "application/msword":
                    extracted_text, extraction_meta = extract_text_from_doc(temp_file_path)
                else:
                    extracted_text, extraction_meta = extract_text_from_docx(temp_file_path)
                extraction_duration_ms = int((time.time() - start_time) * 1000)

                metadata = {
                    "extraction_method": extraction_meta.extraction_method,
                    "word_count": extraction_meta.word_count,
                    "character_count": extraction_meta.character_count,
                }

                text_uri = f"gs://{bucket}/text/{file_id}.txt"
                frontmatter = build_text_frontmatter(
                    file_id=file_id,
                    region_id=region_id or "unknown",
                    text_uri=text_uri,
                    file_category=file_category,
                    extraction_metadata=extraction_meta,
                    original_filename=object_name,
                    original_content_type=content_type,
                    original_size_bytes=file_size_bytes,
                    bucket=bucket,
                    object_path=object_name,
                    extraction_duration_ms=extraction_duration_ms,
                )

            except ExtractionError as e:
                logger.error(
                    "Word document extraction failed, skipping file",
                    extra={"file_id": file_id, "error": str(e), "file_category": file_category},
                )
                return {
                    "file_id": file_id,
                    "status": "skipped",
                    "reason": f"Extraction failed: {str(e)}",
                    "metadata": {"extraction_method": "none", "file_category": file_category},
                }

        elif file_category == "excel":
            # Excel spreadsheets
            logger.info("Extracting text from Excel", extra={"file_id": file_id})
            start_time = time.time()
            try:
                extracted_text, extraction_meta = extract_text_from_xlsx(temp_file_path)
                extraction_duration_ms = int((time.time() - start_time) * 1000)

                metadata = {
                    "extraction_method": extraction_meta.extraction_method,
                    "sheet_count": extraction_meta.sheet_count,
                    "word_count": extraction_meta.word_count,
                    "character_count": extraction_meta.character_count,
                }

                text_uri = f"gs://{bucket}/text/{file_id}.txt"
                frontmatter = build_text_frontmatter(
                    file_id=file_id,
                    region_id=region_id or "unknown",
                    text_uri=text_uri,
                    file_category=file_category,
                    extraction_metadata=extraction_meta,
                    original_filename=object_name,
                    original_content_type=content_type,
                    original_size_bytes=file_size_bytes,
                    bucket=bucket,
                    object_path=object_name,
                    extraction_duration_ms=extraction_duration_ms,
                )

            except ExtractionError as e:
                logger.error(
                    "Excel extraction failed, skipping file",
                    extra={"file_id": file_id, "error": str(e), "file_category": file_category},
                )
                return {
                    "file_id": file_id,
                    "status": "skipped",
                    "reason": f"Extraction failed: {str(e)}",
                    "metadata": {"extraction_method": "none", "file_category": file_category},
                }

        elif file_category == "odf":
            # OpenDocument formats
            logger.info("Extracting text from ODF", extra={"file_id": file_id, "content_type": content_type})
            start_time = time.time()
            try:
                # Route based on ODF content type
                if content_type == "application/vnd.oasis.opendocument.text":
                    extracted_text, extraction_meta = extract_text_from_odt(temp_file_path)
                elif content_type == "application/vnd.oasis.opendocument.spreadsheet":
                    extracted_text, extraction_meta = extract_text_from_ods(temp_file_path)
                elif content_type == "application/vnd.oasis.opendocument.presentation":
                    extracted_text, extraction_meta = extract_text_from_odp(temp_file_path)
                else:
                    # Unknown ODF type - treat as "other"
                    logger.warning(
                        "Unknown ODF content type, treating as 'other'",
                        extra={"file_id": file_id, "content_type": content_type},
                    )
                    return {
                        "file_id": file_id,
                        "status": "skipped",
                        "reason": f"Unknown ODF content type: {content_type}",
                        "metadata": {"extraction_method": "none", "file_category": file_category},
                    }

                extraction_duration_ms = int((time.time() - start_time) * 1000)

                metadata = {
                    "extraction_method": extraction_meta.extraction_method,
                    "page_count": extraction_meta.page_count,
                    "sheet_count": extraction_meta.sheet_count,
                    "slide_count": extraction_meta.slide_count,
                    "word_count": extraction_meta.word_count,
                    "character_count": extraction_meta.character_count,
                }

                text_uri = f"gs://{bucket}/text/{file_id}.txt"
                frontmatter = build_text_frontmatter(
                    file_id=file_id,
                    region_id=region_id or "unknown",
                    text_uri=text_uri,
                    file_category=file_category,
                    extraction_metadata=extraction_meta,
                    original_filename=object_name,
                    original_content_type=content_type,
                    original_size_bytes=file_size_bytes,
                    bucket=bucket,
                    object_path=object_name,
                    extraction_duration_ms=extraction_duration_ms,
                )

            except ExtractionError as e:
                logger.error(
                    "ODF extraction failed, skipping file",
                    extra={"file_id": file_id, "error": str(e), "file_category": file_category},
                )
                return {
                    "file_id": file_id,
                    "status": "skipped",
                    "reason": f"Extraction failed: {str(e)}",
                    "metadata": {"extraction_method": "none", "file_category": file_category},
                }

        elif file_category == "audio":
            logger.info("Transcribing audio file", extra={"file_id": file_id})
            start_time = time.time()
            try:
                # Determine language (default to English, could be configurable)
                language_code = settings.SPEECH_LANGUAGE_EN

                extracted_text, audio_meta = transcribe_audio(
                    temp_file_path,
                    language_code=language_code,
                    storage_client=storage_client,
                    bucket=bucket,
                    file_id=file_id,
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
                    original_filename=object_name,
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
            # For "other" category, just log warning and return success without processing
            logger.warning(
                "File category is 'other', skipping text extraction and upload",
                extra={
                    "file_id": file_id,
                    "content_type": content_type,
                    "bucket": bucket,
                    "object_name": object_name,
                },
            )

            # Return success response without uploading anything
            return {
                "file_id": file_id,
                "status": "skipped",
                "reason": "File category 'other' - no text extraction performed",
                "metadata": {"extraction_method": "none", "file_category": file_category},
            }

        else:
            # Unknown category - treat as "other"
            logger.warning(
                "Unknown file category, treating as 'other'",
                extra={
                    "file_id": file_id,
                    "file_category": file_category,
                    "content_type": content_type,
                },
            )

            # Return success response without uploading anything
            return {
                "file_id": file_id,
                "status": "skipped",
                "reason": f"Unknown file category '{file_category}' - no processing performed",
                "metadata": {"extraction_method": "none", "file_category": file_category},
            }

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
