"""Tests for upload store."""

from datetime import datetime

import pytest

from eduscale.storage.upload_store import UploadRecord, UploadStore


@pytest.fixture
def upload_store():
    """Create a fresh upload store for each test."""
    return UploadStore()


@pytest.fixture
def sample_record():
    """Create a sample upload record."""
    return UploadRecord(
        file_id="test-uuid-123",
        region_id="eu-west",
        file_name="test.csv",
        content_type="text/csv",
        size_bytes=1024,
        storage_backend="local",
        storage_path="data/uploads/raw/test-uuid-123/test.csv",
        created_at=datetime.utcnow(),
    )


def test_create_record(upload_store, sample_record):
    """Test creating an upload record."""
    upload_store.create(sample_record)

    retrieved = upload_store.get(sample_record.file_id)
    assert retrieved is not None
    assert retrieved.file_id == sample_record.file_id
    assert retrieved.region_id == sample_record.region_id
    assert retrieved.file_name == sample_record.file_name


def test_get_nonexistent_record(upload_store):
    """Test retrieving a record that doesn't exist."""
    result = upload_store.get("nonexistent-id")
    assert result is None


def test_list_all_empty(upload_store):
    """Test listing all records when store is empty."""
    records = upload_store.list_all()
    assert records == []


def test_list_all_with_records(upload_store):
    """Test listing all records."""
    record1 = UploadRecord(
        file_id="id-1",
        region_id="eu-west",
        file_name="file1.csv",
        content_type="text/csv",
        size_bytes=100,
        storage_backend="local",
        storage_path="path1",
        created_at=datetime.utcnow(),
    )
    record2 = UploadRecord(
        file_id="id-2",
        region_id="us-east",
        file_name="file2.csv",
        content_type="text/csv",
        size_bytes=200,
        storage_backend="local",
        storage_path="path2",
        created_at=datetime.utcnow(),
    )

    upload_store.create(record1)
    upload_store.create(record2)

    records = upload_store.list_all()
    assert len(records) == 2
    assert record1 in records
    assert record2 in records


def test_overwrite_record(upload_store, sample_record):
    """Test that creating a record with same file_id overwrites."""
    upload_store.create(sample_record)

    # Create new record with same file_id but different data
    new_record = UploadRecord(
        file_id=sample_record.file_id,
        region_id="us-east",
        file_name="different.csv",
        content_type="text/csv",
        size_bytes=2048,
        storage_backend="gcs",
        storage_path="gs://bucket/path",
        created_at=datetime.utcnow(),
    )
    upload_store.create(new_record)

    # Should retrieve the new record
    retrieved = upload_store.get(sample_record.file_id)
    assert retrieved.region_id == "us-east"
    assert retrieved.file_name == "different.csv"
    assert retrieved.storage_backend == "gcs"

    # Should only have one record
    assert len(upload_store.list_all()) == 1
