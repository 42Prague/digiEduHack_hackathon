"""Unit tests for NLQ Schema Context module."""

import pytest

from eduscale.core.config import settings
from eduscale.nlq.schema_context import (
    ColumnSchema,
    SchemaContext,
    TableSchema,
    get_cached_schema_context,
    get_system_prompt,
    load_schema_context,
)


class TestSchemaContext:
    """Tests for schema context loading and prompt generation."""

    def test_load_schema_context_returns_valid_structure(self):
        """Test that load_schema_context returns a valid SchemaContext."""
        context = load_schema_context()
        
        assert isinstance(context, SchemaContext)
        assert context.dataset_id == settings.BIGQUERY_DATASET_ID
        assert len(context.tables) > 0
        assert isinstance(context.system_prompt, str)
        assert len(context.system_prompt) > 0

    def test_schema_contains_all_expected_tables(self):
        """Test that schema context includes all expected BigQuery tables."""
        context = load_schema_context()
        table_names = [table.name for table in context.tables]
        
        expected_tables = [
            "dim_region",
            "dim_school",
            "dim_time",
            "fact_assessment",
            "fact_intervention",
            "observations",
            "observation_targets",
            "ingest_runs",
        ]
        
        for expected in expected_tables:
            assert expected in table_names, f"Missing expected table: {expected}"

    def test_fact_assessment_has_correct_columns(self):
        """Test that fact_assessment table has correct column definitions."""
        context = load_schema_context()
        fact_assessment = next(
            (t for t in context.tables if t.name == "fact_assessment"), None
        )
        
        assert fact_assessment is not None
        
        column_names = [col.name for col in fact_assessment.columns]
        
        # Check required columns
        required_columns = [
            "date",
            "region_id",
            "school_name",
            "student_id",
            "student_name",
            "subject",
            "test_score",
            "file_id",
            "ingest_timestamp",
        ]
        
        for col in required_columns:
            assert col in column_names, f"Missing column: {col}"
        
        # Check test_score is FLOAT type
        test_score_col = next(
            (c for c in fact_assessment.columns if c.name == "test_score"), None
        )
        assert test_score_col.type == "FLOAT"

    def test_observations_table_has_text_content_column(self):
        """Test that observations table has text_content column (not observation_text)."""
        context = load_schema_context()
        observations = next(
            (t for t in context.tables if t.name == "observations"), None
        )
        
        assert observations is not None
        
        column_names = [col.name for col in observations.columns]
        
        # Should have text_content, not observation_text
        assert "text_content" in column_names
        assert "observation_text" not in column_names

    def test_dim_time_has_integer_columns(self):
        """Test that dim_time table uses INTEGER type for numeric columns."""
        context = load_schema_context()
        dim_time = next((t for t in context.tables if t.name == "dim_time"), None)
        
        assert dim_time is not None
        
        # Check that year, month, day, quarter, day_of_week are INTEGER
        integer_columns = ["year", "month", "day", "quarter", "day_of_week"]
        
        for col_name in integer_columns:
            col = next((c for c in dim_time.columns if c.name == col_name), None)
            assert col is not None, f"Missing column: {col_name}"
            assert col.type == "INTEGER", f"{col_name} should be INTEGER, got {col.type}"

    def test_system_prompt_contains_schema_documentation(self):
        """Test that system prompt includes schema documentation."""
        prompt = get_system_prompt()
        
        # Check for dataset ID
        assert settings.BIGQUERY_DATASET_ID in prompt
        
        # Check for table names
        assert "fact_assessment" in prompt
        assert "fact_intervention" in prompt
        assert "observations" in prompt
        assert "dim_region" in prompt
        
        # Check for key column names
        assert "test_score" in prompt
        assert "region_id" in prompt
        assert "text_content" in prompt

    def test_system_prompt_contains_safety_rules(self):
        """Test that system prompt includes SQL safety rules."""
        prompt = get_system_prompt()
        
        # Check for safety keywords
        assert "SELECT" in prompt or "select" in prompt
        assert "read-only" in prompt.lower()
        assert "INSERT" in prompt or "insert" in prompt
        assert "UPDATE" in prompt or "update" in prompt
        assert "DELETE" in prompt or "delete" in prompt

    def test_system_prompt_contains_json_format_instruction(self):
        """Test that system prompt specifies JSON output format."""
        prompt = get_system_prompt()
        
        assert "json" in prompt.lower()
        assert '"sql"' in prompt or "'sql'" in prompt
        assert '"explanation"' in prompt or "'explanation'" in prompt

    def test_system_prompt_contains_few_shot_examples(self):
        """Test that system prompt includes few-shot examples."""
        prompt = get_system_prompt()
        
        # Check for example queries
        assert "example" in prompt.lower()
        
        # Check for at least one complete example with SQL
        assert "SELECT" in prompt
        assert "FROM" in prompt
        
        # Check for dataset prefix in examples
        assert f"`{settings.BIGQUERY_DATASET_ID}." in prompt

    def test_system_prompt_includes_limit_instruction(self):
        """Test that system prompt instructs LLM to use LIMIT clause."""
        prompt = get_system_prompt()
        
        assert "LIMIT" in prompt or "limit" in prompt

    def test_system_prompt_includes_bigquery_syntax_notes(self):
        """Test that system prompt mentions BigQuery-specific syntax."""
        prompt = get_system_prompt()
        
        # Check for BigQuery-specific functions or notes
        assert "BigQuery" in prompt or "bigquery" in prompt

    def test_cached_schema_context_returns_same_instance(self):
        """Test that get_cached_schema_context returns cached instance."""
        context1 = get_cached_schema_context()
        context2 = get_cached_schema_context()
        
        # Should be the same instance (cached)
        assert context1 is context2

    def test_table_partition_and_clustering_metadata(self):
        """Test that tables include partitioning and clustering metadata."""
        context = load_schema_context()
        
        # fact_assessment should be partitioned by date
        fact_assessment = next(
            (t for t in context.tables if t.name == "fact_assessment"), None
        )
        assert fact_assessment.partition_field == "date"
        assert "region_id" in fact_assessment.clustering_fields
        
        # observations should be partitioned by ingest_timestamp
        observations = next(
            (t for t in context.tables if t.name == "observations"), None
        )
        assert observations.partition_field == "ingest_timestamp"
        assert "region_id" in observations.clustering_fields

    def test_column_schema_includes_descriptions(self):
        """Test that column schemas include human-readable descriptions."""
        context = load_schema_context()
        
        fact_assessment = next(
            (t for t in context.tables if t.name == "fact_assessment"), None
        )
        
        # All columns should have non-empty descriptions
        for col in fact_assessment.columns:
            assert isinstance(col.description, str)
            assert len(col.description) > 0, f"Column {col.name} missing description"

    def test_required_columns_marked_correctly(self):
        """Test that required columns are marked with REQUIRED mode."""
        context = load_schema_context()
        
        fact_assessment = next(
            (t for t in context.tables if t.name == "fact_assessment"), None
        )
        
        # Check that date, region_id, file_id, ingest_timestamp are REQUIRED
        required_column_names = ["date", "region_id", "file_id", "ingest_timestamp"]
        
        for col_name in required_column_names:
            col = next((c for c in fact_assessment.columns if c.name == col_name), None)
            assert col.mode == "REQUIRED", f"{col_name} should be REQUIRED"

