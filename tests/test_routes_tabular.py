"""Tests for tabular API endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from eduscale.api.v1.routes_tabular import router
from eduscale.tabular.pipeline import IngestResult

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "tabular-service"
    assert "models" in data
    assert "embedding_model" in data["models"]


@patch("eduscale.api.v1.routes_tabular.StorageClient")
@patch("eduscale.api.v1.routes_tabular.process_tabular_text")
def test_handle_cloud_event_success(mock_process, mock_storage_class):
    """Test CloudEvent handling with successful processing."""
    # Mock storage client
    mock_storage = MagicMock()
    mock_storage_class.return_value = mock_storage

    # Mock process_tabular_text
    mock_result = IngestResult(
        file_id="test-file-123",
        status="INGESTED",
        table_type="ASSESSMENT",
        rows_loaded=10,
        clean_location=None,
        bytes_processed=None,
        cache_hit=None,
        error_message=None,
        warnings=[],
        processing_time_ms=100,
    )
    mock_process.return_value = mock_result

    # Create CloudEvent payload
    cloud_event = {
        "id": "event-123",
        "type": "google.cloud.storage.object.v1.finalized",
        "data": {"bucket": "test-bucket", "name": "text/test-file-123.txt"},
    }

    # Send request
    response = client.post("/", json=cloud_event)

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["file_id"] == "test-file-123"
    assert data["table_type"] == "ASSESSMENT"


def test_handle_cloud_event_skip_non_text():
    """Test CloudEvent handling skips non-text files."""
    cloud_event = {
        "id": "event-456",
        "type": "google.cloud.storage.object.v1.finalized",
        "data": {"bucket": "test-bucket", "name": "uploads/file.pdf"},
    }

    response = client.post("/", json=cloud_event)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "skipped"
    assert data["reason"] == "not_text_file"


def test_handle_cloud_event_unsupported_type():
    """Test CloudEvent handling with unsupported event type."""
    cloud_event = {
        "id": "event-789",
        "type": "google.cloud.storage.object.v1.deleted",
        "data": {"bucket": "test-bucket", "name": "text/file.txt"},
    }

    response = client.post("/", json=cloud_event)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "skipped"
    assert data["reason"] == "unsupported_event_type"


def test_handle_cloud_event_missing_data():
    """Test CloudEvent handling with missing data."""
    cloud_event = {
        "id": "event-999",
        "type": "google.cloud.storage.object.v1.finalized",
        "data": {},  # Missing bucket and name
    }

    response = client.post("/", json=cloud_event)

    assert response.status_code == 400
    assert "Missing bucket or object_name" in response.json()["detail"]


@patch("eduscale.api.v1.routes_tabular.StorageClient")
@patch("eduscale.api.v1.routes_tabular.process_tabular_text")
def test_analyze_tabular_direct_success(mock_process, mock_storage_class):
    """Test direct API endpoint with successful processing."""
    # Mock storage client
    mock_storage = MagicMock()
    mock_storage_class.return_value = mock_storage

    # Mock process_tabular_text
    mock_result = IngestResult(
        file_id="test-file-456",
        status="INGESTED",
        table_type="FEEDBACK",
        rows_loaded=5,
        clean_location=None,
        bytes_processed=1000,
        cache_hit=False,
        error_message=None,
        warnings=["Low confidence mapping"],
        processing_time_ms=250,
    )
    mock_process.return_value = mock_result

    # Create request
    request_data = {
        "file_id": "test-file-456",
        "region_id": "region-cz-01",
        "text_uri": "gs://test-bucket/text/test-file-456.txt",
        "original_content_type": "text/csv",
    }

    # Send request
    response = client.post("/api/v1/tabular/analyze", json=request_data)

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["file_id"] == "test-file-456"
    assert data["status"] == "INGESTED"
    assert data["table_type"] == "FEEDBACK"
    assert data["rows_loaded"] == 5
    assert len(data["warnings"]) == 1


def test_analyze_tabular_direct_invalid_uri():
    """Test direct API endpoint with invalid text_uri."""
    request_data = {
        "file_id": "test-file-789",
        "region_id": "region-cz-01",
        "text_uri": "invalid-uri",  # Not gs:// format
    }

    response = client.post("/api/v1/tabular/analyze", json=request_data)

    assert response.status_code == 400
    assert "Invalid text_uri format" in response.json()["detail"]
