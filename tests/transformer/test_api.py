"""Smoke tests for Transformer API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from eduscale.services.transformer.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_transform_file():
    """Mock transform_file function."""
    with patch("eduscale.services.transformer.main.transform_file") as mock:
        mock.return_value = {
            "file_id": "test-file-123",
            "status": "transformed",
            "text_uri": "gs://test-bucket/text/test-file-123.txt",
            "extracted_text_length": 1000,
            "metadata": {
                "extraction_method": "plain_text",
                "word_count": 200,
            },
        }
        yield mock


def test_transform_endpoint_success(client, mock_transform_file):
    """Test successful transformation request."""
    request_data = {
        "file_id": "test-file-123",
        "bucket": "test-bucket",
        "object_name": "test-file.txt",
        "content_type": "text/plain",
        "file_category": "text",
        "region_id": "region-1",
    }

    response = client.post("/process", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["file_id"] == "test-file-123"
    assert data["status"] == "transformed"
    assert "text_uri" in data
    assert "metadata" in data


def test_transform_endpoint_missing_file_id(client):
    """Test transformation request with missing file_id."""
    request_data = {
        "bucket": "test-bucket",
        "object_name": "test-file.txt",
        "content_type": "text/plain",
        "file_category": "text",
    }

    response = client.post("/process", json=request_data)

    assert response.status_code == 422  # Validation error


def test_transform_endpoint_file_too_large(client):
    """Test transformation request with file too large."""
    from eduscale.services.transformer.exceptions import FileTooLargeError

    with patch("eduscale.services.transformer.main.transform_file") as mock:
        mock.side_effect = FileTooLargeError("File too large")

        request_data = {
            "file_id": "test-file-123",
            "bucket": "test-bucket",
            "object_name": "test-file.txt",
            "content_type": "text/plain",
            "file_category": "text",
        }

        response = client.post("/process", json=request_data)

        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()


def test_transform_endpoint_internal_error(client):
    """Test transformation request with internal error."""
    from eduscale.services.transformer.exceptions import TransformationError

    with patch("eduscale.services.transformer.main.transform_file") as mock:
        mock.side_effect = TransformationError("Internal error")

        request_data = {
            "file_id": "test-file-123",
            "bucket": "test-bucket",
            "object_name": "test-file.txt",
            "content_type": "text/plain",
            "file_category": "text",
        }

        response = client.post("/process", json=request_data)

        assert response.status_code == 500


def test_health_endpoint_success(client):
    """Test health check endpoint."""
    with patch("eduscale.services.transformer.main.StorageClient"):
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "transformer"
        assert data["status"] in ["healthy", "degraded"]


def test_health_endpoint_degraded(client):
    """Test health check when Cloud Storage is down."""
    with patch("eduscale.services.transformer.main.StorageClient") as mock_storage:
        mock_storage.side_effect = Exception("Storage unavailable")

        response = client.get("/health")

        # Should return 503 when critical dependency (Cloud Storage) is unhealthy
        assert response.status_code == 503
        data = response.json()
        assert "unavailable" in data["detail"].lower()
