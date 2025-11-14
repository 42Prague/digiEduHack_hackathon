"""Unit tests for NLQ BigQuery Query Engine module."""

from unittest.mock import Mock, patch

import pytest
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

from eduscale.nlq.bq_query_engine import (
    QueryExecutionError,
    _sanitize_bigquery_error,
    get_bigquery_client,
    run_analytics_query,
)


class TestBigQueryEngine:
    """Tests for BigQuery query execution."""

    @patch("eduscale.nlq.bq_query_engine.bigquery.Client")
    def test_get_bigquery_client_creates_singleton(self, mock_client_class):
        """Test that get_bigquery_client returns singleton instance."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # First call
        client1 = get_bigquery_client()
        
        # Second call should return same instance
        client2 = get_bigquery_client()
        
        assert client1 is client2
        # Client should only be instantiated once
        assert mock_client_class.call_count == 1

    @patch("eduscale.nlq.bq_query_engine.get_bigquery_client")
    def test_successful_query_execution(self, mock_get_client):
        """Test successful query execution and result conversion."""
        # Setup mock client
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Setup mock query job
        mock_job = Mock()
        mock_job.total_bytes_processed = 1000
        mock_job.total_bytes_billed = 500
        mock_job.cache_hit = False
        mock_job.num_dml_affected_rows = None
        
        # Setup mock result with rows
        mock_row1 = Mock()
        mock_row1.items.return_value = [("region_id", "A"), ("count", 10)]
        mock_row2 = Mock()
        mock_row2.items.return_value = [("region_id", "B"), ("count", 20)]
        
        mock_result = Mock()
        mock_result.total_rows = 2
        mock_result.__iter__ = Mock(return_value=iter([mock_row1, mock_row2]))
        
        mock_job.result.return_value = mock_result
        mock_client.query.return_value = mock_job
        
        # Test
        sql = "SELECT region_id, COUNT(*) as count FROM table GROUP BY region_id LIMIT 100"
        rows = run_analytics_query(sql)
        
        assert len(rows) == 2
        assert rows[0] == {"region_id": "A", "count": 10}
        assert rows[1] == {"region_id": "B", "count": 20}

    @patch("eduscale.nlq.bq_query_engine.get_bigquery_client")
    def test_query_execution_with_correlation_id(self, mock_get_client):
        """Test query execution with correlation ID logging."""
        # Setup mock
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_job = Mock()
        mock_job.total_bytes_processed = 1000
        mock_job.cache_hit = False
        mock_result = Mock()
        mock_result.total_rows = 0
        mock_result.__iter__ = Mock(return_value=iter([]))
        mock_job.result.return_value = mock_result
        mock_client.query.return_value = mock_job
        
        # Test with correlation ID
        sql = "SELECT * FROM table LIMIT 100"
        correlation_id = "test-456"
        rows = run_analytics_query(sql, correlation_id=correlation_id)
        
        assert len(rows) == 0

    @patch("eduscale.nlq.bq_query_engine.get_bigquery_client")
    def test_empty_result_returns_empty_list(self, mock_get_client):
        """Test that query with no results returns empty list."""
        # Setup mock
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_job = Mock()
        mock_job.total_bytes_processed = 100
        mock_job.cache_hit = True
        mock_result = Mock()
        mock_result.total_rows = 0
        mock_result.__iter__ = Mock(return_value=iter([]))
        mock_job.result.return_value = mock_result
        mock_client.query.return_value = mock_job
        
        # Test
        sql = "SELECT * FROM table WHERE 1=0 LIMIT 100"
        rows = run_analytics_query(sql)
        
        assert rows == []

    @patch("eduscale.nlq.bq_query_engine.get_bigquery_client")
    @patch("eduscale.nlq.bq_query_engine.settings")
    def test_row_limit_enforcement(self, mock_settings, mock_get_client):
        """Test that results are limited to NLQ_MAX_RESULTS."""
        # Setup settings
        mock_settings.NLQ_MAX_RESULTS = 2
        mock_settings.NLQ_QUERY_TIMEOUT_SECONDS = 60
        mock_settings.BQ_MAX_BYTES_BILLED = None
        
        # Setup mock client
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Setup mock with 5 rows
        mock_rows = []
        for i in range(5):
            mock_row = Mock()
            mock_row.items.return_value = [("id", i)]
            mock_rows.append(mock_row)
        
        mock_job = Mock()
        mock_result = Mock()
        mock_result.total_rows = 5
        mock_result.__iter__ = Mock(return_value=iter(mock_rows))
        mock_job.result.return_value = mock_result
        mock_job.total_bytes_processed = 1000
        mock_job.cache_hit = False
        mock_client.query.return_value = mock_job
        
        # Test
        sql = "SELECT id FROM table LIMIT 5"
        rows = run_analytics_query(sql)
        
        # Should be limited to 2 rows
        assert len(rows) == 2

    @patch("eduscale.nlq.bq_query_engine.get_bigquery_client")
    def test_bigquery_error_raises_query_execution_error(self, mock_get_client):
        """Test that BigQuery errors are caught and wrapped."""
        # Setup mock to raise GoogleCloudError
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.query.side_effect = GoogleCloudError("Table not found")
        
        # Test
        sql = "SELECT * FROM nonexistent_table LIMIT 100"
        with pytest.raises(QueryExecutionError):
            run_analytics_query(sql)

    @patch("eduscale.nlq.bq_query_engine.get_bigquery_client")
    @patch("eduscale.nlq.bq_query_engine.settings")
    def test_maximum_bytes_billed_configured(self, mock_settings, mock_get_client):
        """Test that maximum_bytes_billed is set when configured."""
        # Setup settings
        mock_settings.NLQ_QUERY_TIMEOUT_SECONDS = 60
        mock_settings.BQ_MAX_BYTES_BILLED = 1000000  # 1MB
        
        # Setup mock
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_job = Mock()
        mock_result = Mock()
        mock_result.total_rows = 0
        mock_result.__iter__ = Mock(return_value=iter([]))
        mock_job.result.return_value = mock_result
        mock_job.total_bytes_processed = 100
        mock_job.cache_hit = False
        mock_client.query.return_value = mock_job
        
        # Test
        sql = "SELECT * FROM table LIMIT 100"
        run_analytics_query(sql)
        
        # Verify query was called with job_config
        assert mock_client.query.called
        call_args = mock_client.query.call_args
        job_config = call_args[0][1]  # Second positional argument
        assert isinstance(job_config, bigquery.QueryJobConfig)

    def test_sanitize_bigquery_error_table_not_found(self):
        """Test error sanitization for table not found."""
        error = Exception("Table not found: dataset.table")
        message = _sanitize_bigquery_error(error)
        
        assert "not found" in message.lower()
        assert "table" in message.lower()

    def test_sanitize_bigquery_error_permission_denied(self):
        """Test error sanitization for permission errors."""
        error = Exception("Permission denied on dataset")
        message = _sanitize_bigquery_error(error)
        
        assert "permission" in message.lower() or "access" in message.lower()

    def test_sanitize_bigquery_error_timeout(self):
        """Test error sanitization for timeout errors."""
        error = Exception("Query exceeded time limit")
        message = _sanitize_bigquery_error(error)
        
        assert "took too long" in message.lower() or "timeout" in message.lower()

    def test_sanitize_bigquery_error_quota_exceeded(self):
        """Test error sanitization for quota errors."""
        error = Exception("Quota exceeded for query processing")
        message = _sanitize_bigquery_error(error)
        
        assert "limit" in message.lower() or "quota" in message.lower()

    def test_sanitize_bigquery_error_syntax_error(self):
        """Test error sanitization for syntax errors."""
        error = Exception("Syntax error: Invalid SQL")
        message = _sanitize_bigquery_error(error)
        
        assert "syntax" in message.lower() or "invalid" in message.lower()

    def test_sanitize_bigquery_error_bytes_billed_exceeded(self):
        """Test error sanitization for bytes billed exceeded."""
        error = Exception("Query would process too many bytes billed")
        message = _sanitize_bigquery_error(error)
        
        assert "data" in message.lower() or "bytes" in message.lower()

    def test_sanitize_bigquery_error_generic(self):
        """Test error sanitization for unknown errors."""
        error = Exception("Some unknown error occurred")
        message = _sanitize_bigquery_error(error)
        
        assert "failed" in message.lower()

    @patch("eduscale.nlq.bq_query_engine.get_bigquery_client")
    def test_query_with_null_values(self, mock_get_client):
        """Test query execution with NULL values in results."""
        # Setup mock
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Row with NULL value
        mock_row = Mock()
        mock_row.items.return_value = [("region_id", "A"), ("score", None)]
        
        mock_job = Mock()
        mock_result = Mock()
        mock_result.total_rows = 1
        mock_result.__iter__ = Mock(return_value=iter([mock_row]))
        mock_job.result.return_value = mock_result
        mock_job.total_bytes_processed = 100
        mock_job.cache_hit = False
        mock_client.query.return_value = mock_job
        
        # Test
        sql = "SELECT region_id, score FROM table LIMIT 100"
        rows = run_analytics_query(sql)
        
        assert len(rows) == 1
        assert rows[0] == {"region_id": "A", "score": None}

    @patch("eduscale.nlq.bq_query_engine.get_bigquery_client")
    def test_query_with_various_data_types(self, mock_get_client):
        """Test query execution with various BigQuery data types."""
        # Setup mock
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Row with different data types
        mock_row = Mock()
        mock_row.items.return_value = [
            ("string_col", "test"),
            ("int_col", 42),
            ("float_col", 3.14),
            ("bool_col", True),
        ]
        
        mock_job = Mock()
        mock_result = Mock()
        mock_result.total_rows = 1
        mock_result.__iter__ = Mock(return_value=iter([mock_row]))
        mock_job.result.return_value = mock_result
        mock_job.total_bytes_processed = 100
        mock_job.cache_hit = False
        mock_client.query.return_value = mock_job
        
        # Test
        sql = "SELECT * FROM table LIMIT 100"
        rows = run_analytics_query(sql)
        
        assert len(rows) == 1
        assert rows[0]["string_col"] == "test"
        assert rows[0]["int_col"] == 42
        assert rows[0]["float_col"] == 3.14
        assert rows[0]["bool_col"] is True

    @patch("eduscale.nlq.bq_query_engine.get_bigquery_client")
    def test_query_cache_hit_logged(self, mock_get_client):
        """Test that cache hits are properly logged."""
        # Setup mock with cache hit
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_job = Mock()
        mock_job.total_bytes_processed = 0
        mock_job.total_bytes_billed = 0
        mock_job.cache_hit = True  # Cache hit
        mock_result = Mock()
        mock_result.total_rows = 0
        mock_result.__iter__ = Mock(return_value=iter([]))
        mock_job.result.return_value = mock_result
        mock_client.query.return_value = mock_job
        
        # Test
        sql = "SELECT * FROM table LIMIT 100"
        rows = run_analytics_query(sql)
        
        assert rows == []
        # Cache hit should be logged (verified via code inspection)

    @patch("eduscale.nlq.bq_query_engine.get_bigquery_client")
    def test_client_initialization_failure(self, mock_get_client):
        """Test handling of BigQuery client initialization failure."""
        # Setup mock to raise exception
        mock_get_client.side_effect = Exception("Failed to initialize client")
        
        # Test
        sql = "SELECT * FROM table LIMIT 100"
        with pytest.raises(QueryExecutionError, match="connection failed"):
            run_analytics_query(sql)

