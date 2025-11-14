"""Tests for frontmatter parsing."""

import pytest

from eduscale.tabular.pipeline import FrontmatterData, parse_frontmatter


def test_parse_frontmatter_with_valid_yaml():
    """Test parsing valid YAML frontmatter."""
    with open("tests/fixtures/sample_text_csv.txt", "r") as f:
        text_content = f.read()

    frontmatter, clean_text = parse_frontmatter(text_content)

    assert frontmatter is not None
    assert isinstance(frontmatter, FrontmatterData)

    # Check top-level fields
    assert frontmatter.file_id == "sample-csv-001"  # Updated to match new fixture
    assert frontmatter.region_id == "region-cz-01"
    assert frontmatter.text_uri == "gs://test-bucket/text/sample-csv-001.txt"  # Updated
    assert frontmatter.event_id == "event-csv-001"  # Updated
    assert frontmatter.file_category == "csv"

    # Check original section
    assert frontmatter.original_filename == "assessment_data.csv"  # Updated to match new fixture
    assert frontmatter.original_content_type == "text/csv"
    assert frontmatter.original_size_bytes == 1234  # Updated to match new fixture
    assert frontmatter.bucket == "test-bucket"
    assert frontmatter.object_path == "uploads/region-cz-01/sample-csv-001_assessment_data.csv"  # Updated
    assert frontmatter.uploaded_at == "2025-01-14T10:30:00Z"

    # Check extraction section
    assert frontmatter.extraction_method == "csv_parser"  # Updated to match new fixture
    assert frontmatter.extraction_timestamp == "2025-01-14T10:30:10Z"  # Updated to match new fixture
    assert frontmatter.extraction_success is True
    assert frontmatter.extraction_duration_ms == 50

    # Check content section
    assert frontmatter.text_length == 500
    assert frontmatter.word_count == 80  # Updated to match new fixture
    assert frontmatter.character_count == 500

    # Check document section
    assert frontmatter.page_count is None
    assert frontmatter.sheet_count is None  # Updated to match new fixture (CSV doesn't have sheets)
    assert frontmatter.slide_count is None

    # Check clean text
    assert clean_text.startswith("student_id,student_name,test_score,date")
    assert "S001,Jan Novák,85,2025-01-10" in clean_text
    assert "---" not in clean_text


def test_parse_frontmatter_no_frontmatter():
    """Test parsing text without frontmatter."""
    text_content = "student_id,student_name,test_score\nS001,Jan Novák,85"

    frontmatter, clean_text = parse_frontmatter(text_content)

    assert frontmatter is None
    assert clean_text == text_content


def test_parse_frontmatter_malformed_yaml():
    """Test parsing with malformed YAML."""
    text_content = """---
file_id: "test-123"
region_id: [invalid yaml structure
---
Some text content
"""

    frontmatter, clean_text = parse_frontmatter(text_content)

    # Should return None and original text on parse error
    assert frontmatter is None
    assert clean_text == text_content


def test_parse_frontmatter_missing_closing_delimiter():
    """Test parsing with missing closing delimiter."""
    text_content = """---
file_id: "test-123"
region_id: "region-01"
Some text without closing delimiter
"""

    frontmatter, clean_text = parse_frontmatter(text_content)

    assert frontmatter is None
    assert clean_text == text_content


def test_parse_frontmatter_missing_nested_sections():
    """Test parsing with missing nested sections."""
    text_content = """---
file_id: "test-123"
region_id: "region-01"
text_uri: "gs://bucket/text/test-123.txt"
---
Some text content
"""

    frontmatter, clean_text = parse_frontmatter(text_content)

    assert frontmatter is not None
    assert frontmatter.file_id == "test-123"
    assert frontmatter.region_id == "region-01"

    # Missing nested sections should be None
    assert frontmatter.original_filename is None
    assert frontmatter.extraction_method is None
    assert frontmatter.text_length is None
    assert frontmatter.page_count is None

    assert clean_text == "Some text content"


def test_parse_frontmatter_partial_nested_sections():
    """Test parsing with partial nested sections."""
    text_content = """---
file_id: "test-123"
region_id: "region-01"
text_uri: "gs://bucket/text/test-123.txt"

original:
  filename: "doc.pdf"
  content_type: "application/pdf"

extraction:
  method: "pdfplumber"
---
PDF text content here
"""

    frontmatter, clean_text = parse_frontmatter(text_content)

    assert frontmatter is not None
    assert frontmatter.original_filename == "doc.pdf"
    assert frontmatter.original_content_type == "application/pdf"
    assert frontmatter.original_size_bytes is None  # Not provided

    assert frontmatter.extraction_method == "pdfplumber"
    assert frontmatter.extraction_timestamp is None  # Not provided

    assert clean_text == "PDF text content here"


def test_parse_frontmatter_empty_text():
    """Test parsing with empty text after frontmatter."""
    text_content = """---
file_id: "test-123"
region_id: "region-01"
text_uri: "gs://bucket/text/test-123.txt"
---
"""

    frontmatter, clean_text = parse_frontmatter(text_content)

    assert frontmatter is not None
    assert frontmatter.file_id == "test-123"
    assert clean_text == ""
