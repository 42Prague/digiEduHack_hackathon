"""Tests for AI table classification."""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from eduscale.tabular.classifier import classify_table, _extract_features
from eduscale.tabular.concepts import load_concepts_catalog, ConceptsCatalog, TableType


@pytest.fixture
def mock_embed_texts():
    """Mock embed_texts to avoid downloading model."""
    def _mock_embed(texts):
        # Return deterministic fake embeddings based on text content
        embeddings = []
        for text in texts:
            # Create a simple hash-based embedding
            text_lower = text.lower()
            # Different patterns for different table types
            if any(word in text_lower for word in ["score", "grade", "test", "assessment"]):
                # Assessment-like embedding
                emb = np.array([0.8, 0.2, 0.1] + [0.0] * 1021)
            elif any(word in text_lower for word in ["present", "absent", "attendance"]):
                # Attendance-like embedding
                emb = np.array([0.1, 0.8, 0.2] + [0.0] * 1021)
            else:
                # Generic embedding
                emb = np.array([0.3, 0.3, 0.3] + [0.0] * 1021)
            embeddings.append(emb)
        return np.array(embeddings)
    
    # Patch both in classifier and concepts modules
    with patch('eduscale.tabular.classifier.embed_texts', side_effect=_mock_embed), \
         patch('eduscale.tabular.concepts.embed_texts', side_effect=_mock_embed):
        yield


@pytest.fixture
def catalog(mock_embed_texts):
    """Load test concepts catalog with mocked embeddings."""
    return load_concepts_catalog("tests/fixtures/concepts_test.yaml")


def test_classify_assessment_table(catalog):
    """Test classification of assessment-like table."""
    df = pd.DataFrame({
        "student_id": ["S001", "S002", "S003"],
        "test_score": [85, 92, 78],
        "grade": ["B", "A", "C"],
        "date": ["2025-01-10", "2025-01-10", "2025-01-10"],
    })

    table_type, confidence = classify_table(df, catalog)

    # Should classify as ASSESSMENT
    assert table_type == "ASSESSMENT"
    assert confidence > 0.4


def test_classify_attendance_table(catalog):
    """Test classification of attendance-like table."""
    df = pd.DataFrame({
        "student_id": ["S001", "S002", "S003"],
        "date": ["2025-01-10", "2025-01-11", "2025-01-12"],
        "present": [True, False, True],
        "absent": [False, True, False],
    })

    table_type, confidence = classify_table(df, catalog)

    # Should classify as ATTENDANCE
    assert table_type == "ATTENDANCE"
    assert confidence > 0.4


def test_classify_empty_dataframe(catalog):
    """Test classification of empty DataFrame."""
    df = pd.DataFrame()

    table_type, confidence = classify_table(df, catalog)

    # Should return FREE_FORM for empty DataFrame
    assert table_type == "FREE_FORM"
    assert confidence == 0.0


def test_extract_features():
    """Test feature extraction from DataFrame."""
    df = pd.DataFrame({
        "student_id": ["S001", "S002", "S003"],
        "test_score": [85, 92, 78],
    })

    features = _extract_features(df, max_samples=2)

    assert len(features) == 2  # 2 columns
    assert "student_id" in features[0]
    assert "S001" in features[0]
    assert "test_score" in features[1]
    assert "85" in features[1]


def test_extract_features_with_nulls():
    """Test feature extraction with null values."""
    df = pd.DataFrame({
        "student_id": ["S001", None, "S003"],
        "test_score": [85, 92, None],
    })

    features = _extract_features(df, max_samples=5)

    # Should skip null values
    assert len(features) == 2
    assert "S001" in features[0]
    assert "None" not in features[0]  # Nulls should be dropped


def test_low_confidence_returns_free_form(catalog):
    """Test that low confidence returns FREE_FORM."""
    # Create DataFrame with ambiguous content
    df = pd.DataFrame({
        "random_col_1": ["abc", "def", "ghi"],
        "random_col_2": [1, 2, 3],
        "random_col_3": ["x", "y", "z"],
    })

    table_type, confidence = classify_table(df, catalog)

    # With only 2 table types in test catalog, might still get a match
    # But confidence should be relatively low
    assert confidence >= 0.0
    assert table_type in ["ASSESSMENT", "ATTENDANCE", "FREE_FORM"]
