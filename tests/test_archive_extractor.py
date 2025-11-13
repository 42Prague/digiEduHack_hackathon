"""Unit tests for archive extractor."""

import gzip
import os
import tarfile
import tempfile
import zipfile
import io
import asyncio

import pytest

from eduscale.services.mime_decoder.archive_extractor import (
    ArchiveExtractor,
    ArchiveExtractionError,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def extractor():
    """Create archive extractor instance."""
    return ArchiveExtractor(max_files=10, max_file_size_mb=5)


def create_test_zip(zip_path: str, files: dict):
    """Helper to create test ZIP archive."""
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for filename, content in files.items():
            zf.writestr(filename, content)


def create_test_tar(tar_path: str, files: dict):
    """Helper to create test TAR archive."""
    with tarfile.open(tar_path, 'w') as tf:
        for filename, content in files.items():
            data = content.encode() if isinstance(content, str) else content
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(data)
            tf.addfile(tarinfo, io.BytesIO(data))


def test_extract_zip_success(extractor, temp_dir):
    """Test successful ZIP extraction."""
    zip_path = os.path.join(temp_dir, "test.zip")
    extract_dir = os.path.join(temp_dir, "extracted")
    
    create_test_zip(zip_path, {"file1.txt": "content1", "file2.txt": "content2"})
    
    files = asyncio.run(extractor.extract_archive(zip_path, "zip", extract_dir))
    
    assert len(files) == 2
    assert files[0].filename == "file1.txt"
    assert files[1].filename == "file2.txt"


def test_extract_tar_success(extractor, temp_dir):
    """Test successful TAR extraction."""
    tar_path = os.path.join(temp_dir, "test.tar")
    extract_dir = os.path.join(temp_dir, "extracted")
    
    create_test_tar(tar_path, {"file1.txt": "content1", "file2.txt": "content2"})
    
    files = asyncio.run(extractor.extract_archive(tar_path, "tar", extract_dir))
    
    assert len(files) == 2


def test_extract_gzip_success(extractor, temp_dir):
    """Test successful GZIP extraction."""
    gz_path = os.path.join(temp_dir, "test.txt.gz")
    extract_dir = os.path.join(temp_dir, "extracted")
    
    with gzip.open(gz_path, 'wb') as f:
        f.write(b"test content")
    
    files = asyncio.run(extractor.extract_archive(gz_path, "gzip", extract_dir))
    
    assert len(files) == 1
    assert files[0].filename == "test.txt"


def test_file_count_limit(temp_dir):
    """Test file count limit enforcement."""
    extractor = ArchiveExtractor(max_files=2, max_file_size_mb=5)
    zip_path = os.path.join(temp_dir, "test.zip")
    extract_dir = os.path.join(temp_dir, "extracted")
    
    create_test_zip(zip_path, {"file1.txt": "c1", "file2.txt": "c2", "file3.txt": "c3"})
    
    files = asyncio.run(extractor.extract_archive(zip_path, "zip", extract_dir))
    
    assert len(files) == 2


def test_file_size_limit(temp_dir):
    """Test file size limit enforcement."""
    extractor = ArchiveExtractor(max_files=10, max_file_size_mb=0.001)
    zip_path = os.path.join(temp_dir, "test.zip")
    extract_dir = os.path.join(temp_dir, "extracted")
    
    create_test_zip(zip_path, {"small.txt": "small", "large.txt": "x" * 2000})
    
    files = asyncio.run(extractor.extract_archive(zip_path, "zip", extract_dir))
    
    assert len(files) == 1
    assert files[0].filename == "small.txt"


def test_path_traversal_protection(extractor, temp_dir):
    """Test path traversal protection."""
    zip_path = os.path.join(temp_dir, "test.zip")
    extract_dir = os.path.join(temp_dir, "extracted")
    
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("../../../etc/passwd", "malicious")
        zf.writestr("safe.txt", "safe content")
    
    files = asyncio.run(extractor.extract_archive(zip_path, "zip", extract_dir))
    
    assert len(files) == 1
    assert files[0].filename == "safe.txt"
