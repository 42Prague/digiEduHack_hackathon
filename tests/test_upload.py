"""Tests for file upload functionality."""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from eduscale.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_local_backend():
    """Mock local storage backend."""
    with patch("eduscale.storage.factory.local_backend") as mock:
        mock.get_backend_name.return_value = "local"
        mock.store_file = AsyncMock(
            return_value="data/uploads/raw/test-id/test.csv"
        )
        yield mock


@pytest.fixture
def local_storage_settings(monkeypatch):
    """Configure local storage settings."""
    from eduscale.core.config import settings

    monkeypatch.setattr(settings, "STORAGE_BACKEND", "local")
    monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 10)
    monkeypatch.setattr(settings, "ALLOWED_UPLOAD_MIME_TYPES", "text/csv")


def test_upload_valid_file(client, mock_local_backend, local_storage_settings):
    """Test uploading a valid file."""
    file_content = b"name,age\nJohn,30\nJane,25"
    files = {"file": ("test.csv", io.BytesIO(file_content), "text/csv")}
    data = {"region_id": "school-123"}

    response = client.post("/api/v1/upload", files=files, data=data)

    assert response.status_code == 201
    json_data = response.json()
    assert "file_id" in json_data
    assert json_data["file_name"] == "test.csv"
    assert json_data["storage_backend"] == "local"
    assert json_data["region_id"] == "school-123"
    assert json_data["content_type"] == "text/csv"
    assert json_data["size_bytes"] == len(file_content)


def test_upload_empty_region_id(client, local_storage_settings):
    """Test upload with empty region_id."""
    file_content = b"test data"
    files = {"file": ("test.csv", io.BytesIO(file_content), "text/csv")}
    data = {"region_id": ""}

    response = client.post("/api/v1/upload", files=files, data=data)

    assert response.status_code == 400
    assert "region_id" in response.json()["detail"].lower()


def test_upload_oversized_file(client, local_storage_settings):
    """Test upload with file exceeding size limit."""
    # Create file larger than 10MB
    file_content = b"x" * (11 * 1024 * 1024)
    files = {"file": ("large.csv", io.BytesIO(file_content), "text/csv")}
    data = {"region_id": "school-456"}

    response = client.post("/api/v1/upload", files=files, data=data)

    assert response.status_code == 400
    assert "size" in response.json()["detail"].lower()


def test_upload_invalid_mime_type(client, local_storage_settings):
    """Test upload with disallowed MIME type."""
    file_content = b"test data"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    data = {"region_id": "school-789"}

    response = client.post("/api/v1/upload", files=files, data=data)

    assert response.status_code == 400
    assert "content type" in response.json()["detail"].lower()


def test_upload_creates_record(
    client, mock_local_backend, local_storage_settings
):
    """Test that upload creates a record in the upload store."""
    from eduscale.storage.upload_store import upload_store

    file_content = b"name,age\nJohn,30"
    files = {"file": ("test.csv", io.BytesIO(file_content), "text/csv")}
    data = {"region_id": "city-london"}

    response = client.post("/api/v1/upload", files=files, data=data)

    assert response.status_code == 201
    file_id = response.json()["file_id"]

    # Verify record exists in store
    record = upload_store.get(file_id)
    assert record is not None
    assert record.file_id == file_id
    assert record.region_id == "city-london"
    assert record.file_name == "test.csv"
