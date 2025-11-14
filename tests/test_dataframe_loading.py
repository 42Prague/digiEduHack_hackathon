"""Tests for DataFrame loading from text."""

import pytest
import pandas as pd

from eduscale.tabular.pipeline import (
    FrontmatterData,
    load_dataframe_from_text,
    parse_frontmatter,
    _to_snake_case,
)


def test_load_dataframe_from_csv():
    """Test loading DataFrame from CSV text."""
    with open("tests/fixtures/sample_text_csv.txt", "r") as f:
        text_content = f.read()

    frontmatter, clean_text = parse_frontmatter(text_content)
    assert frontmatter is not None

    df = load_dataframe_from_text(clean_text, frontmatter)

    assert len(df) == 5  # Updated to match new fixture
    assert "student_id" in df.columns
    assert "student_name" in df.columns
    assert "test_score" in df.columns
    assert "date" in df.columns

    # Check data
    assert df["student_id"].iloc[0] == "S001"
    assert df["student_name"].iloc[0] == "Jan Novák"
    assert df["test_score"].iloc[0] == 85


def test_load_dataframe_from_json():
    """Test loading DataFrame from JSON text."""
    with open("tests/fixtures/sample_text_json.txt", "r") as f:
        text_content = f.read()

    frontmatter, clean_text = parse_frontmatter(text_content)
    assert frontmatter is not None

    df = load_dataframe_from_text(clean_text, frontmatter)

    assert len(df) == 3
    assert "feedback_id" in df.columns  # Updated to match new fixture
    assert "feedback_text" in df.columns  # Updated to match new fixture
    assert "author_type" in df.columns  # Updated to match new fixture

    # Check data
    assert df["feedback_id"].iloc[0] == "FB001"  # Updated to match new fixture
    assert df["author_type"].iloc[2] == "teacher"  # Updated to match new fixture


def test_load_dataframe_from_tsv():
    """Test loading DataFrame from TSV text."""
    with open("tests/fixtures/sample_text_tsv.txt", "r") as f:
        text_content = f.read()

    frontmatter, clean_text = parse_frontmatter(text_content)
    assert frontmatter is not None

    df = load_dataframe_from_text(clean_text, frontmatter)

    assert len(df) == 2
    assert "student_id" in df.columns
    assert "student_name" in df.columns


def test_column_name_normalization():
    """Test that column names are normalized to snake_case."""
    text_content = "Student ID,Student Name,Test Score\nS001,Jan,85"

    frontmatter = FrontmatterData(
        file_id="test",
        region_id="region-01",
        text_uri="gs://bucket/test.txt",
        event_id=None,
        file_category=None,
        original_filename="test.csv",
        original_content_type="text/csv",
        original_size_bytes=None,
        bucket=None,
        object_path=None,
        uploaded_at=None,
        extraction_method=None,
        extraction_timestamp=None,
        extraction_success=None,
        extraction_duration_ms=None,
        text_length=None,
        word_count=None,
        character_count=None,
        page_count=None,
        sheet_count=None,
        slide_count=None,
    )

    df = load_dataframe_from_text(text_content, frontmatter)

    # Check normalized column names
    assert "student_id" in df.columns
    assert "student_name" in df.columns
    assert "test_score" in df.columns


def test_row_limit_enforcement():
    """Test that row limit is enforced."""
    # Create CSV with many rows
    rows = ["student_id,test_score"]
    for i in range(250000):  # Exceeds INGEST_MAX_ROWS (200000)
        rows.append(f"S{i:06d},{i % 100}")

    text_content = "\n".join(rows)

    frontmatter = FrontmatterData(
        file_id="test",
        region_id="region-01",
        text_uri="gs://bucket/test.txt",
        event_id=None,
        file_category=None,
        original_filename="test.csv",
        original_content_type="text/csv",
        original_size_bytes=None,
        bucket=None,
        object_path=None,
        uploaded_at=None,
        extraction_method=None,
        extraction_timestamp=None,
        extraction_success=None,
        extraction_duration_ms=None,
        text_length=None,
        word_count=None,
        character_count=None,
        page_count=None,
        sheet_count=None,
        slide_count=None,
    )

    with pytest.raises(ValueError, match="exceeds maximum rows"):
        load_dataframe_from_text(text_content, frontmatter)


def test_empty_columns_dropped():
    """Test that empty columns are dropped."""
    text_content = "student_id,empty_col,test_score\nS001,,85\nS002,,92"

    frontmatter = FrontmatterData(
        file_id="test",
        region_id="region-01",
        text_uri="gs://bucket/test.txt",
        event_id=None,
        file_category=None,
        original_filename="test.csv",
        original_content_type="text/csv",
        original_size_bytes=None,
        bucket=None,
        object_path=None,
        uploaded_at=None,
        extraction_method=None,
        extraction_timestamp=None,
        extraction_success=None,
        extraction_duration_ms=None,
        text_length=None,
        word_count=None,
        character_count=None,
        page_count=None,
        sheet_count=None,
        slide_count=None,
    )

    df = load_dataframe_from_text(text_content, frontmatter)

    # empty_col should be dropped
    assert "empty_col" not in df.columns
    assert "student_id" in df.columns
    assert "test_score" in df.columns


def test_to_snake_case():
    """Test snake_case conversion."""
    assert _to_snake_case("Student ID") == "student_id"
    assert _to_snake_case("StudentID") == "student_id"
    assert _to_snake_case("student-id") == "student_id"
    assert _to_snake_case("Test Score") == "test_score"
    assert _to_snake_case("testScore") == "test_score"
    assert _to_snake_case("TEST_SCORE") == "test_score"
    assert _to_snake_case("  Student  ID  ") == "student_id"


def test_jsonl_format():
    """Test loading JSONL (line-delimited JSON)."""
    text_content = """{"student_id": "S001", "test_score": 85}
{"student_id": "S002", "test_score": 92}
{"student_id": "S003", "test_score": 78}"""

    frontmatter = FrontmatterData(
        file_id="test",
        region_id="region-01",
        text_uri="gs://bucket/test.txt",
        event_id=None,
        file_category=None,
        original_filename="test.jsonl",
        original_content_type="application/json",
        original_size_bytes=None,
        bucket=None,
        object_path=None,
        uploaded_at=None,
        extraction_method=None,
        extraction_timestamp=None,
        extraction_success=None,
        extraction_duration_ms=None,
        text_length=None,
        word_count=None,
        character_count=None,
        page_count=None,
        sheet_count=None,
        slide_count=None,
    )

    df = load_dataframe_from_text(text_content, frontmatter)

    assert len(df) == 3
    assert "student_id" in df.columns
    assert "test_score" in df.columns
