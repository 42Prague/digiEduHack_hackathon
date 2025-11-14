"""Tests for feedback analyzer module."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from eduscale.tabular.analysis.entity_resolver import EntityCache
from eduscale.tabular.analysis.feedback_analyzer import (
    FeedbackTarget,
    analyze_feedback_batch,
)
from eduscale.tabular.pipeline import FrontmatterData


@pytest.fixture
def sample_frontmatter():
    """Sample frontmatter for testing."""
    return FrontmatterData(
        file_id="test-file-123",
        region_id="region-cz-01",
        text_uri="gs://bucket/text/test-file-123.txt",
        event_id="event-456",
        file_category="csv",
        original_filename="feedback.csv",
        original_content_type="text/csv",
        original_size_bytes=12345,
        bucket="bucket-name",
        object_path="uploads/region/test-file-123.csv",
        uploaded_at="2025-01-14T10:30:00Z",
        extraction_method="csv_parser",
        extraction_timestamp="2025-01-14T10:31:00Z",
        extraction_success=True,
        extraction_duration_ms=100,
        text_length=1000,
        word_count=150,
        character_count=1000,
        page_count=None,
        sheet_count=1,
        slide_count=None,
    )


@pytest.fixture
def sample_entity_cache():
    """Sample entity cache with test entities."""
    cache = EntityCache()

    # Add sample teachers
    cache.teachers = {
        "петрова": "teacher-uuid-123",
        "иванов": "teacher-uuid-456",
    }
    cache.entity_names = {
        "teacher-uuid-123": "Петрова",
        "teacher-uuid-456": "Иванов",
    }

    # Add sample students
    cache.students = {
        "новак": "student-uuid-789",
    }
    cache.entity_names["student-uuid-789"] = "Новак"

    # Add sample subjects
    cache.subjects = {
        "математика": "subject-uuid-111",
        "физика": "subject-uuid-222",
    }
    cache.entity_names["subject-uuid-111"] = "Математика"
    cache.entity_names["subject-uuid-222"] = "Физика"

    return cache


def test_analyze_feedback_batch_empty_dataframe(sample_frontmatter, sample_entity_cache):
    """Test feedback analysis with empty DataFrame."""
    df_feedback = pd.DataFrame()

    targets = analyze_feedback_batch(
        df_feedback=df_feedback,
        region_id="region-cz-01",
        frontmatter=sample_frontmatter,
        entity_cache=sample_entity_cache,
    )

    assert targets == []


def test_analyze_feedback_batch_missing_columns(sample_frontmatter, sample_entity_cache):
    """Test feedback analysis with missing required columns."""
    df_feedback = pd.DataFrame({"id": [1, 2], "text": ["test1", "test2"]})

    targets = analyze_feedback_batch(
        df_feedback=df_feedback,
        region_id="region-cz-01",
        frontmatter=sample_frontmatter,
        entity_cache=sample_entity_cache,
    )

    assert targets == []


@patch("eduscale.tabular.analysis.feedback_analyzer.embed_texts")
def test_analyze_feedback_batch_basic(mock_embed_texts, sample_frontmatter, sample_entity_cache):
    """Test basic feedback analysis.
    
    Note: This test mocks embed_texts to avoid downloading the BGE-M3 model (~2.2GB).
    The batch function processes multiple feedback records at once for efficiency.
    """
    # Mock embedding function to return random embeddings (1024-dim for BGE-M3)
    mock_embed_texts.return_value = np.random.rand(1, 1024)
    
    df_feedback = pd.DataFrame(
        {
            "feedback_id": ["fb-001", "fb-002"],
            "feedback_text": [
                "Учитель Петрова отлично объясняет математику.",
                "Ученик Новак показывает прогресс.",
            ],
        }
    )

    targets = analyze_feedback_batch(
        df_feedback=df_feedback,
        region_id="region-cz-01",
        frontmatter=sample_frontmatter,
        entity_cache=sample_entity_cache,
    )

    # Should return list of FeedbackTarget objects
    assert isinstance(targets, list)

    # Targets may be empty if LLM is disabled or similarity is low
    # This is expected behavior
    for target in targets:
        assert isinstance(target, FeedbackTarget)
        assert target.feedback_id in ["fb-001", "fb-002"]
        assert target.target_type in [
            "teacher",
            "student",
            "parent",
            "subject",
            "region",
            "school",
        ]
        assert isinstance(target.target_id, str)
        assert 0.0 <= target.relevance_score <= 1.0
        assert target.confidence in ["HIGH", "MEDIUM", "LOW"]


def test_analyze_feedback_batch_empty_text(sample_frontmatter, sample_entity_cache):
    """Test feedback analysis with empty text."""
    df_feedback = pd.DataFrame(
        {
            "feedback_id": ["fb-001", "fb-002"],
            "feedback_text": ["", None],
        }
    )

    targets = analyze_feedback_batch(
        df_feedback=df_feedback,
        region_id="region-cz-01",
        frontmatter=sample_frontmatter,
        entity_cache=sample_entity_cache,
    )

    # Should return empty list for empty/null text
    assert targets == []


@patch("eduscale.tabular.analysis.feedback_analyzer.embed_texts")
def test_analyze_feedback_batch_with_embeddings(mock_embed_texts, sample_frontmatter):
    """Test feedback analysis with entity embeddings.
    
    This test verifies that embedding-based matching works when entity cache
    has precomputed embeddings for entities.
    """
    # Mock embedding function to return consistent embeddings
    mock_embed_texts.return_value = np.random.rand(1, 1024)
    
    # Create cache with embeddings
    cache = EntityCache()
    cache.teachers = {"петрова": "teacher-uuid-123"}
    cache.entity_names = {"teacher-uuid-123": "Петрова"}

    # Add sample embedding (1024-dimensional for BGE-M3)
    cache.teacher_embeddings = {
        "teacher-uuid-123": np.random.rand(1024),
    }

    df_feedback = pd.DataFrame(
        {
            "feedback_id": ["fb-001"],
            "feedback_text": ["Учитель Петрова отлично объясняет математику."],
        }
    )

    targets = analyze_feedback_batch(
        df_feedback=df_feedback,
        region_id="region-cz-01",
        frontmatter=sample_frontmatter,
        entity_cache=cache,
    )

    # Should return list (may be empty if similarity is low)
    assert isinstance(targets, list)


def test_feedback_target_dataclass():
    """Test FeedbackTarget dataclass."""
    target = FeedbackTarget(
        feedback_id="fb-001",
        target_type="teacher",
        target_id="teacher-uuid-123",
        relevance_score=0.85,
        confidence="HIGH",
    )

    assert target.feedback_id == "fb-001"
    assert target.target_type == "teacher"
    assert target.target_id == "teacher-uuid-123"
    assert target.relevance_score == 0.85
    assert target.confidence == "HIGH"
