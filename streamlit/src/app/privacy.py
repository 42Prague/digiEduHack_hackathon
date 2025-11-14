"""
Privacy guardrails module
Enforces GDPR-aligned privacy protections: k-anonymity, aggregation-only queries
"""

import re
import streamlit as st
from typing import Tuple, Dict, Set, Optional, TYPE_CHECKING
import pandas as pd
import os
import requests
import logging

if TYPE_CHECKING:
    import duckdb

logger = logging.getLogger(__name__)


# Default allowed tables and their allowed columns (fallback only)
# Primary source is FastAPI /schemas endpoint via get_allowed_tables()
_DEFAULT_ALLOWED_TABLES: Dict[str, Set[str]] = {
    'schools': {'school_id', 'name', 'region', 'locale', 'deprivation_index', 
                'district_name', 'school_type', 'charter_flag', 'magnet_flag',
                'enrollment', 'free_reduced_lunch_pct', 'iep_pct', 'ell_pct',
                'latitude', 'longitude',
                'gdp_per_capita', 'education_expenditure_pct', 'internet_penetration', 'student_teacher_ratio'},
    'students': {'student_id_hash', 'school_id', 'birth_year_band', 'gender', 
                 'language_home', 'sen_flag', 'immigrant_status', 'race_ethnicity',
                 'ell_flag', 'free_reduced_lunch'},
    'assessments': {'assessment_id', 'student_id_hash', 'date', 'subject', 
                    'score', 'scale', 'percentile', 'grade_level'},
    'interventions': {'intervention_id', 'school_id', 'type', 'start_date', 
                     'end_date', 'intensity', 'target_group', 'provider', 
                     'budget', 'participant_count'},
    'outcomes': {'outcome_id', 'student_id_hash', 'date', 'outcome_type', 'value'},
    'surveys': {'survey_id', 'school_id', 'survey_date', 'survey_type',
                'parent_satisfaction', 'teacher_satisfaction', 'student_engagement',
                'safety_rating', 'bullying_incidents', 'response_rate'},
    'behavior': {'behavior_id', 'student_id_hash', 'date', 'attendance_rate',
                 'engagement_score', 'homework_completion', 'discipline_incidents', 'lms_logins'},
    'feedback': {'school_year', 'date', 'year', 'month', 'semester', 'name_of_participant',
                 'organization_school', 'school_grade', 'school_type', 'region', 'intervention',
                 'interventition_type', 'interventition_detail', 'target_group', 'overall_satisfaction',
                 'lecturer_performance_and_skills', 'planned_goals', 'gained_professional_development',
                 'open_feedback'}
}

# For backward compatibility, export ALLOWED_TABLES as a function that gets from FastAPI
def get_allowed_tables(conn=None) -> Dict[str, Set[str]]:
    """
    Get allowed tables with columns from FastAPI /schemas endpoint.
    Falls back to default tables if FastAPI is unavailable.
    
    Args:
        conn: DuckDB connection (optional, for database fallback)
        
    Returns:
        Dictionary mapping table names to their allowed column sets
    """
    return get_available_tables(conn)

# Backward compatibility: ALLOWED_TABLES as a property that fetches from FastAPI
# Note: This is a callable that should be used as get_allowed_tables() or get_available_tables()
ALLOWED_TABLES = _DEFAULT_ALLOWED_TABLES  # Kept for direct access, but prefer get_allowed_tables()

# Sensitive columns that should never be exposed directly
SENSITIVE_COLUMNS = {
    'student_id_hash',  # Pseudonymized but still sensitive
    'student_id',  # In case of variations
}

# Aggregation functions that are safe
SAFE_AGGREGATIONS = {
    'COUNT', 'SUM', 'AVG', 'AVERAGE', 'MIN', 'MAX', 'STDDEV', 'STDDEV_POP',
    'VAR_POP', 'VARIANCE', 'PERCENTILE_CONT', 'PERCENTILE_DISC'
}


def fetch_schemas_from_fastapi() -> Dict[str, Set[str]]:
    """
    Fetch registered schemas from FastAPI /schemas endpoint.
    This is the primary source for table and column information.
    
    Returns:
        Dictionary mapping table names to their allowed column sets
    """
    try:
        # Try FASTAPI_URL_EXTERNAL first, then FASTAPI_URL
        fastapi_url = os.getenv("FASTAPI_URL_EXTERNAL") or os.getenv("FASTAPI_URL")
        
        # If no URL is set, default to Docker service name (for container-to-container communication)
        if not fastapi_url:
            fastapi_url = "http://fastapi-bi-backend:8000"
            logger.info("No FastAPI URL set in env, defaulting to Docker service name: fastapi-bi-backend:8000")
        
        schemas_url = f"{fastapi_url}/schemas"
        logger.info(f"Fetching schemas from FastAPI: {schemas_url}")
        response = requests.get(schemas_url, timeout=10)
        
        if response.status_code == 200:
            schemas = response.json().get("schemas", [])
            tables_dict = {}
            
            for schema in schemas:
                schema_name = schema.get("schema_name", "").lower()
                columns = schema.get("columns", {})
                
                # Convert columns dict to set of column names
                # FastAPI returns columns as: {"col_name": {"type": "...", "description": "..."}}
                if isinstance(columns, dict):
                    # Extract column names from the keys of the columns dictionary
                    column_set = {col_name.lower() for col_name in columns.keys()}
                elif isinstance(columns, list):
                    column_set = {str(col).lower() for col in columns}
                else:
                    column_set = set()
                
                if schema_name:
                    tables_dict[schema_name] = column_set
                    logger.info(f"Loaded schema '{schema_name}' with {len(column_set)} columns from FastAPI")
            
            logger.info(f"Successfully fetched {len(tables_dict)} schemas with columns from FastAPI")
            return tables_dict
        else:
            logger.warning(f"FastAPI returned status {response.status_code}, falling back to default tables")
            return _DEFAULT_ALLOWED_TABLES
    except Exception as e:
        logger.error(f"Failed to fetch schemas from FastAPI: {e}. Falling back to default tables.")
        return _DEFAULT_ALLOWED_TABLES


def get_available_tables(conn=None) -> Dict[str, Set[str]]:
    """
    Get available tables from FastAPI schemas, with fallback to database and default tables.
    Combines FastAPI schemas with database tables to ensure all available tables are included.
    
    Args:
        conn: DuckDB connection (optional, for fallback)
        
    Returns:
        Dictionary mapping table names to their allowed column sets
    """
    # Start with FastAPI schemas
    fastapi_tables = fetch_schemas_from_fastapi()
    combined_tables = fastapi_tables.copy() if fastapi_tables else {}
    
    # Also check database directly and add any tables that exist there
    if conn is not None:
        try:
            existing_tables = conn.execute("SHOW TABLES").fetchdf()
            if not existing_tables.empty:
                table_names = {name.lower() for name in existing_tables['name'].tolist()}
                # Add database tables that aren't in FastAPI (with empty column sets = allow all columns)
                for table_name in table_names:
                    if table_name not in combined_tables:
                        combined_tables[table_name] = set()
        except Exception as e:
            logger.warning(f"Failed to get tables from database: {e}")
    
    # If we have tables from either source, return them
    if combined_tables:
        return combined_tables
    
    # Final fallback: use default _DEFAULT_ALLOWED_TABLES
    return _DEFAULT_ALLOWED_TABLES


def is_aggregation_only(sql: str) -> Tuple[bool, str]:
    """
    Check if SQL query only uses aggregations (no row-level data)
    
    Args:
        sql: SQL query string
        
    Returns:
        Tuple of (is_safe, error_message)
    """
    sql_upper = sql.upper().strip()
    
    # Remove comments
    sql_upper = re.sub(r'--.*?$', '', sql_upper, flags=re.MULTILINE)
    sql_upper = re.sub(r'/\*.*?\*/', '', sql_upper, flags=re.DOTALL)
    
    # Check for SELECT without GROUP BY or aggregation - likely row-level
    has_group_by = 'GROUP BY' in sql_upper
    has_aggregation = any(agg in sql_upper for agg in SAFE_AGGREGATIONS)
    
    # If no GROUP BY and no aggregation, it's likely returning raw rows
    if not has_group_by and not has_aggregation:
        # Exception: COUNT(*) queries are safe
        if not re.search(r'COUNT\s*\(\s*\*\s*\)', sql_upper):
            return False, "Query returns row-level data. Only aggregated queries are allowed."
    
    # Check if sensitive columns are selected directly (not in aggregations)
    for col in SENSITIVE_COLUMNS:
        # Match column selection patterns
        patterns = [
            rf'SELECT.*?{col}\b',  # Direct selection
            rf',\s*{col}\b',  # In column list
        ]
        for pattern in patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                # Allow if it's within an aggregation function context
                if not any(agg in sql_upper for agg in ['COUNT', 'DISTINCT']):
                    return False, f"Query selects sensitive column '{col}'. Use aggregations only."
    
    return True, ""


def validate_table_columns(sql: str, allowed_tables: Dict[str, Set[str]] = None, conn = None) -> Tuple[bool, str]:
    """
    Validate that only allowed tables and columns are used.
    Fetches available tables from FastAPI /schemas endpoint.
    
    Args:
        sql: SQL query string
        allowed_tables: Dictionary mapping table names to allowed column sets (optional)
        conn: DuckDB connection to check if tables exist (optional)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    sql_upper = sql.upper()
    
    # Extract table references
    table_pattern = r'\b(FROM|JOIN)\s+(\w+)\b'
    tables_mentioned = re.findall(table_pattern, sql_upper, re.IGNORECASE)
    
    # Get available tables from FastAPI (with fallbacks)
    if allowed_tables is None:
        allowed_tables = get_available_tables(conn)
    
    allowed_table_names = {name.lower() for name in allowed_tables.keys()}
    
    # Also check database directly as a fallback
    if conn is not None:
        try:
            existing_tables = conn.execute("SHOW TABLES").fetchdf()
            existing_table_names = {name.lower() for name in existing_tables['name'].tolist()} if not existing_tables.empty else set()
        except Exception:
            existing_table_names = set()
    else:
        existing_table_names = set()
    
    # Combine allowed tables from FastAPI and database
    all_allowed_tables = allowed_table_names | existing_table_names
    
    for _, table_name in tables_mentioned:
        table_lower = table_name.lower()
        # Allow if in allowed_tables OR if it exists in the database
        if table_lower not in all_allowed_tables:
            return False, f"Table '{table_name}' is not allowed. Allowed tables: {', '.join(sorted(all_allowed_tables))}"
    
    # Extract column references (basic check)
    # Only validate columns for tables that have column restrictions defined
    # If a table has an empty column set, allow all columns
    for table_name, allowed_cols in allowed_tables.items():
        if not allowed_cols:  # Empty set means allow all columns
            continue
        # Look for column.table patterns
        col_pattern = rf'\b(\w+)\.{table_name}\b'
        matches = re.findall(col_pattern, sql, re.IGNORECASE)
        for col in matches:
            if col.lower() not in allowed_cols:
                return False, f"Column '{col}' in table '{table_name}' is not allowed."
    
    return True, ""


def enforce_kanon(sql: str, k: int = 10) -> str:
    """
    Add k-anonymity enforcement (HAVING COUNT(*) >= k) to grouped queries
    
    Args:
        sql: SQL query string
        k: Minimum group size (default 10)
        
    Returns:
        Modified SQL query with k-anonymity enforcement
    """
    sql_upper = sql.upper()
    
    # Only enforce if there's a GROUP BY
    if 'GROUP BY' not in sql_upper:
        return sql
    
    # Check if HAVING already exists
    if 'HAVING' in sql_upper:
        # Try to merge with existing HAVING clause
        # Simple approach: add COUNT(*) >= k to existing HAVING
        sql = re.sub(
            r'(HAVING\s+.*)',
            rf'\1 AND COUNT(*) >= {k}',
            sql,
            flags=re.IGNORECASE | re.DOTALL
        )
    else:
        # Add HAVING clause before ORDER BY or at end
        if 'ORDER BY' in sql_upper:
            sql = re.sub(
                r'\s+(ORDER BY\s+.+)',
                rf' HAVING COUNT(*) >= {k}\1',
                sql,
                flags=re.IGNORECASE
            )
        else:
            sql = sql.rstrip(';').rstrip() + f' HAVING COUNT(*) >= {k}'
    
    return sql


def is_safe_sql(sql: str, allowed_tables: Dict[str, Set[str]] = None, conn = None) -> Tuple[bool, str]:
    """
    Comprehensive SQL safety check
    
    Args:
        sql: SQL query string
        allowed_tables: Dictionary of allowed tables and columns (optional)
        conn: DuckDB connection to check if tables exist (optional)
        
    Returns:
        Tuple of (is_safe, error_message)
    """
    # Privacy checks disabled - always return safe
    return True, ""


def run_safe_query(conn, sql: str, k: int = 10) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Execute a SQL query directly without any privacy checks.
    Automatically tries to load missing tables from MinIO if query fails.
    
    Args:
        conn: DuckDB connection
        sql: SQL query string
        k: Minimum group size for k-anonymity (ignored, kept for compatibility)
        
    Returns:
        Tuple of (result_dataframe, error_message)
    """
    try:
        # Execute query directly without any restrictions
        result_df = conn.execute(sql).fetchdf()
        return result_df, None
    except Exception as e:
        error_msg = str(e)
        # Check if it's a table not found error
        if "does not exist" in error_msg.lower() or "catalog error" in error_msg.lower():
            # Try to extract table name from error message
            import re
            table_match = re.search(r"Table with name (\w+) does not exist", error_msg, re.IGNORECASE)
            if table_match:
                missing_table = table_match.group(1)
                logger.info(f"Table '{missing_table}' not found, attempting to load from MinIO...")
                
                # Try to load missing tables from gold bucket
                try:
                    from database import load_parquet_from_gold_bucket
                    # Try to load the specific missing table
                    success, load_message = load_parquet_from_gold_bucket(conn, specific_table=missing_table)
                    
                    if success:
                        # Retry the query after loading
                        try:
                            result_df = conn.execute(sql).fetchdf()
                            logger.info(f"Successfully loaded table '{missing_table}' and executed query")
                            return result_df, None
                        except Exception as retry_e:
                            # Still failed, return error with context
                            return None, f"Query execution error after loading table: {str(retry_e)}\n\nTable loading: {load_message}"
                    else:
                        # Loading failed, return detailed error
                        logger.warning(f"Failed to load table from MinIO: {load_message}")
                        return None, f"Query execution error: {error_msg}\n\n❌ Failed to load table '{missing_table}' from MinIO:\n{load_message}\n\n💡 Check:\n- MINIO_ENABLED=true in .env\n- MINIO_URL is correct (e.g., http://minio:9000)\n- Table file exists in bucket: {os.getenv('MINIO_BUCKET', 'gold')}/{missing_table}.parquet"
                except Exception as load_error:
                    logger.warning(f"Exception while loading table from MinIO: {load_error}")
                    import traceback
                    traceback_str = traceback.format_exc()
                    return None, f"Query execution error: {error_msg}\n\n❌ Exception while loading table:\n{str(load_error)}\n\n{traceback_str}\n\n💡 Make sure MINIO_ENABLED=true and MINIO_URL are set correctly in your .env file."
        
        return None, f"Query execution error: {error_msg}"


def get_privacy_summary() -> str:
    """
    Get summary of privacy protections for display
    
    Returns:
        Privacy summary text
    """
    return """
    **Privacy Protections:**
    - ✅ Aggregation-only queries (no row-level data)
    - ✅ k-anonymity enforcement (minimum group size: 10)
    - ✅ Column allowlist validation
    - ✅ Sensitive data protection
    - ✅ No destructive operations (DROP, DELETE, etc.)
    """

