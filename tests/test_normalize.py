"""Tests for data normalization."""

import pandas as pd
import pytest

from eduscale.tabular.normalize import (
    normalize_dataframe,
    _normalize_school_name,
    _pseudonymize_id,
    _cast_column_types,
)
from eduscale.tabular.mapping import ColumnMapping


def test_normalize_dataframe_basic():
    """Test basic DataFrame normalization."""
    df = pd.DataFrame({
        "Student ID": ["S001", "S002"],
        "Test Score": [85, 92],
    })

    mappings = [
        ColumnMapping(
            source_column="Student ID",
            concept_key="student_id",
            score=0.9,
            status="AUTO",
            candidates=[("student_id", 0.9)],
        ),
        ColumnMapping(
            source_column="Test Score",
            concept_key="test_score",
            score=0.85,
            status="AUTO",
            candidates=[("test_score", 0.85)],
        ),
    ]

    df_norm = normalize_dataframe(
        df_raw=df,
        table_type="ASSESSMENT",
        mappings=mappings,
        region_id="region-01",
        file_id="file-123",
    )

    # Check renamed columns
    assert "student_id" in df_norm.columns
    assert "test_score" in df_norm.columns

    # Check metadata columns
    assert "region_id" in df_norm.columns
    assert "file_id" in df_norm.columns
    assert "ingest_timestamp" in df_norm.columns
    assert "source_table_type" in df_norm.columns

    assert df_norm["region_id"].iloc[0] == "region-01"
    assert df_norm["file_id"].iloc[0] == "file-123"
    assert df_norm["source_table_type"].iloc[0] == "ASSESSMENT"


def test_normalize_dataframe_skip_unknown_mappings():
    """Test that UNKNOWN mappings are not renamed."""
    df = pd.DataFrame({
        "known_col": [1, 2],
        "unknown_col": [3, 4],
    })

    mappings = [
        ColumnMapping(
            source_column="known_col",
            concept_key="student_id",
            score=0.9,
            status="AUTO",
            candidates=[],
        ),
        ColumnMapping(
            source_column="unknown_col",
            concept_key=None,
            score=0.3,
            status="UNKNOWN",
            candidates=[],
        ),
    ]

    df_norm = normalize_dataframe(
        df_raw=df,
        table_type="ASSESSMENT",
        mappings=mappings,
        region_id="region-01",
        file_id="file-123",
    )

    # known_col should be renamed
    assert "student_id" in df_norm.columns
    # unknown_col should keep original name
    assert "unknown_col" in df_norm.columns


def test_cast_column_types():
    """Test column type casting."""
    df = pd.DataFrame({
        "date": ["2025-01-10", "2025-01-11"],
        "test_score": ["85", "92"],
        "student_name": ["  John  ", "  Jane  "],
    })

    df_cast = _cast_column_types(df)

    # Date should be datetime
    assert pd.api.types.is_datetime64_any_dtype(df_cast["date"])

    # Score should be numeric
    assert pd.api.types.is_numeric_dtype(df_cast["test_score"])

    # Name should be stripped
    assert df_cast["student_name"].iloc[0] == "John"
    assert df_cast["student_name"].iloc[1] == "Jane"


def test_normalize_school_name():
    """Test school name normalization."""
    assert _normalize_school_name("  základní  škola  ") == "Základní Škola"
    assert _normalize_school_name("ZS Masarykova") == "ZŠ Masarykova"
    assert _normalize_school_name("Gym Praha") == "Gymnázium Praha"
    assert _normalize_school_name("") == ""


def test_pseudonymize_id():
    """Test ID pseudonymization."""
    original_id = "S12345"
    hashed = _pseudonymize_id(original_id)

    # Should be hashed
    assert hashed != original_id
    assert len(hashed) == 16

    # Should be deterministic
    hashed2 = _pseudonymize_id(original_id)
    assert hashed == hashed2

    # Empty values should remain empty
    assert _pseudonymize_id("") == ""


def test_normalize_dataframe_with_pseudonymization(monkeypatch):
    """Test normalization with pseudonymization enabled."""
    # Enable pseudonymization
    monkeypatch.setattr("eduscale.tabular.normalize.settings.PSEUDONYMIZE_IDS", True)

    df = pd.DataFrame({
        "student_id": ["S001", "S002"],
        "test_score": [85, 92],
    })

    mappings = [
        ColumnMapping(
            source_column="student_id",
            concept_key="student_id",
            score=0.9,
            status="AUTO",
            candidates=[],
        ),
        ColumnMapping(
            source_column="test_score",
            concept_key="test_score",
            score=0.85,
            status="AUTO",
            candidates=[],
        ),
    ]

    df_norm = normalize_dataframe(
        df_raw=df,
        table_type="ASSESSMENT",
        mappings=mappings,
        region_id="region-01",
        file_id="file-123",
    )

    # student_id should be hashed
    assert df_norm["student_id"].iloc[0] != "S001"
    assert len(df_norm["student_id"].iloc[0]) == 16

    # Original should be preserved
    assert "student_id_original" in df_norm.columns
    assert df_norm["student_id_original"].iloc[0] == "S001"


def test_normalize_empty_dataframe():
    """Test normalization of empty DataFrame."""
    df = pd.DataFrame()

    df_norm = normalize_dataframe(
        df_raw=df,
        table_type="ASSESSMENT",
        mappings=[],
        region_id="region-01",
        file_id="file-123",
    )

    assert df_norm.empty


def test_normalize_dataframe_low_confidence_mappings():
    """Test that LOW_CONFIDENCE mappings are also renamed."""
    df = pd.DataFrame({
        "col1": [1, 2],
    })

    mappings = [
        ColumnMapping(
            source_column="col1",
            concept_key="student_id",
            score=0.65,
            status="LOW_CONFIDENCE",
            candidates=[],
        ),
    ]

    df_norm = normalize_dataframe(
        df_raw=df,
        table_type="ASSESSMENT",
        mappings=mappings,
        region_id="region-01",
        file_id="file-123",
    )

    # LOW_CONFIDENCE should still be renamed
    assert "student_id" in df_norm.columns
