"""Schema context module for NLQ.

This module defines the BigQuery schema structure and generates
system prompts for the LLM to translate natural language to SQL.
"""

import logging
from dataclasses import dataclass
from typing import Any

from eduscale.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ColumnSchema:
    """Schema definition for a single column."""

    name: str
    type: str
    description: str
    mode: str = "NULLABLE"


@dataclass
class TableSchema:
    """Schema definition for a BigQuery table."""

    name: str
    description: str
    columns: list[ColumnSchema]
    partition_field: str | None = None
    clustering_fields: list[str] | None = None


@dataclass
class SchemaContext:
    """Complete schema context for BigQuery dataset."""

    dataset_id: str
    tables: list[TableSchema]
    system_prompt: str


def load_schema_context() -> SchemaContext:
    """Load BigQuery schema context from actual BigQuery table definitions.
    
    Returns:
        SchemaContext with all tables and columns defined
    """
    dataset_id = settings.BIGQUERY_DATASET_ID
    
    # Define dimension tables
    dim_region = TableSchema(
        name="dim_region",
        description="Region dimension table. Contains regional hierarchy data.",
        columns=[
            ColumnSchema("region_id", "STRING", "Unique region identifier", "REQUIRED"),
            ColumnSchema("region_name", "STRING", "Human-readable region name"),
            ColumnSchema("from_date", "DATE", "Validity start date for this region record"),
            ColumnSchema("to_date", "DATE", "Validity end date for this region record"),
        ],
    )
    
    dim_school = TableSchema(
        name="dim_school",
        description="School dimension table. Contains school master data.",
        columns=[
            ColumnSchema("school_name", "STRING", "School name", "REQUIRED"),
            ColumnSchema("region_id", "STRING", "Foreign key to dim_region"),
            ColumnSchema("from_date", "DATE", "Validity start date for this school record"),
            ColumnSchema("to_date", "DATE", "Validity end date for this school record"),
        ],
    )
    
    dim_time = TableSchema(
        name="dim_time",
        description="Time dimension table. Contains date attributes for temporal analysis.",
        columns=[
            ColumnSchema("date", "DATE", "Calendar date", "REQUIRED"),
            ColumnSchema("year", "INTEGER", "Year (e.g. 2023)"),
            ColumnSchema("month", "INTEGER", "Month number (1-12)"),
            ColumnSchema("day", "INTEGER", "Day of month (1-31)"),
            ColumnSchema("quarter", "INTEGER", "Quarter (1-4)"),
            ColumnSchema("day_of_week", "INTEGER", "Day of week (1-7, Monday=1)"),
        ],
    )
    
    # Define fact tables
    fact_assessment = TableSchema(
        name="fact_assessment",
        description="Assessment fact table. Contains student test scores and assessment results. Partitioned by date, clustered by region_id.",
        columns=[
            ColumnSchema("date", "DATE", "Assessment date", "REQUIRED"),
            ColumnSchema("region_id", "STRING", "Foreign key to dim_region", "REQUIRED"),
            ColumnSchema("school_name", "STRING", "School name"),
            ColumnSchema("student_id", "STRING", "Student identifier"),
            ColumnSchema("student_name", "STRING", "Student name"),
            ColumnSchema("subject", "STRING", "Subject/course name (e.g. Math, English)"),
            ColumnSchema("test_score", "FLOAT", "Numeric test score (0-100 or similar scale)"),
            ColumnSchema("file_id", "STRING", "Source file identifier", "REQUIRED"),
            ColumnSchema("ingest_timestamp", "TIMESTAMP", "When this record was ingested", "REQUIRED"),
        ],
        partition_field="date",
        clustering_fields=["region_id"],
    )
    
    fact_intervention = TableSchema(
        name="fact_intervention",
        description="Intervention fact table. Contains educational intervention/program data. Partitioned by date, clustered by region_id.",
        columns=[
            ColumnSchema("date", "DATE", "Intervention date", "REQUIRED"),
            ColumnSchema("region_id", "STRING", "Foreign key to dim_region", "REQUIRED"),
            ColumnSchema("school_name", "STRING", "School name"),
            ColumnSchema("intervention_type", "STRING", "Type of intervention (e.g. tutoring, remedial)"),
            ColumnSchema("participants_count", "INTEGER", "Number of participants in intervention"),
            ColumnSchema("file_id", "STRING", "Source file identifier", "REQUIRED"),
            ColumnSchema("ingest_timestamp", "TIMESTAMP", "When this record was ingested", "REQUIRED"),
        ],
        partition_field="date",
        clustering_fields=["region_id"],
    )
    
    # Define observations table (unstructured/mixed data)
    observations = TableSchema(
        name="observations",
        description="Observations table. Contains unstructured or semi-structured data like feedback text, transcribed audio, etc. Partitioned by ingest_timestamp, clustered by region_id.",
        columns=[
            ColumnSchema("file_id", "STRING", "Source file identifier", "REQUIRED"),
            ColumnSchema("region_id", "STRING", "Foreign key to dim_region", "REQUIRED"),
            ColumnSchema("text_content", "STRING", "Full text content (transcribed audio, feedback text, etc.)"),
            ColumnSchema("detected_entities", "JSON", "JSON object with detected entities (teachers, students, subjects)"),
            ColumnSchema("sentiment_score", "FLOAT64", "Sentiment score (-1.0 to 1.0)"),
            ColumnSchema("original_content_type", "STRING", "Original file type (audio, pdf, text)"),
            ColumnSchema("audio_duration_ms", "INT64", "Audio duration in milliseconds (if audio)"),
            ColumnSchema("audio_confidence", "FLOAT64", "Audio transcription confidence (0-1)"),
            ColumnSchema("audio_language", "STRING", "Detected audio language code (e.g. en-US, cs-CZ)"),
            ColumnSchema("page_count", "INT64", "Number of pages (if document)"),
            ColumnSchema("source_table_type", "STRING", "Source table type classification"),
            ColumnSchema("ingest_timestamp", "TIMESTAMP", "When this record was ingested", "REQUIRED"),
        ],
        partition_field="ingest_timestamp",
        clustering_fields=["region_id"],
    )
    
    # Define observation_targets table
    observation_targets = TableSchema(
        name="observation_targets",
        description="Observation targets junction table. Links observations to detected entities (teachers, students, subjects). Partitioned by ingest_timestamp, clustered by observation_id and target_type.",
        columns=[
            ColumnSchema("observation_id", "STRING", "Foreign key to observations (file_id)", "REQUIRED"),
            ColumnSchema("target_type", "STRING", "Type of target entity (teacher, student, subject)", "REQUIRED"),
            ColumnSchema("target_id", "STRING", "ID of the target entity", "REQUIRED"),
            ColumnSchema("relevance_score", "FLOAT64", "Relevance/similarity score (0-1)"),
            ColumnSchema("confidence", "STRING", "Confidence level (high, medium, low)"),
            ColumnSchema("ingest_timestamp", "TIMESTAMP", "When this record was ingested", "REQUIRED"),
        ],
        partition_field="ingest_timestamp",
        clustering_fields=["observation_id", "target_type"],
    )
    
    # Define ingest_runs table
    ingest_runs = TableSchema(
        name="ingest_runs",
        description="Ingest runs tracking table. Tracks data pipeline execution for audit and debugging. Partitioned by created_at, clustered by region_id and status.",
        columns=[
            ColumnSchema("file_id", "STRING", "File identifier being processed", "REQUIRED"),
            ColumnSchema("region_id", "STRING", "Region of the file", "REQUIRED"),
            ColumnSchema("status", "STRING", "Processing status (success, error, pending)", "REQUIRED"),
            ColumnSchema("step", "STRING", "Current processing step"),
            ColumnSchema("error_message", "STRING", "Error message if status=error"),
            ColumnSchema("created_at", "TIMESTAMP", "When processing started", "REQUIRED"),
            ColumnSchema("updated_at", "TIMESTAMP", "Last update timestamp", "REQUIRED"),
        ],
        partition_field="created_at",
        clustering_fields=["region_id", "status"],
    )
    
    tables = [
        dim_region,
        dim_school,
        dim_time,
        fact_assessment,
        fact_intervention,
        observations,
        observation_targets,
        ingest_runs,
    ]
    
    # Generate system prompt with current dataset_id and tables
    system_prompt = _build_system_prompt(dataset_id, tables)
    
    logger.info(f"Loaded schema context for dataset: {dataset_id}")
    
    return SchemaContext(
        dataset_id=dataset_id,
        tables=tables,
        system_prompt=system_prompt,
    )


def _build_system_prompt(dataset_id: str, tables: list[TableSchema]) -> str:
    """Build system prompt from dataset ID and tables.
    
    Args:
        dataset_id: BigQuery dataset ID
        tables: List of table schemas
    
    Returns:
        System prompt string with schema context and instructions
    """
    
    # Build table schema documentation
    schema_doc = []
    for table in tables:
        table_header = f"\n### Table: {dataset_id}.{table.name}"
        table_desc = f"Description: {table.description}"
        
        # Add partitioning/clustering info
        meta_info = []
        if table.partition_field:
            meta_info.append(f"Partitioned by: {table.partition_field}")
        if table.clustering_fields:
            meta_info.append(f"Clustered by: {', '.join(table.clustering_fields)}")
        
        columns_doc = "Columns:"
        for col in table.columns:
            col_line = f"  - {col.name} ({col.type}, {col.mode}): {col.description}"
            columns_doc += f"\n{col_line}"
        
        table_block = [table_header, table_desc]
        if meta_info:
            table_block.append(" | ".join(meta_info))
        table_block.append(columns_doc)
        
        schema_doc.append("\n".join(table_block))
    
    schema_str = "\n".join(schema_doc)
    
    # Build few-shot examples
    few_shot_examples = """
## Example Queries

Example 1:
User: "Show me average test scores by region"
Response:
{
  "sql": "SELECT region_id, AVG(test_score) as avg_score FROM `jedouscale_core.fact_assessment` GROUP BY region_id ORDER BY avg_score DESC LIMIT 100",
  "explanation": "This query calculates the average test score for each region from the fact_assessment table, ordered by highest average score first."
}

Example 2:
User: "List interventions in the last 30 days"
Response:
{
  "sql": "SELECT date, region_id, school_name, intervention_type, participants_count FROM `jedouscale_core.fact_intervention` WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) ORDER BY date DESC LIMIT 100",
  "explanation": "This query retrieves all interventions from the last 30 days, showing key details about each intervention ordered by most recent first."
}

Example 3:
User: "Find feedback mentioning teachers"
Response:
{
  "sql": "SELECT o.file_id, o.text_content, o.sentiment_score, ot.target_type FROM `jedouscale_core.observations` o JOIN `jedouscale_core.observation_targets` ot ON o.file_id = ot.observation_id WHERE ot.target_type = 'teacher' LIMIT 100",
  "explanation": "This query finds observations (feedback text) that mention teachers by joining with observation_targets table filtered by target_type='teacher'."
}

Example 4:
User: "What are the top performing schools?"
Response:
{
  "sql": "SELECT school_name, AVG(test_score) as avg_score, COUNT(*) as assessment_count FROM `jedouscale_core.fact_assessment` GROUP BY school_name HAVING assessment_count > 10 ORDER BY avg_score DESC LIMIT 100",
  "explanation": "This query ranks schools by average test score, including only schools with more than 10 assessments, to show top performers."
}

Example 5:
User: "Show intervention participation trends by month"
Response:
{
  "sql": "SELECT t.year, t.month, SUM(i.participants_count) as total_participants FROM `jedouscale_core.fact_intervention` i JOIN `jedouscale_core.dim_time` t ON i.date = t.date GROUP BY t.year, t.month ORDER BY t.year, t.month LIMIT 100",
  "explanation": "This query aggregates intervention participation counts by month using the time dimension table to extract year and month from dates."
}
"""
    
    # Build complete system prompt
    system_prompt = f"""You are an expert SQL query generator for BigQuery. Your task is to translate natural language questions into safe, read-only SQL queries against the EduScale educational analytics database.

## Database Schema

Dataset: {dataset_id}
{schema_str}

## Important Rules

1. **Output Format**: ALWAYS respond with valid JSON containing "sql" and "explanation" fields:
   {{"sql": "SELECT ...", "explanation": "This query..."}}

2. **Dataset Prefix**: ALWAYS use fully-qualified table names with dataset prefix: `{dataset_id}.table_name`

3. **SQL Safety**:
   - Only generate SELECT queries (read-only)
   - NEVER use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, MERGE, GRANT, REVOKE
   - Do not modify data or schema

4. **Query Limits**:
   - Always include a LIMIT clause (default: LIMIT 100)
   - For aggregations, use reasonable GROUP BY and filtering

5. **BigQuery Syntax**:
   - Use BigQuery Standard SQL (not legacy SQL)
   - Use DATE_SUB() for date arithmetic
   - Use CURRENT_DATE() for current date
   - Use backticks for table names: `dataset.table`

6. **Best Practices**:
   - Use partitioning fields in WHERE clauses when possible (date, ingest_timestamp)
   - Use clustering fields for efficient filtering (region_id)
   - Include ORDER BY for predictable results
   - Provide clear explanations for generated queries

7. **Error Handling**:
   - If the question is unclear, generate a reasonable query based on available tables
   - If a column name is not found, suggest similar columns
   - Always return valid JSON even if you're uncertain

{few_shot_examples}

## Your Task

Translate the user's natural language question into a safe BigQuery SQL query following all the rules above. Return ONLY the JSON response with "sql" and "explanation" fields.
"""
    
    return system_prompt


# Module-level cache for schema context
_schema_context_cache: SchemaContext | None = None


def get_cached_schema_context() -> SchemaContext:
    """Get cached schema context or load if not cached.
    
    Returns:
        Cached SchemaContext instance
    """
    global _schema_context_cache
    
    if _schema_context_cache is None:
        _schema_context_cache = load_schema_context()
    
    return _schema_context_cache


def get_system_prompt() -> str:
    """Get system prompt for LLM SQL generation.
    
    Uses cached schema context.
    
    Returns:
        System prompt string with schema context and instructions
    """
    context = get_cached_schema_context()
    return context.system_prompt
