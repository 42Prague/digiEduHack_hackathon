"""Audio transcription handler using Google Cloud Speech-to-Text with ffmpeg."""

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


def transcribe_audio_long(gcs_uri: str, language_code: str = "en-US") -> tuple[str, float]:
    """Transcribe long audio file (> 60 seconds) using long-running recognition.

    Args:
        gcs_uri: GCS URI of the audio file (gs://bucket/object) in LINEAR16 WAV format
        language_code: Language code (e.g., 'en-US', 'cs-CZ')

    Returns:
        Tuple of (transcript, confidence)

    Raises:
        TranscriptionError: If transcription fails
    """
    try:
        logger.info(
            "Transcribing long audio",
            extra={"gcs_uri": gcs_uri, "language": language_code},
        )

        client = speech.SpeechClient()

        audio = speech.RecognitionAudio(uri=gcs_uri)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language_code,
            enable_automatic_punctuation=True,
        )

        operation = client.long_running_recognize(config=config, audio=audio)

        logger.info("Waiting for long-running transcription to complete", extra={"gcs_uri": gcs_uri})
        response = operation.result(timeout=600)  # Wait up to 10 minutes

        if not response.results:
            logger.warning("No transcription results", extra={"gcs_uri": gcs_uri})
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
            "Long audio transcription successful",
            extra={
                "gcs_uri": gcs_uri,
                "transcript_length": len(transcript),
                "confidence": avg_confidence,
            },
        )

        return transcript, avg_confidence
    except Exception as e:
        logger.error(
            "Failed to transcribe long audio",
            extra={"gcs_uri": gcs_uri, "error": str(e)},
        )
        raise TranscriptionError(f"Long audio transcription failed: {e}") from e


def transcribe_audio(
    file_path: Path,
    gcs_uri: str | None = None,
    language_code: str = "en-US",
) -> tuple[str, AudioMetadata]:
    """Transcribe audio file, automatically choosing short or long recognition.

    Args:
        file_path: Path to the audio file
        gcs_uri: Optional GCS URI for long audio files (must be LINEAR16 WAV)
        language_code: Language code (e.g., 'en-US', 'cs-CZ')

    Returns:
        Tuple of (transcript, metadata)

    Raises:
        TranscriptionError: If transcription fails
    """
    try:
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
            if metadata.duration_seconds and metadata.duration_seconds > 60:
                # Long audio: requires GCS URI of the CONVERTED file
                if not gcs_uri:
                    raise TranscriptionError(
                        "GCS URI required for audio files longer than 60 seconds. "
                        "Upload the converted LINEAR16 WAV file to GCS first."
                    )
                # Note: gcs_uri should point to the converted file uploaded to GCS
                transcript, confidence = transcribe_audio_long(gcs_uri, language_code)
            else:
                # Short audio: use synchronous recognition with converted file
                transcript, confidence = transcribe_audio_short(converted_path, language_code)

            # Update metadata with transcription info
            metadata = metadata._replace(
                confidence=confidence,
                language=language_code,
                sample_rate=sample_rate,
                channels=channels,
            )

            logger.info(
                "Audio transcription completed",
                extra={
                    "file_path": str(file_path),
                    "transcript_length": len(transcript),
                    "confidence": confidence,
                },
            )

            return transcript, metadata
        finally:
            # Clean up converted file
            if converted_path.exists():
                converted_path.unlink()
                logger.debug("Cleaned up converted file", extra={"path": str(converted_path)})

    except Exception as e:
        logger.error(
            "Failed to transcribe audio",
            extra={"file_path": str(file_path), "error": str(e)},
        )
        raise TranscriptionError(f"Audio transcription failed: {e}") from e
