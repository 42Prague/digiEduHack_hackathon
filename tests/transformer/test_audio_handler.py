"""Tests for ffmpeg-based audio handler."""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from eduscale.services.transformer.handlers.audio_handler import (
    get_audio_metadata,
    convert_to_linear16,
    AudioMetadata,
)
from eduscale.services.transformer.exceptions import TranscriptionError


@pytest.fixture
def mock_ffprobe_output():
    """Mock ffprobe JSON output."""
    return json.dumps({
        "streams": [
            {
                "codec_type": "audio",
                "codec_name": "mp3",
                "sample_rate": "44100",
                "channels": 2,
            }
        ],
        "format": {
            "duration": "45.5",
            "format_name": "mp3",
        }
    })


def test_get_audio_metadata_success(mock_ffprobe_output):
    """Test successful audio metadata extraction with ffprobe."""
    with patch("eduscale.services.transformer.handlers.audio_handler.subprocess.run") as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = mock_ffprobe_output
        mock_run.return_value = mock_result

        with tempfile.NamedTemporaryFile(suffix=".mp3") as temp_file:
            file_path = Path(temp_file.name)
            metadata = get_audio_metadata(file_path)

            assert isinstance(metadata, AudioMetadata)
            assert metadata.duration_seconds == 45.5
            assert metadata.sample_rate == 44100
            assert metadata.channels == 2
            assert metadata.format == "MP3"

            # Verify ffprobe was called correctly
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "ffprobe"
            assert str(file_path) in call_args


def test_get_audio_metadata_no_audio_stream():
    """Test metadata extraction when no audio stream found."""
    ffprobe_output = json.dumps({
        "streams": [
            {
                "codec_type": "video",  # No audio stream
                "codec_name": "h264",
            }
        ],
        "format": {}
    })

    with patch("eduscale.services.transformer.handlers.audio_handler.subprocess.run") as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ffprobe_output
        mock_run.return_value = mock_result

        with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_file:
            file_path = Path(temp_file.name)
            with pytest.raises(TranscriptionError, match="No audio stream found"):
                get_audio_metadata(file_path)


def test_get_audio_metadata_ffprobe_failure():
    """Test metadata extraction when ffprobe fails."""
    with patch("eduscale.services.transformer.handlers.audio_handler.subprocess.run") as mock_run:
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "ffprobe error: invalid file"
        mock_run.return_value = mock_result

        with tempfile.NamedTemporaryFile(suffix=".mp3") as temp_file:
            file_path = Path(temp_file.name)
            with pytest.raises(TranscriptionError, match="ffprobe failed"):
                get_audio_metadata(file_path)


def test_get_audio_metadata_timeout():
    """Test metadata extraction timeout."""
    with patch("eduscale.services.transformer.handlers.audio_handler.subprocess.run") as mock_run:
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("ffprobe", 30)

        with tempfile.NamedTemporaryFile(suffix=".mp3") as temp_file:
            file_path = Path(temp_file.name)
            with pytest.raises(TranscriptionError, match="timed out"):
                get_audio_metadata(file_path)


def test_convert_to_linear16_success():
    """Test successful audio conversion with ffmpeg."""
    with patch("eduscale.services.transformer.handlers.audio_handler.subprocess.run") as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as input_file:
            input_path = Path(input_file.name)
            output_path = input_path.with_suffix(".wav")

            try:
                # Create output file to simulate ffmpeg behavior
                output_path.write_bytes(b"RIFF" + b"\x00" * 100)

                sample_rate, channels = convert_to_linear16(input_path, output_path)

                assert sample_rate == 16000
                assert channels == 1

                # Verify ffmpeg was called correctly
                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]
                assert call_args[0] == "ffmpeg"
                assert "-i" in call_args
                assert str(input_path) in call_args
                assert "-acodec" in call_args
                assert "pcm_s16le" in call_args
                assert "-ar" in call_args
                assert "16000" in call_args
                assert "-ac" in call_args
                assert "1" in call_args
                assert str(output_path) in call_args
            finally:
                # Cleanup
                if input_path.exists():
                    input_path.unlink()
                if output_path.exists():
                    output_path.unlink()


def test_convert_to_linear16_ffmpeg_failure():
    """Test conversion when ffmpeg fails."""
    with patch("eduscale.services.transformer.handlers.audio_handler.subprocess.run") as mock_run:
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "ffmpeg error: unsupported codec"
        mock_run.return_value = mock_result

        with tempfile.NamedTemporaryFile(suffix=".mp3") as input_file:
            input_path = Path(input_file.name)
            output_path = input_path.with_suffix(".wav")

            with pytest.raises(TranscriptionError, match="conversion failed"):
                convert_to_linear16(input_path, output_path)


def test_convert_to_linear16_timeout():
    """Test conversion timeout."""
    with patch("eduscale.services.transformer.handlers.audio_handler.subprocess.run") as mock_run:
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("ffmpeg", 120)

        with tempfile.NamedTemporaryFile(suffix=".mp3") as input_file:
            input_path = Path(input_file.name)
            output_path = input_path.with_suffix(".wav")

            with pytest.raises(TranscriptionError, match="timed out"):
                convert_to_linear16(input_path, output_path)


def test_convert_to_linear16_output_not_created():
    """Test conversion when output file is not created."""
    with patch("eduscale.services.transformer.handlers.audio_handler.subprocess.run") as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        with tempfile.NamedTemporaryFile(suffix=".mp3") as input_file:
            input_path = Path(input_file.name)
            output_path = input_path.with_suffix(".wav")

            # Don't create output file - simulates ffmpeg failure

            with pytest.raises(TranscriptionError, match="Output file was not created"):
                convert_to_linear16(input_path, output_path)


def test_audio_metadata_structure():
    """Test AudioMetadata structure."""
    metadata = AudioMetadata(
        duration_seconds=60.5,
        sample_rate=16000,
        channels=1,
        format="MP3",
        confidence=0.95,
        language="en-US",
    )

    assert metadata.duration_seconds == 60.5
    assert metadata.sample_rate == 16000
    assert metadata.channels == 1
    assert metadata.format == "MP3"
    assert metadata.confidence == 0.95
    assert metadata.language == "en-US"


def test_audio_metadata_optional_fields():
    """Test AudioMetadata with optional fields as None."""
    metadata = AudioMetadata(
        format="WAV",
    )

    assert metadata.format == "WAV"
    assert metadata.duration_seconds is None
    assert metadata.sample_rate is None
    assert metadata.channels is None
    assert metadata.confidence is None
    assert metadata.language is None
