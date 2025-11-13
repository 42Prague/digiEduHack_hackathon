"""
Tests for MIME Decoder models and path parsing.
"""

import pytest
from datetime import datetime
from eduscale.services.mime_decoder.models import (
    CloudEvent,
    StorageObjectData,
    ProcessingRequest,
)


def test_processing_request_from_cloud_event_new_format():
    """Test ProcessingRequest creation from CloudEvent with new path format."""
    # Create CloudEvent with new path format: uploads/{region_id}/{file_id}_{filename}
    storage_data = StorageObjectData(
        bucket="test-bucket",
        name="uploads/region-cz-01/abc123_report.pdf",
        contentType="application/pdf",
        size="2048",
        timeCreated=datetime.utcnow(),
        updated=datetime.utcnow(),
        generation="1234567890",
        metageneration="1",
    )

    cloud_event = CloudEvent(
        specversion="1.0",
        type="google.cloud.storage.object.v1.finalized",
        source="//storage.googleapis.com/buckets/test-bucket",
        subject="objects/uploads/region-cz-01/abc123_report.pdf",
        id="test-event-123",
        time=datetime.utcnow(),
        datacontenttype="application/json",
        data=storage_data,
    )

    # Create ProcessingRequest
    processing_req = ProcessingRequest.from_cloud_event(cloud_event, "text")

    # Verify extracted metadata
    assert processing_req.file_id == "abc123"
    assert processing_req.region_id == "region-cz-01"
    assert processing_req.bucket == "test-bucket"
    assert processing_req.object_name == "uploads/region-cz-01/abc123_report.pdf"
    assert processing_req.content_type == "application/pdf"
    assert processing_req.file_category == "text"
    assert processing_req.size_bytes == 2048


def test_processing_request_from_cloud_event_with_complex_filename():
    """Test path parsing with complex filename containing underscores."""
    storage_data = StorageObjectData(
        bucket="test-bucket",
        name="uploads/school-paris-01/xyz789_2024_9_FG-PL-ucastnici_ZAZNAM.m4a",
        contentType="audio/mp4",
        size="5242880",
        timeCreated=datetime.utcnow(),
        updated=datetime.utcnow(),
    )

    cloud_event = CloudEvent(
        specversion="1.0",
        type="google.cloud.storage.object.v1.finalized",
        source="//storage.googleapis.com/buckets/test-bucket",
        subject="objects/uploads/school-paris-01/xyz789_2024_9_FG-PL-ucastnici_ZAZNAM.m4a",
        id="test-event-456",
        time=datetime.utcnow(),
        datacontenttype="application/json",
        data=storage_data,
    )

    processing_req = ProcessingRequest.from_cloud_event(cloud_event, "audio")

    # Verify extracted metadata
    assert processing_req.file_id == "xyz789"
    assert processing_req.region_id == "school-paris-01"
    assert processing_req.file_category == "audio"


def test_processing_request_fallback_for_invalid_path():
    """Test fallback behavior when path doesn't match expected pattern."""
    storage_data = StorageObjectData(
        bucket="test-bucket",
        name="some/random/path/file.txt",
        contentType="text/plain",
        size="1024",
        timeCreated=datetime.utcnow(),
        updated=datetime.utcnow(),
    )

    cloud_event = CloudEvent(
        specversion="1.0",
        type="google.cloud.storage.object.v1.finalized",
        source="//storage.googleapis.com/buckets/test-bucket",
        subject="objects/some/random/path/file.txt",
        id="test-event-789",
        time=datetime.utcnow(),
        datacontenttype="application/json",
        data=storage_data,
    )

    processing_req = ProcessingRequest.from_cloud_event(cloud_event, "text")

    # Verify fallback behavior
    assert processing_req.file_id == "file"  # Extracted from filename
    assert processing_req.region_id == "unknown"  # Fallback value
    assert processing_req.file_category == "text"
