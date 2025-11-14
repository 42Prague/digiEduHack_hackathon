"""Smoke tests for Text handler."""

import pytest
from pathlib import Path
import tempfile

from eduscale.services.transformer.handlers.text_handler import (
    extract_text_from_plain,
    ExtractionMetadata,
)
from eduscale.services.transformer.exceptions import ExtractionError


def test_extract_text_from_plain_utf8():
    """Test extracting text from UTF-8 plain text file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Hello, world!\nThis is a test.")
        temp_path = Path(f.name)

    try:
        text, metadata = extract_text_from_plain(temp_path)

        assert "Hello, world!" in text
        assert "This is a test." in text
        assert isinstance(metadata, ExtractionMetadata)
        assert metadata.extraction_method == "plain_text"
        assert metadata.word_count > 0
    finally:
        temp_path.unlink()


def test_extract_text_from_plain_empty_file():
    """Test extracting text from empty file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("")
        temp_path = Path(f.name)

    try:
        text, metadata = extract_text_from_plain(temp_path)

        assert text == ""
        assert metadata.word_count == 0
    finally:
        temp_path.unlink()


def test_extract_text_from_plain_multiline():
    """Test extracting multiline text."""
    content = """Line 1
Line 2
Line 3
With multiple words here"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)

    try:
        text, metadata = extract_text_from_plain(temp_path)

        assert "Line 1" in text
        assert "Line 2" in text
        assert "Line 3" in text
        assert metadata.word_count >= 8
    finally:
        temp_path.unlink()


def test_extraction_metadata_structure():
    """Test ExtractionMetadata structure."""
    metadata = ExtractionMetadata(
        extraction_method="test_method",
        page_count=5,
        word_count=100,
        character_count=500,
    )

    assert metadata.extraction_method == "test_method"
    assert metadata.page_count == 5
    assert metadata.word_count == 100
    assert metadata.character_count == 500
    assert metadata.sheet_count is None
    assert metadata.slide_count is None
