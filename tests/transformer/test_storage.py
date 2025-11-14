"""Smoke tests for Storage client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

from eduscale.services.transformer.storage import StorageClient
from eduscale.services.transformer.exceptions import StorageError


@pytest.fixture
def mock_storage_client():
    """Create a mock GCS client."""
    with patch("eduscale.services.transformer.storage.storage.Client") as mock_client:
        yield mock_client


def test_storage_client_initialization(mock_storage_client):
    """Test StorageClient initialization."""
    client = StorageClient(project_id="test-project")
    assert client is not None
    mock_storage_client.assert_called_once_with(project="test-project")


def test_storage_client_download_file_success(mock_storage_client):
    """Test successful file download."""
    # Setup mock
    mock_bucket = Mock()
    mock_blob = Mock()

    # Create a side effect that writes a file when download_to_filename is called
    def mock_download(filename):
        Path(filename).write_text("test content")

    mock_blob.download_to_filename.side_effect = mock_download
    mock_storage_client.return_value.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    client = StorageClient(project_id="test-project")

    with tempfile.TemporaryDirectory() as tmpdir:
        dest_path = Path(tmpdir) / "test.txt"
        client.download_file("test-bucket", "test-object", dest_path)

        mock_storage_client.return_value.bucket.assert_called_with("test-bucket")
        mock_bucket.blob.assert_called_with("test-object")
        mock_blob.download_to_filename.assert_called_once()

        # Verify file was created
        assert dest_path.exists()
        assert dest_path.read_text() == "test content"


def test_storage_client_download_file_not_found(mock_storage_client):
    """Test file download when file doesn't exist."""
    from google.cloud.exceptions import NotFound

    mock_bucket = Mock()
    mock_blob = Mock()
    mock_blob.download_to_filename.side_effect = NotFound("File not found")
    mock_storage_client.return_value.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    client = StorageClient(project_id="test-project")

    with tempfile.TemporaryDirectory() as tmpdir:
        dest_path = Path(tmpdir) / "test.txt"
        with pytest.raises(StorageError, match="File not found"):
            client.download_file("test-bucket", "test-object", dest_path)


def test_storage_client_upload_text_streaming_success(mock_storage_client):
    """Test successful text upload using streaming."""
    mock_bucket = Mock()
    mock_blob = Mock()
    mock_file_handle = MagicMock()

    # Mock blob.open() context manager
    mock_blob.open.return_value.__enter__ = Mock(return_value=mock_file_handle)
    mock_blob.open.return_value.__exit__ = Mock(return_value=False)

    mock_storage_client.return_value.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    client = StorageClient(project_id="test-project")

    # Create a generator for text chunks
    def text_generator():
        yield "Test "
        yield "content"

    text_uri = client.upload_text_streaming("test-bucket", "test-object.txt", text_generator())

    assert text_uri == "gs://test-bucket/test-object.txt"
    mock_blob.open.assert_called_once_with("w", encoding="utf-8")
    # Verify write was called for each chunk
    assert mock_file_handle.write.call_count == 2
    mock_file_handle.write.assert_any_call("Test ")
    mock_file_handle.write.assert_any_call("content")


def test_storage_client_get_file_size(mock_storage_client):
    """Test getting file size."""
    mock_bucket = Mock()
    mock_blob = Mock()
    mock_blob.size = 1024
    mock_storage_client.return_value.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    client = StorageClient(project_id="test-project")
    size = client.get_file_size("test-bucket", "test-object")

    assert size == 1024
    mock_blob.reload.assert_called_once()
