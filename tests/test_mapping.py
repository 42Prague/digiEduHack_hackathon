"""Tests for AI column mapping."""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch

from eduscale.tabular.mapping import (
    ColumnMapping,
    map_columns,
    _infer_column_type,
    _adjust_score_by_type,
    _build_column_description,
)
from eduscale.tabular.concepts import load_concepts_catalog


@pytest.fixture
def mock_embed_texts():
    """Mock embed_texts to avoid downloading model."""
    def _mock_embed(texts):
        # Return deterministic fake embeddings based on text content
        embeddings = []
        for text in texts:
            text_lower = text.lower()
            # Create embeddings that match well with expected concepts
            if "student_id" in text_lower or "student id" in text_lower:
                emb = np.array([0.9, 0.1, 0.0] + [0.0] * 1021)
            elif "test_score" in text_lower or "score" in text_lower:
                emb = np.array([0.1, 0.9, 0.0] + [0.0] * 1021)
            elif "date" in text_lower:
                emb = np.array([0.0, 0.1, 0.9] + [0.0] * 1021)
            else:
                # Random/unknown column
                emb = np.array([0.3, 0.3, 0.3] + [0.0] * 1021)
            embeddings.append(emb)
        return np.array(embeddings)
    
    # Patch both in mapping and concepts modules
    with patch('eduscale.tabular.mapping.embed_texts', side_effect=_mock_embed), \
         patch('eduscale.tabular.concepts.embed_texts', side_effect=_mock_embed):
        yield


@pytest.fixture
def catalog(mock_embed_texts):
    """Load test concepts catalog with mocked embeddings."""
    return load_concepts_catalog("tests/fixtures/concepts_test.yaml")


def test_map_columns_basic(catalog):
    """Test basic column mapping."""
    df = pd.DataFrame({
        "student_id": ["S001", "S002", "S003"],
        "test_score": [85, 92, 78],
        "date": ["2025-01-10", "2025-01-10", "2025-01-10"],
    })

    mappings = map_columns(df, "ASSESSMENT", catalog)

    assert len(mappings) == 3

    # Check that mappings were created
    for mapping in mappings:
        assert isinstance(mapping, ColumnMapping)
        assert mapping.source_column in df.columns
        assert mapping.status in ["AUTO", "LOW_CONFIDENCE", "UNKNOWN"]
        assert 0.0 <= mapping.score <= 1.0
        assert len(mapping.candidates) <= 3


def test_map_columns_empty_dataframe(catalog):
    """Test mapping with empty DataFrame."""
    df = pd.DataFrame()

    mappings = map_columns(df, "ASSESSMENT", catalog)

    assert mappings == []


def test_infer_column_type_numeric():
    """Test type inference for numeric columns."""
    series = pd.Series([1, 2, 3, 4, 5])
    assert _infer_column_type(series) == "number"

    series = pd.Series([1.5, 2.7, 3.2])
    assert _infer_column_type(series) == "number"


def test_infer_column_type_date():
    """Test type inference for date columns."""
    series = pd.Series(["2025-01-10", "2025-01-11", "2025-01-12"])
    assert _infer_column_type(series) == "date"

    series = pd.Series(pd.to_datetime(["2025-01-10", "2025-01-11"]))
    assert _infer_column_type(series) == "date"


def test_infer_column_type_categorical():
    """Test type inference for categorical columns."""
    # Low cardinality -> categorical
    series = pd.Series(["A", "B", "A", "B", "A", "B", "A", "B", "A", "B"] * 10)
    assert _infer_column_type(series) == "categorical"


def test_infer_column_type_string():
    """Test type inference for string columns."""
    # High cardinality -> string
    series = pd.Series([f"Name_{i}" for i in range(100)])
    assert _infer_column_type(series) == "string"


def test_adjust_score_by_type_match():
    """Test score adjustment for type matches."""
    # Number match
    score = _adjust_score_by_type(0.7, "number", "number")
    assert abs(score - 0.8) < 0.001  # 0.7 + 0.1

    # Date match
    score = _adjust_score_by_type(0.7, "date", "date")
    assert abs(score - 0.8) < 0.001  # 0.7 + 0.1

    # String match
    score = _adjust_score_by_type(0.7, "string", "string")
    assert abs(score - 0.75) < 0.001  # 0.7 + 0.05


def test_adjust_score_by_type_mismatch():
    """Test score adjustment for type mismatches."""
    # Type mismatch penalty
    score = _adjust_score_by_type(0.7, "number", "string")
    assert abs(score - 0.55) < 0.001  # 0.7 - 0.15

    score = _adjust_score_by_type(0.7, "date", "number")
    assert abs(score - 0.55) < 0.001  # 0.7 - 0.15


def test_adjust_score_bounds():
    """Test that adjusted scores stay within [0, 1]."""
    # Should not exceed 1.0
    score = _adjust_score_by_type(0.95, "number", "number")
    assert score <= 1.0

    # Should not go below 0.0
    score = _adjust_score_by_type(0.1, "number", "string")
    assert score >= 0.0


def test_build_column_description():
    """Test column description building."""
    df = pd.DataFrame({
        "student_id": ["S001", "S002", "S003", "S004", "S005"],
    })

    description = _build_column_description(df, "student_id", max_samples=3)

    assert "student_id" in description
    assert "S001" in description
    assert "S002" in description
    assert "S003" in description
    # S004 and S005 should not be included (max_samples=3)


def test_build_column_description_with_nulls():
    """Test column description with null values."""
    df = pd.DataFrame({
        "test_score": [85, None, 92, None, 78],
    })

    description = _build_column_description(df, "test_score", max_samples=5)

    # Should skip nulls
    assert "85" in description
    assert "92" in description
    assert "78" in description
    assert "None" not in description


def test_mapping_status_thresholds(catalog):
    """Test that mapping status is assigned correctly based on score thresholds."""
    df = pd.DataFrame({
        "student_id": ["S001", "S002"],  # Should map well to student_id concept
        "random_xyz": ["abc", "def"],  # Should have low score
    })

    mappings = map_columns(df, "ASSESSMENT", catalog)

    # student_id should have high confidence
    student_id_mapping = next(m for m in mappings if m.source_column == "student_id")
    assert student_id_mapping.status in ["AUTO", "LOW_CONFIDENCE"]

    # random_xyz might be UNKNOWN or LOW_CONFIDENCE
    random_mapping = next(m for m in mappings if m.source_column == "random_xyz")
    assert random_mapping.status in ["LOW_CONFIDENCE", "UNKNOWN"]
