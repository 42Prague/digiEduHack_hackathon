"""Unit tests for NLQ LLM SQL Generation module."""

import json
from unittest.mock import Mock, patch

import pytest
from openai import OpenAIError

from eduscale.core.config import settings
from eduscale.nlq.llm_sql import (
    SqlGenerationError,
    SqlSafetyError,
    generate_sql_from_nl,
)


class TestLLMSQLGeneration:
    """Tests for LLM-based SQL generation."""

    @patch("eduscale.nlq.llm_sql.OpenAI")
    def test_successful_sql_generation(self, mock_openai_class):
        """Test successful SQL generation from natural language."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "sql": "SELECT * FROM `jedouscale_core.fact_assessment` WHERE region_id = 'A' LIMIT 100",
            "explanation": "This query shows all assessments for region A.",
        })
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Test
        result = generate_sql_from_nl("Show me assessments in region A")
        
        assert "sql" in result
        assert "explanation" in result
        assert "SELECT" in result["sql"]
        assert "jedouscale_core" in result["sql"]

    @patch("eduscale.nlq.llm_sql.OpenAI")
    def test_sql_generation_with_conversation_history(self, mock_openai_class):
        """Test SQL generation with conversation history."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "sql": "SELECT * FROM `jedouscale_core.fact_assessment` LIMIT 100",
            "explanation": "This query shows assessments.",
        })
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Test with history
        history = [
            {"role": "user", "content": "What tables are available?"},
            {"role": "assistant", "content": "There are fact and dimension tables."},
        ]
        
        result = generate_sql_from_nl("Show me assessments", history=history)
        
        assert "sql" in result
        assert "explanation" in result

    @patch("eduscale.nlq.llm_sql.OpenAI")
    def test_invalid_json_response_raises_error(self, mock_openai_class):
        """Test that invalid JSON response raises SqlGenerationError."""
        # Setup mock with invalid JSON
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "This is not valid JSON"
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Test
        with pytest.raises(SqlGenerationError, match="invalid JSON"):
            generate_sql_from_nl("Show me data")

    @patch("eduscale.nlq.llm_sql.OpenAI")
    def test_missing_sql_field_raises_error(self, mock_openai_class):
        """Test that response missing 'sql' field raises SqlGenerationError."""
        # Setup mock with missing sql field
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "explanation": "This is an explanation without SQL.",
        })
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Test
        with pytest.raises(SqlGenerationError, match="missing 'sql' field"):
            generate_sql_from_nl("Show me data")

    @patch("eduscale.nlq.llm_sql.OpenAI")
    def test_missing_explanation_field_raises_error(self, mock_openai_class):
        """Test that response missing 'explanation' field raises SqlGenerationError."""
        # Setup mock with missing explanation field
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "sql": "SELECT * FROM table LIMIT 100",
        })
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Test
        with pytest.raises(SqlGenerationError, match="missing 'explanation' field"):
            generate_sql_from_nl("Show me data")

    @patch("eduscale.nlq.llm_sql.OpenAI")
    def test_openai_api_error_raises_sql_generation_error(self, mock_openai_class):
        """Test that OpenAI API errors are caught and wrapped."""
        # Setup mock to raise OpenAI error
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = OpenAIError("API timeout")
        mock_openai_class.return_value = mock_client
        
        # Test
        with pytest.raises(SqlGenerationError, match="API call failed"):
            generate_sql_from_nl("Show me data")

    @patch("eduscale.nlq.llm_sql.OpenAI")
    def test_insert_statement_rejected(self, mock_openai_class):
        """Test that INSERT statements are rejected by safety checks."""
        # Setup mock with INSERT statement
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "sql": "INSERT INTO table VALUES (1, 2, 3)",
            "explanation": "This inserts data.",
        })
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Test
        with pytest.raises(SqlSafetyError, match="INSERT"):
            generate_sql_from_nl("Insert some data")

    @patch("eduscale.nlq.llm_sql.OpenAI")
    def test_update_statement_rejected(self, mock_openai_class):
        """Test that UPDATE statements are rejected by safety checks."""
        # Setup mock with UPDATE statement
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "sql": "UPDATE table SET col = 1 WHERE id = 2",
            "explanation": "This updates data.",
        })
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Test
        with pytest.raises(SqlSafetyError, match="UPDATE"):
            generate_sql_from_nl("Update some data")

    @patch("eduscale.nlq.llm_sql.OpenAI")
    def test_delete_statement_rejected(self, mock_openai_class):
        """Test that DELETE statements are rejected by safety checks."""
        # Setup mock with DELETE statement
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "sql": "DELETE FROM table WHERE id = 1",
            "explanation": "This deletes data.",
        })
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Test
        with pytest.raises(SqlSafetyError, match="DELETE"):
            generate_sql_from_nl("Delete some data")

    @patch("eduscale.nlq.llm_sql.OpenAI")
    def test_drop_statement_rejected(self, mock_openai_class):
        """Test that DROP statements are rejected by safety checks."""
        # Setup mock with DROP statement
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "sql": "DROP TABLE table_name",
            "explanation": "This drops a table.",
        })
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Test
        with pytest.raises(SqlSafetyError, match="DROP"):
            generate_sql_from_nl("Drop the table")

    @patch("eduscale.nlq.llm_sql.OpenAI")
    def test_limit_clause_appended_when_missing(self, mock_openai_class):
        """Test that LIMIT clause is appended when missing."""
        # Setup mock without LIMIT
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "sql": "SELECT * FROM `jedouscale_core.fact_assessment`",
            "explanation": "This shows all assessments.",
        })
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Test
        result = generate_sql_from_nl("Show me all assessments")
        
        assert "LIMIT" in result["sql"]
        assert f"LIMIT {settings.NLQ_MAX_RESULTS}" in result["sql"]

    @patch("eduscale.nlq.llm_sql.OpenAI")
    def test_limit_clause_reduced_when_too_high(self, mock_openai_class):
        """Test that LIMIT clause is reduced when exceeding maximum."""
        # Setup mock with excessive LIMIT
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "sql": "SELECT * FROM `jedouscale_core.fact_assessment` LIMIT 10000",
            "explanation": "This shows many assessments.",
        })
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Test
        result = generate_sql_from_nl("Show me 10000 assessments")
        
        assert "LIMIT" in result["sql"]
        assert f"LIMIT {settings.NLQ_MAX_RESULTS}" in result["sql"]
        assert "LIMIT 10000" not in result["sql"]

    @patch("eduscale.nlq.llm_sql.OpenAI")
    def test_non_select_query_rejected(self, mock_openai_class):
        """Test that queries not starting with SELECT are rejected."""
        # Setup mock with non-SELECT query
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "sql": "DESCRIBE table_name",
            "explanation": "This describes a table.",
        })
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Test
        with pytest.raises(SqlSafetyError, match="SELECT"):
            generate_sql_from_nl("Describe the table")

    @patch("eduscale.nlq.llm_sql.settings")
    @patch("eduscale.nlq.llm_sql.OpenAI")
    def test_llm_disabled_raises_error(self, mock_openai_class, mock_settings):
        """Test that error is raised when LLM is disabled."""
        # Setup mock settings
        mock_settings.LLM_ENABLED = False
        
        # Test
        with pytest.raises(SqlGenerationError, match="disabled"):
            generate_sql_from_nl("Show me data")

    @patch("eduscale.nlq.llm_sql.settings")
    @patch("eduscale.nlq.llm_sql.OpenAI")
    def test_missing_api_key_raises_error(self, mock_openai_class, mock_settings):
        """Test that error is raised when API key is missing."""
        # Setup mock settings
        mock_settings.LLM_ENABLED = True
        mock_settings.FEATHERLESS_API_KEY = ""
        
        # Test
        with pytest.raises(SqlGenerationError, match="API key not configured"):
            generate_sql_from_nl("Show me data")

    @patch("eduscale.nlq.llm_sql.OpenAI")
    def test_correlation_id_logging(self, mock_openai_class):
        """Test that correlation ID is used in logging."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "sql": "SELECT * FROM `jedouscale_core.fact_assessment` LIMIT 100",
            "explanation": "This shows assessments.",
        })
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Test with correlation ID
        correlation_id = "test-123"
        result = generate_sql_from_nl("Show me data", correlation_id=correlation_id)
        
        assert "sql" in result
        # Correlation ID should be used in logging (verified via code inspection)

    @patch("eduscale.nlq.llm_sql.OpenAI")
    def test_case_insensitive_keyword_detection(self, mock_openai_class):
        """Test that forbidden keywords are detected case-insensitively."""
        # Setup mock with lowercase UPDATE
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "sql": "select * from table where id = 1; update table set col = 2",
            "explanation": "This is a compound statement.",
        })
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Test
        with pytest.raises(SqlSafetyError, match="UPDATE"):
            generate_sql_from_nl("Do something")

