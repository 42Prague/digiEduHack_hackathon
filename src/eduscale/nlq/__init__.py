"""Natural Language Query (NLQ) module for BigQuery analytics.

This module provides natural language to SQL translation capabilities,
enabling users to query BigQuery data using plain English questions.
"""

from eduscale.nlq.schema_context import load_schema_context, get_system_prompt
from eduscale.nlq.llm_sql import generate_sql_from_nl, SqlGenerationError, SqlSafetyError
from eduscale.nlq.bq_query_engine import run_analytics_query, QueryExecutionError

__all__ = [
    "load_schema_context",
    "get_system_prompt",
    "generate_sql_from_nl",
    "SqlGenerationError",
    "SqlSafetyError",
    "run_analytics_query",
    "QueryExecutionError",
]

