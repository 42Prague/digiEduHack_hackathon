"""Integration tests for NLQ Chat API routes."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from eduscale.main import app
from eduscale.nlq.bq_query_engine import QueryExecutionError
from eduscale.nlq.llm_sql import SqlGenerationError, SqlSafetyError

client = TestClient(app)


class TestChatAPIEndpoint:
    """Tests for /api/v1/nlq/chat endpoint."""

    @patch("eduscale.api.v1.routes_nlq.run_analytics_query")
    @patch("eduscale.api.v1.routes_nlq.generate_sql_from_nl")
    def test_successful_chat_flow(self, mock_generate_sql, mock_run_query):
        """Test successful end-to-end chat flow."""
        # Setup mocks
        mock_generate_sql.return_value = {
            "sql": "SELECT * FROM `jedouscale_core.fact_assessment` LIMIT 100",
            "explanation": "This query shows all assessments.",
        }
        mock_run_query.return_value = [
            {"region_id": "A", "test_score": 85.5},
            {"region_id": "B", "test_score": 90.0},
        ]
        
        # Test request
        request_data = {
            "messages": [
                {"role": "user", "content": "Show me assessments"}
            ]
        }
        
        response = client.post("/api/v1/nlq/chat", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "messages" in data
        assert "sql" in data
        assert "explanation" in data
        assert "rows" in data
        assert "total_rows" in data
        assert data["error"] is None
        
        # Verify messages
        assert len(data["messages"]) == 2  # User + assistant
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"
        
        # Verify SQL and results
        assert "SELECT" in data["sql"]
        assert len(data["rows"]) == 2
        assert data["total_rows"] == 2

    @patch("eduscale.api.v1.routes_nlq.run_analytics_query")
    @patch("eduscale.api.v1.routes_nlq.generate_sql_from_nl")
    def test_chat_with_empty_results(self, mock_generate_sql, mock_run_query):
        """Test chat flow with query returning no results."""
        # Setup mocks
        mock_generate_sql.return_value = {
            "sql": "SELECT * FROM `jedouscale_core.fact_assessment` WHERE 1=0 LIMIT 100",
            "explanation": "This query has no results.",
        }
        mock_run_query.return_value = []
        
        # Test request
        request_data = {
            "messages": [
                {"role": "user", "content": "Show me impossible data"}
            ]
        }
        
        response = client.post("/api/v1/nlq/chat", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_rows"] == 0
        assert len(data["rows"]) == 0
        assert "No results" in data["messages"][1]["content"]

    def test_chat_with_no_messages_returns_400(self):
        """Test that request with no messages returns 400 error."""
        request_data = {"messages": []}
        
        response = client.post("/api/v1/nlq/chat", json=request_data)
        
        assert response.status_code == 400
        assert "No messages provided" in response.json()["detail"]

    def test_chat_with_no_user_message_returns_400(self):
        """Test that request with no user messages returns 400 error."""
        request_data = {
            "messages": [
                {"role": "assistant", "content": "Hello"}
            ]
        }
        
        response = client.post("/api/v1/nlq/chat", json=request_data)
        
        assert response.status_code == 400
        assert "No user message found" in response.json()["detail"]

    @patch("eduscale.api.v1.routes_nlq.settings")
    def test_chat_with_llm_disabled_returns_503(self, mock_settings):
        """Test that request with LLM disabled returns 503 error."""
        mock_settings.LLM_ENABLED = False
        
        request_data = {
            "messages": [
                {"role": "user", "content": "Show me data"}
            ]
        }
        
        response = client.post("/api/v1/nlq/chat", json=request_data)
        
        assert response.status_code == 503
        assert "disabled" in response.json()["detail"].lower()

    @patch("eduscale.api.v1.routes_nlq.generate_sql_from_nl")
    def test_chat_with_sql_generation_error(self, mock_generate_sql):
        """Test handling of SQL generation errors."""
        # Setup mock to raise error
        mock_generate_sql.side_effect = SqlGenerationError("Failed to generate SQL")
        
        request_data = {
            "messages": [
                {"role": "user", "content": "Show me data"}
            ]
        }
        
        response = client.post("/api/v1/nlq/chat", json=request_data)
        
        assert response.status_code == 200  # Error handled gracefully
        data = response.json()
        
        assert data["error"] is not None
        assert "Failed to generate SQL" in data["error"]
        assert "assistant" == data["messages"][-1]["role"]
        assert data["sql"] is None

    @patch("eduscale.api.v1.routes_nlq.generate_sql_from_nl")
    def test_chat_with_sql_safety_error(self, mock_generate_sql):
        """Test handling of SQL safety validation errors."""
        # Setup mock to raise safety error
        mock_generate_sql.side_effect = SqlSafetyError("Query contains INSERT")
        
        request_data = {
            "messages": [
                {"role": "user", "content": "Insert some data"}
            ]
        }
        
        response = client.post("/api/v1/nlq/chat", json=request_data)
        
        assert response.status_code == 200  # Error handled gracefully
        data = response.json()
        
        assert data["error"] is not None
        assert "Safety check failed" in data["error"]
        assert "couldn't process your query safely" in data["messages"][-1]["content"]

    @patch("eduscale.api.v1.routes_nlq.run_analytics_query")
    @patch("eduscale.api.v1.routes_nlq.generate_sql_from_nl")
    def test_chat_with_query_execution_error(self, mock_generate_sql, mock_run_query):
        """Test handling of BigQuery execution errors."""
        # Setup mocks
        mock_generate_sql.return_value = {
            "sql": "SELECT * FROM nonexistent_table LIMIT 100",
            "explanation": "This query will fail.",
        }
        mock_run_query.side_effect = QueryExecutionError("Table not found")
        
        request_data = {
            "messages": [
                {"role": "user", "content": "Show me data from nowhere"}
            ]
        }
        
        response = client.post("/api/v1/nlq/chat", json=request_data)
        
        assert response.status_code == 200  # Error handled gracefully
        data = response.json()
        
        assert data["error"] is not None
        assert "Query execution failed" in data["error"]
        assert "failed to execute" in data["messages"][-1]["content"]
        assert data["sql"] is not None  # SQL was generated

    @patch("eduscale.api.v1.routes_nlq.run_analytics_query")
    @patch("eduscale.api.v1.routes_nlq.generate_sql_from_nl")
    def test_chat_with_conversation_history(self, mock_generate_sql, mock_run_query):
        """Test chat with multi-turn conversation history."""
        # Setup mocks
        mock_generate_sql.return_value = {
            "sql": "SELECT * FROM `jedouscale_core.fact_assessment` LIMIT 100",
            "explanation": "This shows assessments.",
        }
        mock_run_query.return_value = [{"region_id": "A", "count": 10}]
        
        # Test request with history
        request_data = {
            "messages": [
                {"role": "user", "content": "What tables do you have?"},
                {"role": "assistant", "content": "We have fact and dimension tables."},
                {"role": "user", "content": "Show me assessments"},
            ]
        }
        
        response = client.post("/api/v1/nlq/chat", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include all history + new assistant message
        assert len(data["messages"]) == 4

    @patch("eduscale.api.v1.routes_nlq.run_analytics_query")
    @patch("eduscale.api.v1.routes_nlq.generate_sql_from_nl")
    def test_chat_response_limits_display_rows(self, mock_generate_sql, mock_run_query):
        """Test that response limits rows to first 20 for display."""
        # Setup mocks with many rows
        mock_generate_sql.return_value = {
            "sql": "SELECT * FROM table LIMIT 100",
            "explanation": "This shows many rows.",
        }
        
        # Generate 50 rows
        many_rows = [{"id": i} for i in range(50)]
        mock_run_query.return_value = many_rows
        
        request_data = {
            "messages": [
                {"role": "user", "content": "Show me lots of data"}
            ]
        }
        
        response = client.post("/api/v1/nlq/chat", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Display rows should be limited to 20
        assert len(data["rows"]) == 20
        # Total rows should be 50
        assert data["total_rows"] == 50

    @patch("eduscale.api.v1.routes_nlq.run_analytics_query")
    @patch("eduscale.api.v1.routes_nlq.generate_sql_from_nl")
    def test_chat_correlation_id_generated(self, mock_generate_sql, mock_run_query):
        """Test that correlation ID is generated for each request."""
        # Setup mocks
        mock_generate_sql.return_value = {
            "sql": "SELECT * FROM table LIMIT 100",
            "explanation": "Test query.",
        }
        mock_run_query.return_value = []
        
        request_data = {
            "messages": [
                {"role": "user", "content": "Test query"}
            ]
        }
        
        response = client.post("/api/v1/nlq/chat", json=request_data)
        
        assert response.status_code == 200
        # Correlation ID should be passed to mocks (verified via call inspection)
        assert mock_generate_sql.called
        call_kwargs = mock_generate_sql.call_args[1]
        assert "correlation_id" in call_kwargs

    def test_chat_invalid_request_body_returns_422(self):
        """Test that invalid request body returns 422 error."""
        request_data = {"invalid_field": "value"}
        
        response = client.post("/api/v1/nlq/chat", json=request_data)
        
        assert response.status_code == 422  # Validation error

    @patch("eduscale.api.v1.routes_nlq.run_analytics_query")
    @patch("eduscale.api.v1.routes_nlq.generate_sql_from_nl")
    def test_chat_response_structure_complete(self, mock_generate_sql, mock_run_query):
        """Test that response includes all required fields."""
        # Setup mocks
        mock_generate_sql.return_value = {
            "sql": "SELECT * FROM table LIMIT 100",
            "explanation": "Test explanation.",
        }
        mock_run_query.return_value = [{"col": "value"}]
        
        request_data = {
            "messages": [
                {"role": "user", "content": "Test"}
            ]
        }
        
        response = client.post("/api/v1/nlq/chat", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields
        required_fields = ["messages", "sql", "explanation", "rows", "total_rows", "error"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_chat_ui_route_returns_html(self):
        """Test that GET /nlq/chat returns HTML page."""
        response = client.get("/nlq/chat")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "EduScale Analytics Chat" in response.text

    def test_openapi_docs_include_nlq_endpoints(self):
        """Test that OpenAPI docs include NLQ endpoints."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        
        # Check openapi.json includes NLQ paths
        openapi_response = client.get("/openapi.json")
        openapi_data = openapi_response.json()
        
        assert "/api/v1/nlq/chat" in openapi_data["paths"]

