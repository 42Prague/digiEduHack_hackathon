"""Audio transcription handler using Google Cloud Speech-to-Text with ffmpeg."""

import asyncio
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

import yaml
from google.cloud import speech_v1 as speech

from eduscale.services.transformer.exceptions import TranscriptionError

logger = logging.getLogger(__name__)


class AudioMetadata(NamedTuple):
    """Metadata about audio file and transcription."""
    duration_seconds: float | None = None
    sample_rate: int | None = None
    channels: int | None = None
    format: str | None = None
    confidence: float | None = None
    language: str | None = None


def build_audio_frontmatter(
    file_id: str,
    region_id: str,
    text_uri: str,
    file_category: str,
    audio_metadata: AudioMetadata,
    transcript_text: str,
    original_filename: str | None = None,
    original_content_type: str | None = None,
    original_size_bytes: int | None = None,
    bucket: str | None = None,
    object_path: str | None = None,
    event_id: str | None = None,
    uploaded_at: str | None = None,
    transcription_duration_ms: int | None = None,
) -> str:
    """Build YAML frontmatter with metadata for AI processing of audio transcriptions.

    Args:
        file_id: Unique file identifier
        region_id: Region identifier
        text_uri: GCS URI of the transcription text file
        file_category: File category (should be 'audio')
        audio_metadata: Metadata from the transcription process
        transcript_text: The transcribed text (for calculating word count)
        original_filename: Original filename
        original_content_type: Original MIME type
        original_size_bytes: Original file size in bytes
        bucket: GCS bucket name
        object_path: Full object path in GCS
        event_id: CloudEvent ID for tracing
        uploaded_at: Upload timestamp (ISO format)
        transcription_duration_ms: Time taken for transcription in milliseconds

    Returns:
        YAML frontmatter string with metadata
    """
    # Build metadata dictionary
    metadata = {
        "file_id": file_id,
        "region_id": region_id,
        "text_uri": text_uri,
    }

    # Add event ID if available
    if event_id:
        metadata["event_id"] = event_id

    # Add original file information
    original = {}
    if original_filename:
        original["filename"] = original_filename
    if original_content_type:
        original["content_type"] = original_content_type
    if original_size_bytes is not None:
        original["size_bytes"] = original_size_bytes
    if bucket:
        original["bucket"] = bucket
    if object_path:
        original["object_path"] = object_path
    if uploaded_at:
        original["uploaded_at"] = uploaded_at

    if original:
        metadata["original"] = original

    # Add file category
    metadata["file_category"] = file_category

    # Add extraction information
    extraction = {
        "method": "google-speech-to-text",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "success": True,
    }
    if transcription_duration_ms is not None:
        extraction["duration_ms"] = transcription_duration_ms

    metadata["extraction"] = extraction

    # Add content metrics
    word_count = len(transcript_text.split())
    content = {
        "text_length": len(transcript_text),
        "word_count": word_count,
        "character_count": len(transcript_text),
    }
    metadata["content"] = content

    # Add audio-specific metadata
    audio = {}
    if audio_metadata.duration_seconds is not None:
        audio["duration_seconds"] = audio_metadata.duration_seconds
    if audio_metadata.sample_rate is not None:
        audio["sample_rate"] = audio_metadata.sample_rate
    if audio_metadata.channels is not None:
        audio["channels"] = audio_metadata.channels
    if audio_metadata.confidence is not None:
        audio["confidence"] = audio_metadata.confidence
    if audio_metadata.language is not None:
        audio["language"] = audio_metadata.language

    if audio:
        metadata["audio"] = audio

    # Convert to YAML with proper formatting
    yaml_content = yaml.dump(
        metadata,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )

    # Return with frontmatter delimiters
    return f"---\n{yaml_content}---\n"


def get_audio_metadata(file_path: Path) -> AudioMetadata:
    """Extract metadata from audio file using ffprobe.

    Args:
        file_path: Path to the audio file

    Returns:
        Audio metadata

    Raises:
        TranscriptionError: If metadata extraction fails
    """
    try:
        logger.info("Extracting audio metadata with ffprobe", extra={"file_path": str(file_path)})

        # Run ffprobe to get audio metadata in JSON format
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            raise TranscriptionError(f"ffprobe failed: {result.stderr}")

        # Parse JSON output
        probe_data = json.loads(result.stdout)

        # Extract audio stream information
        audio_stream = None
        for stream in probe_data.get("streams", []):
            if stream.get("codec_type") == "audio":
                audio_stream = stream
                break

        if not audio_stream:
            raise TranscriptionError("No audio stream found in file")

        # Extract metadata
        duration = float(probe_data.get("format", {}).get("duration", 0))
        sample_rate = int(audio_stream.get("sample_rate", 0))
        channels = int(audio_stream.get("channels", 0))
        codec_name = audio_stream.get("codec_name", "unknown").upper()

        metadata = AudioMetadata(
            duration_seconds=duration if duration > 0 else None,
            sample_rate=sample_rate if sample_rate > 0 else None,
            channels=channels if channels > 0 else None,
            format=codec_name,
        )

        logger.info(
            "Audio metadata extracted",
            extra={
                "file_path": str(file_path),
                "duration": duration,
                "sample_rate": sample_rate,
                "channels": channels,
                "codec": codec_name,
            },
        )

        return metadata
    except subprocess.TimeoutExpired:
        logger.error("ffprobe timeout", extra={"file_path": str(file_path)})
        raise TranscriptionError("Metadata extraction timed out")
    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse ffprobe output",
            extra={"file_path": str(file_path), "error": str(e)},
        )
        raise TranscriptionError(f"Failed to parse audio metadata: {e}") from e
    except Exception as e:
        logger.error(
            "Failed to extract audio metadata",
            extra={"file_path": str(file_path), "error": str(e)},
        )
        raise TranscriptionError(f"Metadata extraction failed: {e}") from e


def convert_to_linear16(file_path: Path, output_path: Path) -> tuple[int, int]:
    """Convert audio to LINEAR16 format required by Google Speech API using ffmpeg.

    Args:
        file_path: Path to the input audio file
        output_path: Path to save the converted WAV file

    Returns:
        Tuple of (sample_rate, channels) = (16000, 1)

    Raises:
        TranscriptionError: If conversion fails
    """
    try:
        logger.info(
            "Converting audio to LINEAR16 with ffmpeg",
            extra={"input": str(file_path), "output": str(output_path)},
        )

        # ffmpeg command to convert to LINEAR16 WAV
        cmd = [
            "ffmpeg",
            "-i", str(file_path),       # Input file
            "-acodec", "pcm_s16le",     # LINEAR16 codec (16-bit PCM little-endian)
            "-ar", "16000",             # Sample rate: 16 kHz
            "-ac", "1",                 # Channels: mono (1 channel)
            "-f", "wav",                # Output format: WAV
            "-y",                       # Overwrite output file without asking
            str(output_path),           # Output file
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minutes timeout for conversion
        )

        if result.returncode != 0:
            # Extract meaningful error from ffmpeg stderr
            error_msg = result.stderr.strip().split('\n')[-1] if result.stderr else "Unknown error"
            logger.error(
                "ffmpeg conversion failed",
                extra={
                    "input": str(file_path),
                    "output": str(output_path),
                    "error": error_msg,
                    "returncode": result.returncode,
                },
            )
            raise TranscriptionError(f"Audio conversion failed: {error_msg}")

        # Verify output file was created
        if not output_path.exists():
            raise TranscriptionError("Output file was not created")

        logger.info(
            "Audio converted successfully",
            extra={
                "input": str(file_path),
                "output": str(output_path),
                "sample_rate": 16000,
                "channels": 1,
                "size_bytes": output_path.stat().st_size,
            },
        )

        return 16000, 1

    except subprocess.TimeoutExpired:
        logger.error(
            "ffmpeg conversion timeout",
            extra={"file_path": str(file_path), "timeout": 120},
        )
        raise TranscriptionError("Audio conversion timed out after 120 seconds")
    except Exception as e:
        logger.error(
            "Failed to convert audio",
            extra={"file_path": str(file_path), "error": str(e)},
        )
        raise TranscriptionError(f"Audio conversion failed: {e}") from e


def split_audio_into_chunks(
    file_path: Path,
    chunk_duration: int = 50,
    overlap: float = 1.0,
) -> list[tuple[Path, float]]:
    """Split audio file into chunks with overlap using ffmpeg.

    Args:
        file_path: Path to the audio file (LINEAR16 WAV format)
        chunk_duration: Duration of each chunk in seconds (default: 50)
        overlap: Overlap between chunks in seconds (default: 1.0)

    Returns:
        List of (chunk_path, start_offset_seconds) tuples

    Raises:
        TranscriptionError: If splitting fails
    """
    try:
        logger.info(
            "Splitting audio into chunks",
            extra={
                "file_path": str(file_path),
                "chunk_duration": chunk_duration,
                "overlap": overlap,
            },
        )

        # Get audio duration using ffprobe
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(file_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise TranscriptionError(f"ffprobe failed: {result.stderr}")

        probe_data = json.loads(result.stdout)
        total_duration = float(probe_data.get("format", {}).get("duration", 0))

        if total_duration == 0:
            raise TranscriptionError("Could not determine audio duration")

        logger.info(
            "Audio duration determined",
            extra={"file_path": str(file_path), "duration": total_duration},
        )

        # Calculate chunk parameters
        step = chunk_duration - overlap  # How much to advance for each chunk
        chunks = []
        chunk_index = 0

        # Create temporary directory for chunks
        import tempfile
        temp_dir = Path(tempfile.mkdtemp(prefix="audio_chunks_"))

        try:
            start_time = 0.0
            while start_time < total_duration:
                chunk_index += 1
                chunk_path = temp_dir / f"chunk_{chunk_index:04d}.wav"

                # Calculate actual duration for this chunk
                actual_duration = min(chunk_duration, total_duration - start_time)

                # Use ffmpeg to extract chunk
                cmd = [
                    "ffmpeg",
                    "-ss", str(start_time),  # Start time (before -i for fast seeking)
                    "-i", str(file_path),
                    "-t", str(actual_duration),  # Duration
                    "-acodec", "pcm_s16le",  # Re-encode to ensure accurate splitting
                    "-ar", "16000",  # Keep sample rate
                    "-ac", "1",  # Keep mono
                    "-y",  # Overwrite output file
                    str(chunk_path),
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode != 0:
                    error_msg = result.stderr.strip().split('\n')[-1] if result.stderr else "Unknown error"
                    raise TranscriptionError(f"ffmpeg chunk extraction failed: {error_msg}")

                if not chunk_path.exists():
                    raise TranscriptionError(f"Chunk file was not created: {chunk_path}")

                chunks.append((chunk_path, start_time))

                logger.debug(
                    "Chunk created",
                    extra={
                        "chunk_index": chunk_index,
                        "start_time": start_time,
                        "duration": actual_duration,
                        "path": str(chunk_path),
                    },
                )

                # Move to next chunk (with overlap)
                start_time += step

                # If this is the last possible chunk, break
                if start_time >= total_duration:
                    break

            logger.info(
                "Audio split into chunks successfully",
                extra={
                    "file_path": str(file_path),
                    "total_chunks": len(chunks),
                    "temp_dir": str(temp_dir),
                },
            )

            return chunks

        except Exception:
            # Clean up temp directory on error
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise

    except subprocess.TimeoutExpired:
        logger.error("Audio splitting timeout", extra={"file_path": str(file_path)})
        raise TranscriptionError("Audio splitting timed out")
    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse ffprobe output",
            extra={"file_path": str(file_path), "error": str(e)},
        )
        raise TranscriptionError(f"Failed to parse audio metadata: {e}") from e
    except Exception as e:
        logger.error(
            "Failed to split audio",
            extra={"file_path": str(file_path), "error": str(e)},
        )
        raise TranscriptionError(f"Audio splitting failed: {e}") from e


def upload_chunks_to_gcs(
    storage_client,
    bucket: str,
    file_id: str,
    chunks: list[tuple[Path, float]],
) -> list[tuple[str, float]]:
    """Upload audio chunks to GCS.

    Args:
        storage_client: StorageClient instance
        bucket: GCS bucket name
        file_id: File identifier
        chunks: List of (chunk_path, start_offset) tuples

    Returns:
        List of (gcs_uri, start_offset) tuples

    Raises:
        TranscriptionError: If upload fails
    """
    try:
        logger.info(
            "Uploading chunks to GCS",
            extra={
                "bucket": bucket,
                "file_id": file_id,
                "total_chunks": len(chunks),
            },
        )

        uploaded_chunks = []
        for idx, (chunk_path, start_offset) in enumerate(chunks, start=1):
            # Build GCS path: audio-chunks/{file_id}/chunk_XXXX.wav
            chunk_filename = chunk_path.name
            object_name = f"audio-chunks/{file_id}/{chunk_filename}"

            # Upload using blob.upload_from_filename
            gcs_bucket = storage_client.client.bucket(bucket)
            blob = gcs_bucket.blob(object_name)
            blob.content_type = "audio/wav"
            blob.upload_from_filename(str(chunk_path))

            gcs_uri = f"gs://{bucket}/{object_name}"
            uploaded_chunks.append((gcs_uri, start_offset))

            logger.debug(
                "Chunk uploaded",
                extra={
                    "chunk_index": idx,
                    "gcs_uri": gcs_uri,
                    "start_offset": start_offset,
                    "size_bytes": chunk_path.stat().st_size,
                },
            )

        logger.info(
            "All chunks uploaded successfully",
            extra={
                "bucket": bucket,
                "file_id": file_id,
                "total_chunks": len(uploaded_chunks),
            },
        )

        return uploaded_chunks

    except Exception as e:
        logger.error(
            "Failed to upload chunks to GCS",
            extra={
                "bucket": bucket,
                "file_id": file_id,
                "error": str(e),
            },
        )
        raise TranscriptionError(f"Failed to upload chunks: {e}") from e


def cleanup_gcs_chunks(storage_client, bucket: str, file_id: str) -> None:
    """Clean up temporary audio chunks from GCS.

    Args:
        storage_client: StorageClient instance
        bucket: GCS bucket name
        file_id: File identifier

    Raises:
        TranscriptionError: If cleanup fails (logged but not raised)
    """
    try:
        logger.info(
            "Cleaning up GCS chunks",
            extra={"bucket": bucket, "file_id": file_id},
        )

        # List and delete all blobs in audio-chunks/{file_id}/
        prefix = f"audio-chunks/{file_id}/"
        gcs_bucket = storage_client.client.bucket(bucket)
        blobs = gcs_bucket.list_blobs(prefix=prefix)

        deleted_count = 0
        for blob in blobs:
            blob.delete()
            deleted_count += 1
            logger.debug(
                "Chunk deleted from GCS",
                extra={"blob_name": blob.name},
            )

        logger.info(
            "GCS chunks cleaned up successfully",
            extra={
                "bucket": bucket,
                "file_id": file_id,
                "deleted_count": deleted_count,
            },
        )

    except Exception as e:
        # Log error but don't raise - cleanup is best effort
        logger.warning(
            "Failed to cleanup GCS chunks",
            extra={
                "bucket": bucket,
                "file_id": file_id,
                "error": str(e),
            },
        )


def transcribe_audio_short(
    audio_path: Path, language_code: str = "en-US"
) -> tuple[str, float]:
    """Transcribe short audio file (< 60 seconds) using synchronous recognition.

    Args:
        audio_path: Path to the audio file (LINEAR16 WAV format)
        language_code: Language code (e.g., 'en-US', 'cs-CZ')

    Returns:
        Tuple of (transcript, confidence)

    Raises:
        TranscriptionError: If transcription fails
    """
    try:
        logger.info(
            "Transcribing short audio",
            extra={"file_path": str(audio_path), "language": language_code},
        )

        client = speech.SpeechClient()

        with open(audio_path, "rb") as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language_code,
            enable_automatic_punctuation=True,
        )

        response = client.recognize(config=config, audio=audio)

        if not response.results:
            logger.warning("No transcription results", extra={"file_path": str(audio_path)})
            return "", 0.0

        # Combine all results
        transcripts = []
        confidences = []

        for result in response.results:
            alternative = result.alternatives[0]
            transcripts.append(alternative.transcript)
            confidences.append(alternative.confidence)

        transcript = " ".join(transcripts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        logger.info(
            "Short audio transcription successful",
            extra={
                "file_path": str(audio_path),
                "transcript_length": len(transcript),
                "confidence": avg_confidence,
            },
        )

        return transcript, avg_confidence
    except Exception as e:
        logger.error(
            "Failed to transcribe short audio",
            extra={"file_path": str(audio_path), "error": str(e)},
        )
        raise TranscriptionError(f"Short audio transcription failed: {e}") from e


async def transcribe_audio_chunk_async(
    chunk_path: Path, language_code: str = "en-US"
) -> tuple[str, float]:
    """Transcribe audio chunk asynchronously using Google Speech API synchronous recognition.

    Args:
        chunk_path: Path to the local audio chunk file (LINEAR16 WAV format, <= 50 seconds)
        language_code: Language code (e.g., 'en-US', 'cs-CZ')

    Returns:
        Tuple of (transcript, confidence)

    Raises:
        TranscriptionError: If transcription fails
    """
    try:
        logger.debug(
            "Transcribing chunk asynchronously from local file",
            extra={"chunk_path": str(chunk_path), "language": language_code},
        )

        # Run synchronous API call in executor to avoid blocking
        loop = asyncio.get_event_loop()

        def _transcribe():
            client = speech.SpeechClient()

            # Read audio content from local file
            with open(chunk_path, "rb") as audio_file:
                content = audio_file.read()

            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language_code,
                enable_automatic_punctuation=True,
            )

            # Use synchronous recognize for short chunks (<= 60 seconds)
            response = client.recognize(config=config, audio=audio)

            if not response.results:
                return "", 0.0

            transcripts = []
            confidences = []
            for result in response.results:
                alternative = result.alternatives[0]
                transcripts.append(alternative.transcript)
                confidences.append(alternative.confidence)

            transcript = " ".join(transcripts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            return transcript, avg_confidence

        transcript, confidence = await loop.run_in_executor(None, _transcribe)

        logger.debug(
            "Chunk transcription successful",
            extra={
                "chunk_path": str(chunk_path),
                "transcript_length": len(transcript),
                "confidence": confidence,
            },
        )

        return transcript, confidence

    except Exception as e:
        logger.error(
            "Failed to transcribe chunk",
            extra={"chunk_path": str(chunk_path), "error": str(e)},
        )
        raise TranscriptionError(f"Chunk transcription failed: {e}") from e


async def process_chunks_parallel(
    chunks: list[tuple[Path, float]], language_code: str = "en-US"
) -> list[tuple[str, float, float]]:
    """Process multiple audio chunks in parallel using asyncio.

    Args:
        chunks: List of (chunk_path, start_offset) tuples
        language_code: Language code for transcription

    Returns:
        List of (transcript, confidence, start_offset) tuples

    Raises:
        TranscriptionError: If any chunk transcription fails
    """
    try:
        logger.info(
            "Processing chunks in parallel",
            extra={"total_chunks": len(chunks), "language": language_code},
        )

        # Create tasks for all chunks with their offsets
        tasks_with_offsets = [
            (transcribe_audio_chunk_async(chunk_path, language_code), start_offset, idx)
            for idx, (chunk_path, start_offset) in enumerate(chunks, start=1)
        ]

        # Execute all tasks in parallel using asyncio.gather
        tasks = [task for task, _, _ in tasks_with_offsets]

        try:
            # Wait for all tasks to complete in parallel
            transcription_results = await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(
                "One or more chunk transcriptions failed",
                extra={"error": str(e)},
            )
            raise TranscriptionError(f"Parallel transcription failed: {e}") from e

        # Build results list with offsets
        results = []
        for idx, ((transcript, confidence), (_, start_offset, chunk_idx)) in enumerate(
            zip(transcription_results, tasks_with_offsets), start=1
        ):
            results.append((transcript, confidence, start_offset))
            logger.info(
                f"Chunk {chunk_idx}/{len(tasks)} processed successfully",
                extra={
                    "chunk_index": chunk_idx,
                    "start_offset": start_offset,
                    "transcript_length": len(transcript),
                },
            )

        logger.info(
            "All chunks processed successfully",
            extra={"total_chunks": len(results)},
        )

        return results

    except TranscriptionError:
        # Re-raise TranscriptionError as-is
        raise
    except Exception as e:
        logger.error(
            "Failed to process chunks in parallel",
            extra={"error": str(e)},
        )
        raise TranscriptionError(f"Parallel processing failed: {e}") from e


def merge_transcription_results(
    results: list[tuple[str, float, float]], overlap: float = 1.0
) -> tuple[str, float]:
    """Merge transcription results from overlapping chunks.

    Removes duplicate words at chunk boundaries based on overlap zone.

    Args:
        results: List of (transcript, confidence, start_offset) tuples
        overlap: Overlap duration in seconds between chunks

    Returns:
        Tuple of (merged_transcript, average_confidence)
    """
    try:
        logger.info(
            "Merging transcription results",
            extra={"total_chunks": len(results), "overlap": overlap},
        )

        if not results:
            return "", 0.0

        if len(results) == 1:
            return results[0][0], results[0][1]

        # Sort results by start offset
        sorted_results = sorted(results, key=lambda x: x[2])

        merged_text = ""
        total_confidence = 0.0
        duplicates_removed = 0

        for idx, (transcript, confidence, start_offset) in enumerate(sorted_results):
            total_confidence += confidence

            if idx == 0:
                # First chunk: add everything
                merged_text = transcript
            else:
                # For subsequent chunks, try to remove duplicates at the boundary
                words_current = transcript.split()
                words_previous = merged_text.split()

                if not words_current:
                    continue

                # Find overlap: compare last N words of previous with first N words of current
                # N = approximately 3-5 words (heuristic for 1 second overlap)
                max_overlap_words = min(5, len(words_previous), len(words_current))

                # Try to find matching words
                best_match_len = 0
                for n in range(max_overlap_words, 0, -1):
                    last_n_words = words_previous[-n:]
                    first_n_words = words_current[:n]

                    if last_n_words == first_n_words:
                        best_match_len = n
                        break

                if best_match_len > 0:
                    # Remove duplicate words from current chunk
                    words_to_add = words_current[best_match_len:]
                    duplicates_removed += best_match_len
                    logger.debug(
                        f"Removed {best_match_len} duplicate words at chunk {idx} boundary",
                        extra={
                            "chunk_index": idx,
                            "duplicates": best_match_len,
                            "words_removed": words_current[:best_match_len],
                        },
                    )
                else:
                    # No duplicates found, add all words
                    words_to_add = words_current

                if words_to_add:
                    merged_text += " " + " ".join(words_to_add)

        avg_confidence = total_confidence / len(sorted_results) if sorted_results else 0.0

        logger.info(
            "Transcription results merged successfully",
            extra={
                "total_chunks": len(results),
                "merged_length": len(merged_text),
                "avg_confidence": avg_confidence,
                "duplicates_removed": duplicates_removed,
            },
        )

        return merged_text.strip(), avg_confidence

    except Exception as e:
        logger.error(
            "Failed to merge transcription results",
            extra={"error": str(e)},
        )
        raise TranscriptionError(f"Failed to merge results: {e}") from e


async def transcribe_audio(
    file_path: Path,
    language_code: str = "en-US",
    storage_client=None,
    bucket: str | None = None,
    file_id: str | None = None,
) -> tuple[str, AudioMetadata]:
    """Transcribe audio file, automatically choosing short or chunked recognition.

    For audio files longer than 50 seconds, splits into chunks,
    processes in parallel from local files, and merges results.

    Args:
        file_path: Path to the audio file
        language_code: Language code (e.g., 'en-US', 'cs-CZ')
        storage_client: Deprecated, no longer used
        bucket: Deprecated, no longer used
        file_id: Deprecated, no longer used

    Returns:
        Tuple of (transcript, metadata)

    Raises:
        TranscriptionError: If transcription fails
    """
    import time
    import shutil

    converted_path = None
    chunks_temp_dir = None

    try:
        start_time = time.time()
        logger.info(
            "Starting audio transcription",
            extra={"file_path": str(file_path), "language": language_code},
        )

        # Get audio metadata from original file
        metadata = get_audio_metadata(file_path)

        # Convert to LINEAR16 WAV for Google Speech API
        converted_path = file_path.with_suffix(".converted.wav")
        sample_rate, channels = convert_to_linear16(file_path, converted_path)

        try:
            # Choose transcription method based on duration
            if metadata.duration_seconds and metadata.duration_seconds > 50:
                # Long audio: split into chunks and process in parallel
                logger.info(
                    "Audio is longer than 50 seconds, using chunked processing",
                    extra={"duration": metadata.duration_seconds},
                )

                # 1. Split audio into chunks
                chunks = split_audio_into_chunks(converted_path, chunk_duration=50, overlap=1.0)
                chunks_temp_dir = chunks[0][0].parent if chunks else None

                logger.info(
                    f"Audio split into {len(chunks)} chunks",
                    extra={"total_chunks": len(chunks)},
                )

                # 2. Process chunks in parallel using asyncio from local files
                results = await process_chunks_parallel(chunks, language_code)

                logger.info(
                    "All chunks transcribed",
                    extra={"total_results": len(results)},
                )

                # 3. Merge transcription results
                transcript, confidence = merge_transcription_results(results, overlap=1.0)

                logger.info(
                    "Transcription results merged",
                    extra={
                        "merged_length": len(transcript),
                        "confidence": confidence,
                    },
                )

            else:
                # Short audio: use synchronous recognition with converted file
                logger.info(
                    "Audio is short (<= 50 seconds), using direct recognition",
                    extra={"duration": metadata.duration_seconds},
                )
                transcript, confidence = transcribe_audio_short(converted_path, language_code)

            # Update metadata with transcription info
            metadata = metadata._replace(
                confidence=confidence,
                language=language_code,
                sample_rate=sample_rate,
                channels=channels,
            )

            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(
                "Audio transcription completed",
                extra={
                    "file_path": str(file_path),
                    "transcript_length": len(transcript),
                    "confidence": confidence,
                    "duration_ms": duration_ms,
                },
            )

            return transcript, metadata

        finally:
            # Clean up converted file
            if converted_path and converted_path.exists():
                converted_path.unlink()
                logger.debug("Cleaned up converted file", extra={"path": str(converted_path)})

            # Clean up local chunks temp directory
            if chunks_temp_dir and chunks_temp_dir.exists():
                shutil.rmtree(chunks_temp_dir)
                logger.debug("Cleaned up chunks temp directory", extra={"path": str(chunks_temp_dir)})

    except TranscriptionError:
        # Re-raise TranscriptionError as-is
        raise
    except Exception as e:
        logger.error(
            "Failed to transcribe audio",
            extra={"file_path": str(file_path), "error": str(e)},
        )
        raise TranscriptionError(f"Audio transcription failed: {e}") from e
