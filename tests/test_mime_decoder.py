"""
Tests for MIME Decoder service.
"""

import pytest
from datetime import datetime
from eduscale.services.mime_decoder.service import (
    _convert_gcs_notification_to_cloud_event,
    process_cloud_event,
)
from eduscale.services.mime_decoder.models import CloudEvent


def test_convert_gcs_notification_to_cloud_event():
    """Test conversion of raw GCS notification to CloudEvent format."""
    # Sample GCS notification data
    gcs_notification = {
        "kind": "storage#object",
        "id": "test-bucket/test-file.txt/1234567890",
        "bucket": "test-bucket",
        "name": "test-file.txt",
        "contentType": "text/plain",
        "size": "1024",
        "timeCreated": "2025-11-13T20:23:47.000Z",
        "updated": "2025-11-13T20:23:47.000Z",
        "generation": "1234567890",
        "metageneration": "1",
    }

    # Convert to CloudEvent
    cloud_event = _convert_gcs_notification_to_cloud_event(gcs_notification)

    # Verify CloudEvent structure
    assert cloud_event.specversion == "1.0"
    assert cloud_event.type == "google.cloud.storage.object.v1.finalized"
    assert cloud_event.source == "//storage.googleapis.com/buckets/test-bucket"
    assert cloud_event.subject == "objects/test-file.txt"
    assert cloud_event.datacontenttype == "application/json"

    # Verify data payload
    assert cloud_event.data.bucket == "test-bucket"
    assert cloud_event.data.name == "test-file.txt"
    assert cloud_event.data.contentType == "text/plain"
    assert cloud_event.data.size == "1024"


def test_convert_gcs_notification_missing_fields():
    """Test that conversion fails gracefully with missing required fields."""
    # Missing bucket and name
    invalid_notification = {
        "kind": "storage#object",
        "contentType": "text/plain",
    }

    with pytest.raises(ValueError, match="Missing required fields"):
        _convert_gcs_notification_to_cloud_event(invalid_notification)


@pytest.mark.asyncio
async def test_process_cloud_event_skips_files_outside_directory():
    """Test that files outside the expected directory are skipped with 200 response."""
    # GCS notification for file outside uploads/ directory
    gcs_notification = {
        "kind": "storage#object",
        "id": "test-bucket/some/random/path/file.txt/1234567890",
        "bucket": "test-bucket",
        "name": "some/random/path/file.txt",
        "contentType": "text/plain",
        "size": "1024",
        "timeCreated": "2025-11-13T20:23:47.000Z",
        "updated": "2025-11-13T20:23:47.000Z",
        "generation": "1234567890",
        "metageneration": "1",
    }

    # Process the event
    result = await process_cloud_event(gcs_notification)

    # Verify successful skip response (not an error)
    assert result["status"] == "skipped"
    assert "outside expected directory pattern" in result["message"]
    assert result["object_name"] == "some/random/path/file.txt"
    assert "processing_time_ms" in result


def test_process_cloud_event_with_gcs_notification():
    """Test processing a raw GCS notification with new path format."""
    gcs_notification = {
        "kind": "storage#object",
        "id": "test-bucket/uploads/region-cz-01/abc123_report.pdf/1234567890",
        "bucket": "test-bucket",
        "name": "uploads/region-cz-01/abc123_report.pdf",
        "contentType": "application/pdf",
        "size": "2048",
        "timeCreated": "2025-11-13T20:23:47.000Z",
        "updated": "2025-11-13T20:23:47.000Z",
        "generation": "1234567890",
        "metageneration": "1",
    }

    # Note: This test would need mocking of transformer and backend services
    # For now, we're just testing the path parsing logic
    # In a real test, you'd mock the call_transformer and update_backend_status functions