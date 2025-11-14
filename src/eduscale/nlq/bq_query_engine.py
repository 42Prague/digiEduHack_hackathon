"""BigQuery query execution engine for NLQ.

This module executes validated SQL queries against BigQuery
and returns results in a standardized format.
"""

import logging
import time
from typing import Any

from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

from eduscale.core.config import settings

logger = logging.getLogger(__name__)


class QueryExecutionError(Exception):
    """Raised when BigQuery query execution fails."""

    pass


# Global BigQuery client (singleton pattern for connection pooling)
_bq_client: bigquery.Client | None = None


def get_bigquery_client() -> bigquery.Client:
    """Get or create BigQuery client singleton.
    
    Returns:
        BigQuery Client instance
    """
    global _bq_client
    
    if _bq_client is None:
        project_id = settings.GCP_PROJECT_ID
        if not project_id:
            # Let BigQuery client auto-detect project
            _bq_client = bigquery.Client()
            logger.info("Initialized BigQuery client with auto-detected project")
        else:
            _bq_client = bigquery.Client(project=project_id)
            logger.info(f"Initialized BigQuery client for project: {project_id}")
    
    return _bq_client


def run_analytics_query(
    sql: str,
    correlation_id: str | None = None,
) -> list[dict[str, Any]]:
    """Execute validated SQL query against BigQuery.
    
    Args:
        sql: Validated SQL query (should already be checked for safety)
        correlation_id: Optional correlation ID for logging
        
    Returns:
        List of result rows as dictionaries
        
    Raises:
        QueryExecutionError: If query execution fails
    """
    log_extra = {"correlation_id": correlation_id} if correlation_id else {}
    
    logger.info(
        f"Executing BigQuery analytics query",
        extra={**log_extra, "sql": sql},
    )
    
    # Get BigQuery client
    try:
        client = get_bigquery_client()
    except Exception as e:
        logger.error(f"Failed to initialize BigQuery client: {e}", extra=log_extra)
        raise QueryExecutionError(f"Database connection failed: {e}")
    
    # Configure query job
    job_config = bigquery.QueryJobConfig(
        use_legacy_sql=False,  # Use Standard SQL
    )
    
    # Set maximum bytes billed if configured (cost control)
    if settings.BQ_MAX_BYTES_BILLED:
        job_config.maximum_bytes_billed = settings.BQ_MAX_BYTES_BILLED
        logger.debug(
            f"Set maximum_bytes_billed to {settings.BQ_MAX_BYTES_BILLED}",
            extra=log_extra,
        )
    
    # Execute query
    start_time = time.time()
    
    try:
        query_job = client.query(sql, job_config=job_config)
        
        # Wait for query to complete with timeout
        timeout = settings.NLQ_QUERY_TIMEOUT_SECONDS
        result = query_job.result(timeout=timeout)
        
        execution_time = time.time() - start_time
        
        # Log query metadata
        logger.info(
            f"BigQuery query completed",
            extra={
                **log_extra,
                "execution_time_seconds": round(execution_time, 2),
                "bytes_processed": query_job.total_bytes_processed or 0,
                "bytes_billed": query_job.total_bytes_billed or 0,
                "cache_hit": query_job.cache_hit or False,
                "num_rows": query_job.num_dml_affected_rows or result.total_rows or 0,
            },
        )
        
    except GoogleCloudError as e:
        execution_time = time.time() - start_time
        
        logger.error(
            f"BigQuery query failed",
            extra={
                **log_extra,
                "error": str(e),
                "execution_time_seconds": round(execution_time, 2),
            },
        )
        
        # Sanitize error message for user
        user_message = _sanitize_bigquery_error(e)
        raise QueryExecutionError(user_message)
    
    except Exception as e:
        execution_time = time.time() - start_time
        
        logger.error(
            f"Unexpected error executing BigQuery query",
            extra={
                **log_extra,
                "error": str(e),
                "execution_time_seconds": round(execution_time, 2),
            },
        )
        
        raise QueryExecutionError(f"Query execution failed: {e}")
    
    # Convert rows to list of dicts
    try:
        rows = [dict(row.items()) for row in result]
        
        # Enforce maximum results limit
        max_results = settings.NLQ_MAX_RESULTS
        if len(rows) > max_results:
            logger.warning(
                f"Query returned {len(rows)} rows, limiting to {max_results}",
                extra=log_extra,
            )
            rows = rows[:max_results]
        
        logger.info(
            f"Successfully retrieved {len(rows)} rows from BigQuery",
            extra=log_extra,
        )
        
        return rows
        
    except Exception as e:
        logger.error(
            f"Failed to convert BigQuery results to dict",
            extra={**log_extra, "error": str(e)},
        )
        raise QueryExecutionError(f"Failed to process query results: {e}")


def _sanitize_bigquery_error(error: Exception) -> str:
    """Convert BigQuery error to user-friendly message.
    
    Args:
        error: Exception from BigQuery
        
    Returns:
        Sanitized error message suitable for end users
    """
    error_str = str(error).lower()
    
    # Map common error patterns to user-friendly messages
    if "not found" in error_str:
        if "table" in error_str or "dataset" in error_str:
            return "Table or dataset not found. The query may reference a non-existent table."
        return "The requested resource was not found."
    
    if "permission" in error_str or "denied" in error_str or "access" in error_str:
        return "Permission denied. You may not have access to the requested data."
    
    if "timeout" in error_str or "exceeded" in error_str:
        if "time" in error_str:
            return "Query took too long to execute. Try simplifying your query or adding filters."
        if "quota" in error_str or "limit" in error_str:
            return "Query exceeded resource limits. Try reducing the amount of data processed."
    
    if "syntax" in error_str or "invalid" in error_str:
        return "Invalid SQL syntax. The generated query may have errors."
    
    if "bytes" in error_str and "billed" in error_str:
        return "Query would process too much data. Try adding filters or limiting the date range."
    
    # Default generic message
    return "Query execution failed. Please try rephrasing your question or simplifying the query."
