"""Tests for storage backends."""

import io
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from eduscale.storage.gcs import GCSStorageBackend
from eduscale.storage.local import LocalStorageBackend


class TestLocalStorageBackend:
    """Tests for local storage backend."""

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        backend = LocalStorageBackend()

        # Test path traversal removal
        assert "../etc/passwd" not in backend._sanitize_filename("../etc/passwd")
        assert "..\\" not in backend._sanitize_filename("..\\windows\\system32")

        # Test directory separator replacement
        assert "/" not in backend._sanitize_filename("path/to/file.txt")
        assert "\\" not in backend._sanitize_filename("path\\to\\file.txt")

        # Test special character replacement
        result = backend._sanitize_filename("file@#$.txt")
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result

        # Test valid characters preserved
        result = backend._sanitize_filename("valid-file_name.123.txt")
        assert "valid-file_name.123.txt" == result

    def test_get_target_path(self):
        """Test target path generation."""
        backend = LocalStorageBackend()
        file_id = "test-uuid-123"
        file_name = "report.csv"
        region_id = "region-test-01"

        path = backend.get_target_path(file_id, file_name, region_id)

        assert file_id in path
        assert region_id in path
        assert ".csv" in path
        assert "data/uploads" in path

    @pytest.mark.asyncio
    async def test_store_file(self):
        """Test file storage to local filesystem."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LocalStorageBackend()
            backend.base_path = Path(tmpdir)

            file_id = "test-uuid-456"
            file_name = "test.csv"
            region_id = "region-test-02"
            content = b"name,age\nJohn,30"
            file_data = io.BytesIO(content)

            storage_path = await backend.store_file(
                file_id, file_name, "text/csv", file_data, region_id
            )

            # Verify file was created
            assert Path(storage_path).exists()

            # Verify content
            with open(storage_path, "rb") as f:
                assert f.read() == content

    def test_get_backend_name(self):
        """Test backend name."""
        backend = LocalStorageBackend()
        assert backend.get_backend_name() == "local"


class TestGCSStorageBackend:
    """Tests for GCS storage backend."""

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        backend = GCSStorageBackend()

        # Test path traversal removal
        assert "../etc/passwd" not in backend._sanitize_filename("../etc/passwd")

        # Test directory separator replacement
        assert "/" not in backend._sanitize_filename("path/to/file.txt")

        # Test valid characters preserved
        result = backend._sanitize_filename("valid-file_name.123.txt")
        assert "valid-file_name.123.txt" == result

    def test_get_target_path(self):
        """Test GCS target path generation."""
        with patch("eduscale.storage.gcs.settings") as mock_settings:
            mock_settings.GCS_BUCKET_NAME = "test-bucket"

            backend = GCSStorageBackend()
            file_id = "test-uuid-789"
            file_name = "report.csv"
            region_id = "region-test-03"

            path = backend.get_target_path(file_id, file_name, region_id)

            assert "gs://test-bucket" in path
            assert file_id in path
            assert region_id in path
            assert ".csv" in path
            assert "uploads/" in path

    @pytest.mark.asyncio
    async def test_store_file(self):
        """Test file upload to GCS."""
        with patch("eduscale.storage.gcs.storage.Client") as mock_client_class:
            with patch("eduscale.storage.gcs.settings") as mock_settings:
                mock_settings.GCS_BUCKET_NAME = "test-bucket"
                mock_settings.GCP_PROJECT_ID = "test-project"

                # Setup mocks
                mock_client = MagicMock()
                mock_bucket = MagicMock()
                mock_blob = MagicMock()

                mock_client_class.return_value = mock_client
                mock_client.bucket.return_value = mock_bucket
                mock_bucket.blob.return_value = mock_blob

                backend = GCSStorageBackend()
                file_id = "test-uuid-999"
                file_name = "test.csv"
                region_id = "region-test-04"
                content = b"name,age\nJohn,30"
                file_data = io.BytesIO(content)

                storage_path = await backend.store_file(
                    file_id, file_name, "text/csv", file_data, region_id
                )

                # Verify blob upload was called
                mock_blob.upload_from_file.assert_called_once()
                assert mock_blob.content_type == "text/csv"
                assert "gs://test-bucket" in storage_path
                assert file_id in storage_path

    def test_get_backend_name(self):
        """Test backend name."""
        backend = GCSStorageBackend()
        assert backend.get_backend_name() == "gcs"

    def test_get_bucket_missing_config(self):
        """Test bucket initialization with missing config."""
        with patch("eduscale.storage.gcs.settings") as mock_settings:
            mock_settings.GCS_BUCKET_NAME = ""

            backend = GCSStorageBackend()

            with pytest.raises(ValueError, match="GCS_BUCKET_NAME not configured"):
                backend._get_bucket()
