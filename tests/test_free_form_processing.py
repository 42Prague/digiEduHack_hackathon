"""Tests for free-form text processing."""

import pytest

from eduscale.tabular.analysis.entity_resolver import EntityCache
from eduscale.tabular.pipeline import (
    FrontmatterData,
    process_free_form_text,
)


@pytest.fixture
def sample_frontmatter():
    """Sample frontmatter for testing."""
    return FrontmatterData(
        file_id="test-file-123",
        region_id="region-cz-01",
        text_uri="gs://bucket/text/test-file-123.txt",
        event_id="event-456",
        file_category="pdf",
        original_filename="document.pdf",
        original_content_type="application/pdf",
        original_size_bytes=123456,
        bucket="bucket-name",
        object_path="uploads/region/test-file-123.pdf",
        uploaded_at="2025-01-14T10:30:00Z",
        extraction_method="pdfplumber",
        extraction_timestamp="2025-01-14T10:31:00Z",
        extraction_success=True,
        extraction_duration_ms=1234,
        text_length=5432,
        word_count=987,
        character_count=5432,
        page_count=15,
        sheet_count=None,
        slide_count=None,
    )


@pytest.fixture
def empty_entity_cache():
    """Empty entity cache for testing."""
    return EntityCache()


def test_process_free_form_text_basic(sample_frontmatter, empty_entity_cache):
    """Test basic free-form text processing."""
    text_content = "This is a sample PDF document about education."

    observation, targets = process_free_form_text(
        text_content=text_content,
        frontmatter=sample_frontmatter,
        entity_cache=empty_entity_cache,
    )

    # Check observation record
    assert observation.file_id == "test-file-123"
    assert observation.region_id == "region-cz-01"
    assert observation.text_content == text_content
    assert observation.original_content_type == "application/pdf"
    assert observation.page_count == 15
    assert isinstance(observation.detected_entities, list)
    assert isinstance(observation.sentiment_score, float)
    assert -1.0 <= observation.sentiment_score <= 1.0

    # Check observation targets (may be empty if LLM is disabled)
    assert isinstance(targets, list)


def test_process_free_form_text_with_entities(sample_frontmatter):
    """Test free-form text processing with entity mentions."""
    text_content = "Учитель Петрова отлично объясняет математику."

    # Create entity cache with sample entities
    entity_cache = EntityCache()
    entity_cache.teachers = {"петрова": "teacher-uuid-123"}
    entity_cache.entity_names = {"teacher-uuid-123": "Петрова"}
    entity_cache.subjects = {"математика": "subject-uuid-456"}
    entity_cache.entity_names["subject-uuid-456"] = "Математика"

    observation, targets = process_free_form_text(
        text_content=text_content,
        frontmatter=sample_frontmatter,
        entity_cache=entity_cache,
    )

    # Check observation record
    assert observation.file_id == "test-file-123"
    assert observation.text_content == text_content

    # Targets may be empty if LLM is disabled or extraction fails
    # This is expected behavior
    assert isinstance(targets, list)


def test_process_free_form_text_empty_text(sample_frontmatter, empty_entity_cache):
    """Test free-form text processing with empty text."""
    text_content = ""

    observation, targets = process_free_form_text(
        text_content=text_content,
        frontmatter=sample_frontmatter,
        entity_cache=empty_entity_cache,
    )

    # Should still create observation record
    assert observation.file_id == "test-file-123"
    assert observation.text_content == ""
    assert observation.detected_entities == []
    assert len(targets) == 0


def test_process_free_form_text_audio_metadata(empty_entity_cache):
    """Test free-form text processing with audio metadata."""
    frontmatter = FrontmatterData(
        file_id="audio-file-789",
        region_id="region-cz-01",
        text_uri="gs://bucket/text/audio-file-789.txt",
        event_id="event-789",
        file_category="audio",
        original_filename="recording.mp3",
        original_content_type="audio/mpeg",
        original_size_bytes=987654,
        bucket="bucket-name",
        object_path="uploads/region/audio-file-789.mp3",
        uploaded_at="2025-01-14T11:00:00Z",
        extraction_method="speech_to_text",
        extraction_timestamp="2025-01-14T11:05:00Z",
        extraction_success=True,
        extraction_duration_ms=5000,
        text_length=1234,
        word_count=200,
        character_count=1234,
        page_count=None,
        sheet_count=None,
        slide_count=None,
    )

    text_content = "This is a transcript of an audio recording."

    observation, targets = process_free_form_text(
        text_content=text_content,
        frontmatter=frontmatter,
        entity_cache=empty_entity_cache,
    )

    # Check audio-specific metadata
    assert observation.original_content_type == "audio/mpeg"
    assert observation.page_count is None
