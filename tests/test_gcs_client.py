"""Unit tests for GCS client."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from google.api_core.exceptions import GoogleAPIError, NotFound

from eduscale.services.mime_decoder.gcs_client import GCSClient


@pytest.fixture
def mock_storage_client():
    """Mock Google Cloud Storage client."""
    with patch('eduscale.services.mime_decoder.gcs_client.storage.Client') as mock_client:
        yield mock_client


@pytest.fixture
def gcs_client(mock_storage_client):
    """Create GCS client with mocked storage."""
    return GCSClient(bucket_name="test-bucket")


@pytest.mark.asyncio
async def test_download_file_success(gcs_client):
    """Test successful file download."""
    mock_blob = Mock()
    gcs_client.bucket.blob = Mock(return_value=mock_blob)
    
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        await gcs_client.download_file("test-object", "/tmp/test-file")
        
        gcs_client.bucket.blob.assert_called_once_with("test-object")
        mock_to_thread.assert_called_once()


@pytest.mark.asyncio
async def test_download_file_not_found(gcs_client):
    """Test download when file doesn't exist."""
    mock_blob = Mock()
    gcs_client.bucket.blob = Mock(return_value=mock_blob)
    
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.side_effect = NotFound("Object not found")
        
        with pytest.raises(NotFound):
            await gcs_client.download_file("missing-object", "/tmp/test-file")


@pytest.mark.asyncio
async def test_download_file_api_error(gcs_client):
    """Test download with API error."""
    mock_blob = Mock()
    gcs_client.bucket.blob = Mock(return_value=mock_blob)
    
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.side_effect = GoogleAPIError("API error")
        
        with pytest.raises(GoogleAPIError):
            await gcs_client.download_file("test-object", "/tmp/test-file")


@pytest.mark.asyncio
async def test_upload_file_success(gcs_client):
    """Test successful file upload."""
    mock_blob = Mock()
    gcs_client.bucket.blob = Mock(return_value=mock_blob)
    
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        await gcs_client.upload_file("/tmp/test-file", "test-object", "text/plain")
        
        gcs_client.bucket.blob.assert_called_once_with("test-object")
        mock_to_thread.assert_called_once()


@pytest.mark.asyncio
async def test_upload_file_api_error(gcs_client):
    """Test upload with API error."""
    mock_blob = Mock()
    gcs_client.bucket.blob = Mock(return_value=mock_blob)
    
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.side_effect = GoogleAPIError("Upload failed")
        
        with pytest.raises(GoogleAPIError):
            await gcs_client.upload_file("/tmp/test-file", "test-object", "text/plain")


def test_get_file_size_success(gcs_client):
    """Test getting file size."""
    mock_blob = Mock()
    mock_blob.size = 1024
    gcs_client.bucket.blob = Mock(return_value=mock_blob)
    
    size = gcs_client.get_file_size("test-object")
    
    assert size == 1024
    gcs_client.bucket.blob.assert_called_once_with("test-object")
    mock_blob.reload.assert_called_once()


def test_get_file_size_not_found(gcs_client):
    """Test getting size of non-existent file."""
    mock_blob = Mock()
    mock_blob.reload.side_effect = NotFound("Object not found")
    gcs_client.bucket.blob = Mock(return_value=mock_blob)
    
    with pytest.raises(NotFound):
        gcs_client.get_file_size("missing-object")
