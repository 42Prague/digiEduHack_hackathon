"""LLM-based SQL generation from natural language.

This module uses Featherless.ai API to translate user questions
into safe, read-only SQL queries.
"""

import json
import logging
import re
from typing import Any

from openai import OpenAI, OpenAIError

from eduscale.core.config import settings
from eduscale.nlq.schema_context import get_system_prompt

logger = logging.getLogger(__name__)


class SqlGenerationError(Exception):
    """Raised when SQL generation fails."""

    pass


class SqlSafetyError(Exception):
    """Raised when generated SQL violates safety rules."""

    pass


def generate_sql_from_nl(
    user_query: str,
    history: list[dict[str, str]] | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Generate SQL query from natural language using Featherless.ai LLM.
    
    Args:
        user_query: Natural language question from user
        history: Optional conversation history (list of {role, content} dicts)
        correlation_id: Optional correlation ID for logging
        
    Returns:
        Dictionary with keys:
            - sql: Generated SQL query (validated and safe)
            - explanation: Human-readable explanation of the query
            
    Raises:
        SqlGenerationError: If LLM fails to generate valid SQL
        SqlSafetyError: If generated SQL violates safety rules
    """
    log_extra = {"correlation_id": correlation_id} if correlation_id else {}
    
    logger.info(
        f"Generating SQL from natural language query",
        extra={**log_extra, "user_query": user_query},
    )
    
    # Check if LLM is enabled
    if not settings.LLM_ENABLED:
        logger.warning("LLM is disabled", extra=log_extra)
        raise SqlGenerationError("Natural language query feature is disabled")
    
    # Check API key
    if not settings.FEATHERLESS_API_KEY:
        logger.error("FEATHERLESS_API_KEY not configured", extra=log_extra)
        raise SqlGenerationError("LLM API key not configured")
    
    # Load system prompt with schema context
    try:
        system_prompt = get_system_prompt()
    except Exception as e:
        logger.error(f"Failed to load system prompt: {e}", extra=log_extra)
        raise SqlGenerationError(f"Failed to load schema context: {e}")
    
    # Build messages for LLM
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history if provided (optional for MVP)
    if history:
        messages.extend(history)
    
    # Add current user query
    messages.append({"role": "user", "content": user_query})
    
    # Call Featherless.ai API
    try:
        client = OpenAI(
            base_url=settings.FEATHERLESS_BASE_URL,
            api_key=settings.FEATHERLESS_API_KEY,
        )
        
        logger.debug(
            f"Calling Featherless.ai API",
            extra={**log_extra, "model": settings.FEATHERLESS_LLM_MODEL},
        )
        
        response = client.chat.completions.create(
            model=settings.FEATHERLESS_LLM_MODEL,
            messages=messages,
            temperature=0.1,  # Low temperature for deterministic SQL generation
            max_tokens=500,
        )
        
        # Extract response content
        llm_response = response.choices[0].message.content
        
        logger.debug(
            f"Featherless.ai API response received",
            extra={**log_extra, "llm_response": llm_response},
        )
        
    except OpenAIError as e:
        logger.error(f"Featherless.ai API error: {e}", extra=log_extra)
        raise SqlGenerationError(f"LLM API call failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error calling Featherless.ai: {e}", extra=log_extra)
        raise SqlGenerationError(f"Unexpected error: {e}")
    
    # Parse JSON response
    try:
        result = json.loads(llm_response)
        
        if "sql" not in result:
            raise ValueError("Response missing 'sql' field")
        if "explanation" not in result:
            raise ValueError("Response missing 'explanation' field")
        
        sql = result["sql"]
        explanation = result["explanation"]
        
    except json.JSONDecodeError as e:
        logger.error(
            f"Failed to parse LLM response as JSON: {e}",
            extra={**log_extra, "llm_response": llm_response},
        )
        raise SqlGenerationError(f"LLM returned invalid JSON: {e}")
    except ValueError as e:
        logger.error(
            f"LLM response missing required fields: {e}",
            extra={**log_extra, "llm_response": llm_response},
        )
        raise SqlGenerationError(f"LLM response incomplete: {e}")
    
    # Validate and fix SQL
    try:
        safe_sql = _validate_and_fix_sql(sql, user_query, correlation_id)
    except SqlSafetyError as e:
        logger.error(f"SQL safety validation failed: {e}", extra=log_extra)
        raise
    
    logger.info(
        f"Successfully generated SQL from natural language",
        extra={**log_extra, "sql": safe_sql},
    )
    
    return {
        "sql": safe_sql,
        "explanation": explanation,
    }


def _validate_and_fix_sql(
    sql: str,
    user_query: str,
    correlation_id: str | None = None,
) -> str:
    """Validate SQL for safety and fix common issues.
    
    Args:
        sql: Generated SQL query
        user_query: Original user query (for context in error messages)
        correlation_id: Optional correlation ID for logging
        
    Returns:
        Validated and possibly modified SQL query
        
    Raises:
        SqlSafetyError: If SQL violates safety rules
    """
    log_extra = {"correlation_id": correlation_id} if correlation_id else {}
    
    # Normalize SQL for checks
    sql_stripped = sql.strip()
    sql_lower = sql_stripped.lower()
    
    # Rule 1: Must start with SELECT
    if not sql_lower.startswith("select"):
        logger.error(
            f"SQL does not start with SELECT",
            extra={**log_extra, "sql": sql_stripped},
        )
        raise SqlSafetyError(
            "Query must be a SELECT statement (read-only queries only)"
        )
    
    # Rule 2: Reject forbidden keywords (write operations)
    forbidden_keywords = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "create",
        "truncate",
        "merge",
        "grant",
        "revoke",
    ]
    
    for keyword in forbidden_keywords:
        # Use word boundaries to avoid false positives
        pattern = r"\b" + keyword + r"\b"
        if re.search(pattern, sql_lower):
            logger.error(
                f"SQL contains forbidden keyword: {keyword}",
                extra={**log_extra, "sql": sql_stripped},
            )
            raise SqlSafetyError(
                f"Query contains forbidden keyword: {keyword.upper()} (read-only queries only)"
            )
    
    # Rule 3: Verify dataset prefix is present
    dataset_id = settings.BIGQUERY_DATASET_ID
    if dataset_id not in sql_stripped:
        logger.warning(
            f"SQL missing dataset prefix: {dataset_id}",
            extra={**log_extra, "sql": sql_stripped},
        )
        # This is a warning, not an error, but should be logged
    
    # Rule 4: Ensure LIMIT clause exists
    if not re.search(r"\blimit\b", sql_lower):
        # Append LIMIT clause
        max_results = settings.NLQ_MAX_RESULTS
        sql_stripped = f"{sql_stripped.rstrip(';')} LIMIT {max_results}"
        logger.info(
            f"Added LIMIT {max_results} clause to SQL",
            extra={**log_extra, "sql": sql_stripped},
        )
    else:
        # Check if LIMIT is too high
        limit_match = re.search(r"\blimit\s+(\d+)", sql_lower)
        if limit_match:
            limit_value = int(limit_match.group(1))
            max_results = settings.NLQ_MAX_RESULTS
            
            if limit_value > max_results:
                # Reduce LIMIT to max allowed
                sql_stripped = re.sub(
                    r"\blimit\s+\d+",
                    f"LIMIT {max_results}",
                    sql_stripped,
                    flags=re.IGNORECASE,
                )
                logger.info(
                    f"Reduced LIMIT from {limit_value} to {max_results}",
                    extra={**log_extra, "sql": sql_stripped},
                )
    
    logger.debug(
        f"SQL validation passed",
        extra={**log_extra, "sql": sql_stripped},
    )
    
    return sql_stripped
