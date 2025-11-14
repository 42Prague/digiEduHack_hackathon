"""Tests for pipeline orchestration."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from eduscale.tabular.pipeline import (
    FrontmatterData,
    IngestResult,
    process_tabular_text,
)


@pytest.fixture
def sample_csv_with_frontmatter():
    """Sample CSV text with frontmatter."""
    return """---
file_id: "test-file-123"
region_id: "region-cz-01"
text_uri: "gs://bucket/text/test-file-123.txt"
event_id: "event-456"
file_category: "csv"

original:
  filename: "data.csv"
  content_type: "text/csv"
  size_bytes: 1234
  bucket: "bucket-name"
  object_path: "uploads/region/test-file-123.csv"
  uploaded_at: "2025-01-14T10:30:00Z"

extraction:
  method: "csv_parser"
  timestamp: "2025-01-14T10:31:00Z"
  success: true
  duration_ms: 100

content:
  text_length: 500
  word_count: 80
  character_count: 500
---
student_id,student_name,test_score,date
S001,John Doe,85,2025-01-10
S002,Jane Smith,92,2025-01-10
S003,Bob Johnson,78,2025-01-10
"""


@pytest.fixture
def sample_pdf_with_frontmatter():
    """Sample PDF text with frontmatter."""
    return """---
file_id: "test-file-456"
region_id: "region-cz-01"
text_uri: "gs://bucket/text/test-file-456.txt"
event_id: "event-789"
file_category: "pdf"

original:
  filename: "document.pdf"
  content_type: "application/pdf"
  size_bytes: 123456
  bucket: "bucket-name"
  object_path: "uploads/region/test-file-456.pdf"
  uploaded_at: "2025-01-14T11:00:00Z"

extraction:
  method: "pdfplumber"
  timestamp: "2025-01-14T11:01:00Z"
  success: true
  duration_ms: 2000

content:
  text_length: 5000
  word_count: 800
  character_count: 5000

document:
  page_count: 10
---
This is a sample PDF document about education.
Teacher Petrova teaches mathematics very well.
Student Novak shows great progress.
"""


@patch("eduscale.tabular.pipeline.load_concepts_catalog")
@patch("eduscale.tabular.pipeline.classify_table")
@patch("eduscale.tabular.pipeline.map_columns")
def test_process_tabular_text_csv(
    mock_map_columns,
    mock_classify_table,
    mock_load_concepts,
    sample_csv_with_frontmatter,
):
    """Test processing CSV text through tabular pipeline."""
    # Mock catalog
    mock_catalog = MagicMock()
    mock_load_concepts.return_value = mock_catalog

    # Mock classification
    mock_classify_table.return_value = ("ASSESSMENT", 0.85)

    # Mock column mappings
    mock_mapping = MagicMock()
    mock_mapping.status = "AUTO"
    mock_mapping.concept_key = "student_id"
    mock_map_columns.return_value = [mock_mapping, mock_mapping, mock_mapping]

    # Process text
    result = process_tabular_text(sample_csv_with_frontmatter)

    # Verify result
    assert isinstance(result, IngestResult)
    assert result.file_id == "test-file-123"
    assert result.status == "INGESTED"
    assert result.table_type == "ASSESSMENT"
    assert result.rows_loaded == 3
    assert result.error_message is None
    assert result.processing_time_ms > 0


@patch("eduscale.tabular.analysis.entity_resolver.load_entity_cache")
@patch("eduscale.tabular.pipeline.process_free_form_text")
def test_process_tabular_text_pdf(
    mock_process_free_form,
    mock_load_cache,
    sample_pdf_with_frontmatter,
):
    """Test processing PDF text through free-form pipeline."""
    # Mock entity cache
    mock_cache = MagicMock()
    mock_load_cache.return_value = mock_cache

    # Mock free-form processing
    mock_observation = MagicMock()
    mock_observation.sentiment_score = 0.75
    mock_process_free_form.return_value = (mock_observation, [])

    # Process text
    result = process_tabular_text(sample_pdf_with_frontmatter)

    # Verify result
    assert isinstance(result, IngestResult)
    assert result.file_id == "test-file-456"
    assert result.status == "INGESTED"
    assert result.table_type == "FREE_FORM"
    assert result.rows_loaded == 1
    assert result.error_message is None
    assert result.processing_time_ms >= 0  # May be 0 for mocked operations


def test_process_tabular_text_no_frontmatter():
    """Test processing text without frontmatter."""
    text_content = "student_id,name,score\nS001,John,85"

    result = process_tabular_text(text_content)

    # Should fail with no frontmatter
    assert result.status == "FAILED"
    assert "No frontmatter found" in result.error_message


@patch("eduscale.tabular.pipeline.load_concepts_catalog")
@patch("eduscale.tabular.pipeline.classify_table")
def test_process_tabular_text_low_confidence(
    mock_classify_table,
    mock_load_concepts,
    sample_csv_with_frontmatter,
):
    """Test processing with low classification confidence routes to FREE_FORM."""
    # Mock catalog
    mock_catalog = MagicMock()
    mock_load_concepts.return_value = mock_catalog

    # Mock low confidence classification
    mock_classify_table.return_value = ("MIXED", 0.3)

    # Mock free-form processing
    with patch("eduscale.tabular.analysis.entity_resolver.load_entity_cache") as mock_cache:
        with patch("eduscale.tabular.pipeline.process_free_form_text") as mock_process:
            mock_cache.return_value = MagicMock()
            mock_observation = MagicMock()
            mock_observation.sentiment_score = 0.0
            mock_process.return_value = (mock_observation, [])

            # Process text
            result = process_tabular_text(sample_csv_with_frontmatter)

            # Should route to FREE_FORM
            assert result.status == "INGESTED"
            assert result.table_type == "FREE_FORM"
            assert len(result.warnings) > 0
            assert "Low classification confidence" in result.warnings[0]


@patch("eduscale.tabular.pipeline.load_dataframe_from_text")
def test_process_tabular_text_error_handling(
    mock_load_df,
    sample_csv_with_frontmatter,
):
    """Test error handling in pipeline."""
    # Mock DataFrame loading to raise error
    mock_load_df.side_effect = ValueError("Invalid CSV format")

    # Process text
    result = process_tabular_text(sample_csv_with_frontmatter)

    # Should return FAILED status
    assert result.status == "FAILED"
    assert "ValueError: Invalid CSV format" in result.error_message
    assert result.processing_time_ms >= 0  # May be 0 for very fast failures
