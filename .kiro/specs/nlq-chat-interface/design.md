# Design Document: NL→SQL Chat Interface

## Overview

The NL→SQL Chat Interface provides a conversational way to query BigQuery analytics data using natural language. The system translates user questions into safe, read-only SQL queries using Llama 3.2 1B via Ollama, executes them against BigQuery, and returns results formatted for display in a simple chat UI.

This is an MVP implementation focused on:
- **Simplicity**: Single endpoint, stateless conversation, minimal UI
- **Safety**: Strict SQL validation, read-only queries, cost controls
- **Reliability**: Local LLM (no external API dependencies), deterministic prompts
- **Demo-Ready**: 3-5 reliable example queries for pitch presentations

The design integrates seamlessly with the existing FastAPI application architecture, following established patterns for configuration, logging, and API routes.

### Goals

1. Enable non-technical users to query BigQuery data using natural language
2. Maintain strict safety controls (read-only, validated SQL)
3. Provide transparent query generation (show generated SQL to users)
4. Keep infrastructure simple (local Ollama, no external SaaS dependencies)
5. Deliver demo-ready feature for hackathon pitch

### Non-Goals

- Complex multi-turn conversation with context retention (MVP: stateless)
- Query result caching or optimization (rely on BigQuery caching)
- User authentication/authorization (inherit from existing Cloud Run auth)
- Advanced NLQ features (query suggestions, autocomplete, query history)
- GPU acceleration for LLM inference (Cloud Run is CPU-only)

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                            │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Chat UI (/nlq/chat)                          │ │
│  │  ┌────────────────────────────────────────────────────┐   │ │
│  │  │  [Chat History]                                    │   │ │
│  │  │  User: "Compare Region A and B test scores"       │   │ │
│  │  │  Assistant: "Here are the results..."             │   │ │
│  │  │    [SQL Table with 10 rows]                       │   │ │
│  │  │    [Show SQL ▼]                                   │   │ │
│  │  └────────────────────────────────────────────────────┘   │ │
│  │  [Text Input] [Send]                                      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                           │ POST /api/v1/nlq/chat              │
└───────────────────────────┼────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              FastAPI Application (Cloud Run)                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Chat API Endpoint (/api/v1/nlq/chat)                    │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │ 1. Extract user message                             │ │ │
│  │  │ 2. Call generate_sql_from_nl()                      │ │ │
│  │  │ 3. Call run_analytics_query()                       │ │ │
│  │  │ 4. Build assistant response                         │ │ │
│  │  │ 5. Return ChatResponse                              │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
│           │                                    │                │
│           ▼                                    ▼                │
│  ┌──────────────────────┐          ┌──────────────────────┐   │
│  │  LLM SQL Generator   │          │  BigQuery Runner     │   │
│  │  (llm_sql.py)        │          │  (bq_query_engine.py)│   │
│  │                      │          │                      │   │
│  │  • Load schema ctx   │          │  • Init BQ client    │   │
│  │  • Call Ollama       │          │  • Execute SQL       │   │
│  │  • Parse JSON        │          │  • Return rows       │   │
│  │  • Safety checks     │          │  • Handle errors     │   │
│  └──────────┬───────────┘          └──────────┬───────────┘   │
│             │                                  │                │
└─────────────┼──────────────────────────────────┼────────────────┘
              │                                  │
              ▼                                  ▼
    ┌──────────────────┐              ┌──────────────────┐
    │  Ollama Service  │              │  BigQuery API    │
    │  (localhost:11434)│             │  (GCP)           │
    │                  │              │                  │
    │  Llama 3.2 1B    │              │  Dataset:        │
    │  (local, CPU)    │              │  jedouscale_core │
    └──────────────────┘              └──────────────────┘
```

### Component Diagram

```
src/eduscale/
├── nlq/                           # 🆕 NLQ Module
│   ├── __init__.py
│   ├── schema_context.py          # BigQuery schema + LLM system prompt
│   ├── llm_sql.py                 # LLM-based SQL generation + safety
│   └── bq_query_engine.py         # BigQuery query execution
│
├── analytics/                     # 🆕 Analytics Module (placeholder for future)
│   ├── __init__.py
│   └── bq_query_engine.py → moved to nlq/
│
├── api/
│   └── v1/
│       ├── routes_nlq.py          # 🆕 NLQ Chat API endpoint
│       ├── routes_health.py       # Existing
│       ├── routes_upload.py       # Existing
│       └── routes_tabular.py      # Existing
│
├── ui/
│   └── templates/
│       ├── chat.html              # 🆕 Chat UI
│       └── upload.html            # Existing
│
└── core/
    ├── config.py                  # Extended with NLQ settings
    └── logging.py                 # Existing
```

### Data Flow

#### Successful Query Flow

```
User → Chat UI → POST /api/v1/nlq/chat
    {messages: [{role: "user", content: "Compare regions by test scores"}]}
        ↓
    Chat API: Extract user message
        ↓
    LLM SQL Generator:
        1. Load schema context + system prompt
        2. Call Ollama: POST http://localhost:11434/api/generate
           {model: "llama3.2:1b", prompt: "<system>\n<user>", temperature: 0.1}
        3. Parse JSON: {"sql": "SELECT ...", "explanation": "..."}
        4. Safety checks: verify SELECT, reject DML, append LIMIT
        5. Return: {sql, explanation}
        ↓
    BigQuery Runner:
        1. Init client: bigquery.Client(project=settings.GCP_PROJECT_ID)
        2. Execute: client.query(sql, job_config={use_legacy_sql: False})
        3. Convert: [dict(row.items()) for row in result]
        4. Return: rows (list of dicts)
        ↓
    Chat API: Build assistant message
        {role: "assistant", content: explanation + "\n\n[10 rows shown]"}
        ↓
    Chat API: Return ChatResponse
        {messages: [...], sql: "SELECT ...", explanation: "...", rows: [...], error: None}
        ↓
    Chat UI: Render messages + table
```

#### Error Handling Flow

```
User → Chat UI → POST /api/v1/nlq/chat
    ↓
    LLM SQL Generator: Call Ollama
        ↓ (Ollama timeout / invalid JSON)
        ✗ Raise SqlGenerationError("LLM failed to generate valid SQL")
        ↓
    Chat API: Catch SqlGenerationError
        ↓
        Build assistant error message:
        {role: "assistant", content: "Sorry, I couldn't generate a query..."}
        ↓
        Return ChatResponse:
        {messages: [...], sql: None, explanation: None, rows: None, 
         error: "LLM failed to generate valid SQL"}
        ↓
    Chat UI: Display error in red box
```

## Detailed Design

### 1. Schema Context Module (`nlq/schema_context.py`)

**Purpose**: Provide BigQuery schema metadata and LLM system prompt

**Data Structures**:

```python
from dataclasses import dataclass
from typing import List

@dataclass
class TableSchema:
    """BigQuery table schema for LLM context."""
    table_name: str
    description: str
    columns: List[dict]  # [{"name": "region_id", "type": "STRING", "description": "..."}]

@dataclass
class SchemaContext:
    """Complete schema context for LLM prompt."""
    dataset_id: str
    tables: List[TableSchema]
    system_prompt: str
    few_shot_examples: List[dict]  # [{"question": "...", "sql": "...", "explanation": "..."}]
```

**System Prompt Template**:

```python
SYSTEM_PROMPT = """You are a BigQuery SQL generator for EduScale analytics.

Your role: Generate safe, read-only SQL queries based on user questions.

Available Tables (dataset: {dataset_id}):

1. fact_assessment
   - region_id (STRING): Region identifier
   - student_id (STRING): Student identifier  
   - date (DATE): Assessment date
   - subject (STRING): Academic subject (math, reading, etc.)
   - test_score (FLOAT64): Score 0-100
   - file_id (STRING): Source file identifier
   Partitioned by: date
   Clustered by: region_id

2. fact_intervention
   - region_id (STRING): Region identifier
   - intervention_id (STRING): Intervention identifier
   - intervention_type (STRING): Type of intervention
   - start_date (DATE): Start date
   - end_date (DATE): End date
   - participants_count (INT64): Number of participants
   Partitioned by: start_date
   Clustered by: region_id

3. fact_attendance
   - region_id (STRING): Region identifier
   - student_id (STRING): Student identifier
   - date (DATE): Attendance date
   - status (STRING): present, absent, late
   Partitioned by: date
   Clustered by: region_id

4. dim_region
   - region_id (STRING): Primary key
   - region_name (STRING): Display name
   - from_date (DATE): Valid from
   - to_date (DATE): Valid to

5. dim_school
   - school_name (STRING): Primary key
   - region_id (STRING): Parent region
   - from_date (DATE): Valid from
   - to_date (DATE): Valid to

6. dim_time
   - date (DATE): Primary key
   - year (INT64): Year
   - month (INT64): Month (1-12)
   - quarter (INT64): Quarter (1-4)
   - day_of_week (INT64): Day of week (1=Sunday)

7. observations
   - observation_id (STRING): Primary key
   - region_id (STRING): Region identifier
   - file_id (STRING): Source file
   - text_content (STRING): Free-form text (PDF content, audio transcripts, feedback)
   - detected_entities (ARRAY<STRING>): Extracted entity mentions
   - sentiment_score (FLOAT64): -1.0 to +1.0
   - created_at (TIMESTAMP): Creation timestamp
   Partitioned by: created_at
   Clustered by: region_id

STRICT RULES:
1. ONLY generate SELECT statements
2. NEVER use: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, MERGE
3. ALWAYS use dataset prefix: {dataset_id}.table_name
4. ALWAYS add LIMIT clause (default LIMIT 100 if user doesn't specify)
5. Use JOINs when crossing tables (e.g., fact_assessment JOIN dim_region ON region_id)
6. For date filters, use DATE() function: WHERE date >= DATE('2024-01-01')
7. For aggregations, use GROUP BY with column references

OUTPUT FORMAT (JSON only, no markdown, no explanation outside JSON):
{{
  "sql": "SELECT ... FROM {dataset_id}.table_name WHERE ... LIMIT 100",
  "explanation": "This query retrieves [brief 1-2 sentence explanation for user]"
}}

FEW-SHOT EXAMPLES:

User: "Compare Region A and Region B by average test performance in the first 6 months"
{{
  "sql": "SELECT r.region_name, AVG(a.test_score) as avg_score, COUNT(*) as test_count FROM {dataset_id}.fact_assessment a JOIN {dataset_id}.dim_region r ON a.region_id = r.region_id WHERE r.region_name IN ('Region A', 'Region B') AND a.date >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH) GROUP BY r.region_name ORDER BY avg_score DESC LIMIT 100",
  "explanation": "This query compares average test scores between Region A and B over the last 6 months."
}}

User: "Which interventions produced the largest improvement in Region A?"
{{
  "sql": "SELECT i.intervention_type, COUNT(*) as intervention_count, SUM(i.participants_count) as total_participants FROM {dataset_id}.fact_intervention i WHERE i.region_id = 'region-a' GROUP BY i.intervention_type ORDER BY intervention_count DESC LIMIT 100",
  "explanation": "This query lists interventions in Region A ordered by frequency."
}}

User: "Show math scores trend for Region A over the last year"
{{
  "sql": "SELECT t.year, t.month, AVG(a.test_score) as avg_score FROM {dataset_id}.fact_assessment a JOIN {dataset_id}.dim_time t ON a.date = t.date WHERE a.region_id = 'region-a' AND a.subject = 'math' AND a.date >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR) GROUP BY t.year, t.month ORDER BY t.year, t.month LIMIT 100",
  "explanation": "This query shows monthly average math scores in Region A over the past year."
}}

User: "Find feedback mentioning teacher Petr"
{{
  "sql": "SELECT observation_id, text_content, sentiment_score, created_at FROM {dataset_id}.observations WHERE LOWER(text_content) LIKE '%petr%' ORDER BY created_at DESC LIMIT 100",
  "explanation": "This query searches observations for mentions of 'Petr' and returns recent entries."
}}

Now generate SQL for the user's question. Return ONLY the JSON, nothing else.
"""
```

**Interface**:

```python
def load_schema_context() -> SchemaContext:
    """Load BigQuery schema context from settings.
    
    Returns:
        SchemaContext with tables, system prompt, and few-shot examples
    """
    dataset_id = settings.BIGQUERY_DATASET_ID
    
    tables = [
        TableSchema(
            table_name=f"{dataset_id}.fact_assessment",
            description="Student assessment scores",
            columns=[
                {"name": "region_id", "type": "STRING", "description": "Region identifier"},
                {"name": "student_id", "type": "STRING", "description": "Student identifier"},
                {"name": "date", "type": "DATE", "description": "Assessment date"},
                {"name": "subject", "type": "STRING", "description": "Academic subject"},
                {"name": "test_score", "type": "FLOAT64", "description": "Score 0-100"},
            ]
        ),
        # ... other tables
    ]
    
    system_prompt = SYSTEM_PROMPT.format(dataset_id=dataset_id)
    
    few_shot_examples = [
        {
            "question": "Compare Region A and Region B by average test performance",
            "sql": "SELECT r.region_name, AVG(a.test_score) as avg_score ...",
            "explanation": "This query compares average test scores between regions"
        },
        # ... more examples
    ]
    
    return SchemaContext(
        dataset_id=dataset_id,
        tables=tables,
        system_prompt=system_prompt,
        few_shot_examples=few_shot_examples
    )

def get_system_prompt() -> str:
    """Get formatted system prompt for LLM.
    
    Returns:
        System prompt string with schema context and rules
    """
    context = load_schema_context()
    return context.system_prompt
```

**Implementation Notes**:
- Schema is loaded once at module import time and cached
- Dataset ID is injected from settings (no hardcoding)
- Few-shot examples are realistic queries validated against staging data
- System prompt emphasizes safety rules and JSON output format

### 2. LLM SQL Generation Module (`nlq/llm_sql.py`)

**Purpose**: Generate SQL from natural language using Ollama + safety validation

**Custom Exceptions**:

```python
class SqlGenerationError(Exception):
    """Raised when SQL generation fails."""
    pass

class SqlSafetyError(Exception):
    """Raised when generated SQL fails safety checks."""
    pass
```

**Main Function**:

```python
def generate_sql_from_nl(
    user_query: str,
    history: list[dict[str, str]] | None = None
) -> dict[str, str]:
    """Generate SQL from natural language query.
    
    Args:
        user_query: User's question in plain text
        history: Optional conversation history (MVP: unused)
        
    Returns:
        dict with keys: "sql" (validated SQL), "explanation" (user-friendly text)
        
    Raises:
        SqlGenerationError: When LLM fails or returns invalid response
        SqlSafetyError: When generated SQL fails safety checks
    """
    # 1. Load system prompt
    system_prompt = get_system_prompt()
    
    # 2. Compose messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]
    
    # 3. Call Ollama
    try:
        response_text = _call_ollama(messages)
    except Exception as e:
        logger.error(f"Ollama call failed: {e}", extra={"user_query": user_query})
        raise SqlGenerationError(f"LLM service unavailable: {e}")
    
    # 4. Parse JSON response
    try:
        response_json = json.loads(response_text.strip())
        sql = response_json["sql"]
        explanation = response_json["explanation"]
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Invalid LLM response: {response_text}", extra={"user_query": user_query})
        raise SqlGenerationError(f"LLM returned invalid response: {e}")
    
    # 5. Apply safety checks
    safe_sql = _validate_and_fix_sql(sql, user_query)
    
    # 6. Return result
    return {
        "sql": safe_sql,
        "explanation": explanation
    }
```

**Safety Validation**:

```python
def _validate_and_fix_sql(sql: str, user_query: str) -> str:
    """Validate SQL safety and apply fixes.
    
    Args:
        sql: Generated SQL query
        user_query: Original user question (for logging)
        
    Returns:
        Validated and potentially modified SQL
        
    Raises:
        SqlSafetyError: When SQL fails safety checks
    """
    # Normalize SQL for checks
    sql_normalized = sql.strip()
    sql_lower = sql_normalized.lower()
    
    # Check 1: Must be SELECT
    if not sql_lower.startswith("select"):
        logger.warning(f"Non-SELECT SQL rejected", extra={
            "user_query": user_query,
            "generated_sql": sql
        })
        raise SqlSafetyError("Only SELECT queries are allowed")
    
    # Check 2: Reject forbidden keywords
    FORBIDDEN_KEYWORDS = [
        "insert", "update", "delete", "drop", "alter", 
        "create", "truncate", "merge", "grant", "revoke"
    ]
    for keyword in FORBIDDEN_KEYWORDS:
        # Use word boundaries to avoid false positives (e.g., "deleted_at" column)
        if re.search(rf'\b{keyword}\b', sql_lower):
            logger.warning(f"Forbidden keyword rejected: {keyword}", extra={
                "user_query": user_query,
                "generated_sql": sql
            })
            raise SqlSafetyError(f"Forbidden operation: {keyword.upper()}")
    
    # Check 3: Verify table names (must reference known dataset)
    dataset_id = settings.BIGQUERY_DATASET_ID
    if dataset_id not in sql_lower:
        logger.warning(f"Missing dataset prefix", extra={
            "user_query": user_query,
            "generated_sql": sql,
            "expected_dataset": dataset_id
        })
        # Auto-fix: This should be caught in LLM prompt, but log warning
    
    # Check 4: Ensure LIMIT clause exists
    if "limit" not in sql_lower:
        sql_normalized = sql_normalized.rstrip(";")  # Remove trailing semicolon if present
        sql_normalized += f" LIMIT {settings.NLQ_MAX_RESULTS}"
        logger.info(f"Added LIMIT clause", extra={
            "user_query": user_query,
            "limit": settings.NLQ_MAX_RESULTS
        })
    
    # Check 5: Verify reasonable LIMIT value
    limit_match = re.search(r'limit\s+(\d+)', sql_lower)
    if limit_match:
        limit_value = int(limit_match.group(1))
        if limit_value > settings.NLQ_MAX_RESULTS:
            # Replace with max allowed
            sql_normalized = re.sub(
                r'limit\s+\d+',
                f'LIMIT {settings.NLQ_MAX_RESULTS}',
                sql_normalized,
                flags=re.IGNORECASE
            )
            logger.info(f"Reduced LIMIT from {limit_value} to {settings.NLQ_MAX_RESULTS}")
    
    return sql_normalized
```

**Ollama Client**:

```python
def _call_ollama(messages: list[dict[str, str]]) -> str:
    """Call Ollama API for chat completion.
    
    Args:
        messages: List of message dicts with "role" and "content"
        
    Returns:
        Response text from LLM
        
    Raises:
        requests.RequestException: When API call fails
    """
    import requests
    
    endpoint = settings.LLM_ENDPOINT
    model = settings.LLM_MODEL
    
    # Ollama /api/generate endpoint (simple prompt-response)
    # Compose full prompt from messages
    prompt_parts = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            prompt_parts.append(f"<system>\n{content}\n</system>")
        elif role == "user":
            prompt_parts.append(f"<user>\n{content}\n</user>")
    
    full_prompt = "\n\n".join(prompt_parts)
    
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for deterministic SQL
            "num_predict": 500,  # Limit output tokens
        }
    }
    
    logger.info(f"Calling Ollama", extra={
        "endpoint": endpoint,
        "model": model,
        "prompt_length": len(full_prompt)
    })
    
    try:
        response = requests.post(
            f"{endpoint}/api/generate",
            json=payload,
            timeout=settings.NLQ_QUERY_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        response_json = response.json()
        return response_json["response"]
    except requests.Timeout:
        logger.error("Ollama request timed out")
        raise SqlGenerationError("LLM request timed out")
    except requests.RequestException as e:
        logger.error(f"Ollama request failed: {e}")
        raise SqlGenerationError(f"LLM service error: {e}")
```

**Logging Strategy**:

```python
# Log all SQL generation attempts
logger.info("SQL generation started", extra={
    "user_query": user_query,
    "history_length": len(history) if history else 0
})

# Log LLM response
logger.info("LLM response received", extra={
    "response_length": len(response_text),
    "parse_success": True/False
})

# Log safety checks
logger.info("SQL safety validation passed", extra={
    "sql_length": len(safe_sql),
    "limit_added": True/False,
    "limit_value": 100
})

# Log errors with context
logger.error("SQL generation failed", extra={
    "user_query": user_query,
    "error_type": "SqlSafetyError",
    "error_message": str(e),
    "generated_sql": sql  # Include for debugging
})
```

### 3. BigQuery Query Engine (`nlq/bq_query_engine.py`)

**Purpose**: Execute validated SQL against BigQuery and return results

**Main Function**:

```python
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
import logging

logger = logging.getLogger(__name__)

class QueryExecutionError(Exception):
    """Raised when BigQuery query execution fails."""
    pass

def run_analytics_query(sql: str) -> list[dict[str, object]]:
    """Execute SQL query against BigQuery and return results.
    
    Args:
        sql: Validated SQL query (assumed safe from llm_sql module)
        
    Returns:
        List of row dictionaries (max NLQ_MAX_RESULTS rows)
        
    Raises:
        QueryExecutionError: When query execution fails
    """
    # 1. Initialize BigQuery client
    project_id = settings.GCP_PROJECT_ID
    client = bigquery.Client(project=project_id)
    
    # 2. Configure query job
    job_config = bigquery.QueryJobConfig(
        use_legacy_sql=False,  # Standard SQL
    )
    
    # Optional: Set cost control
    if settings.BQ_MAX_BYTES_BILLED:
        job_config.maximum_bytes_billed = settings.BQ_MAX_BYTES_BILLED
    
    # 3. Execute query
    logger.info("Executing BigQuery query", extra={
        "sql": sql,
        "project": project_id,
        "max_bytes_billed": settings.BQ_MAX_BYTES_BILLED
    })
    
    try:
        query_job = client.query(sql, job_config=job_config)
        result = query_job.result()  # Wait for completion
    except GoogleCloudError as e:
        logger.error("BigQuery query failed", extra={
            "sql": sql,
            "error": str(e),
            "error_type": type(e).__name__
        })
        # Sanitize error message for user
        user_message = _sanitize_bigquery_error(e)
        raise QueryExecutionError(user_message)
    
    # 4. Convert to list of dicts
    rows = []
    for row in result:
        rows.append(dict(row.items()))
        if len(rows) >= settings.NLQ_MAX_RESULTS:
            break  # Limit rows returned
    
    # 5. Log metrics
    logger.info("BigQuery query succeeded", extra={
        "row_count": len(rows),
        "bytes_processed": query_job.total_bytes_processed,
        "bytes_billed": query_job.total_bytes_billed,
        "cache_hit": query_job.cache_hit,
        "execution_time_ms": query_job.ended - query_job.started if query_job.ended else None
    })
    
    return rows

def _sanitize_bigquery_error(error: Exception) -> str:
    """Convert BigQuery error to user-friendly message.
    
    Args:
        error: Original BigQuery exception
        
    Returns:
        Sanitized error message safe to show to users
    """
    error_str = str(error).lower()
    
    # Common error patterns
    if "not found" in error_str:
        return "Table or column not found. Please rephrase your question."
    elif "permission" in error_str or "access denied" in error_str:
        return "Permission denied accessing data. Please contact support."
    elif "timeout" in error_str or "deadline" in error_str:
        return "Query took too long to execute. Try a more specific question."
    elif "quota" in error_str or "limit exceeded" in error_str:
        return "Query limit exceeded. Please try again later."
    elif "syntax" in error_str:
        return "Invalid SQL generated. Please rephrase your question."
    else:
        # Generic error (hide implementation details)
        return "Query execution failed. Please try a different question."
```

**Connection Management**:

```python
# Option 1: Create client per request (simpler, Cloud Run handles connection pooling)
def run_analytics_query(sql: str) -> list[dict[str, object]]:
    client = bigquery.Client(project=settings.GCP_PROJECT_ID)
    # ... execute query
    
# Option 2: Reuse client (better performance, requires app-level caching)
_bigquery_client = None

def get_bigquery_client() -> bigquery.Client:
    """Get or create BigQuery client (singleton)."""
    global _bigquery_client
    if _bigquery_client is None:
        _bigquery_client = bigquery.Client(project=settings.GCP_PROJECT_ID)
    return _bigquery_client

def run_analytics_query(sql: str) -> list[dict[str, object]]:
    client = get_bigquery_client()
    # ... execute query
```

**Recommendation**: Use Option 1 for MVP (simpler, sufficient for demo). Consider Option 2 if performance becomes an issue.

### 4. Chat API Endpoint (`api/v1/routes_nlq.py`)

**Purpose**: FastAPI endpoint for chat interactions

**Pydantic Models**:

```python
from typing import Literal, Optional
from pydantic import BaseModel

class ChatMessage(BaseModel):
    """Single message in chat conversation."""
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    """Request payload for chat endpoint."""
    messages: list[ChatMessage]

class ChatResponse(BaseModel):
    """Response payload for chat endpoint."""
    messages: list[ChatMessage]
    sql: Optional[str] = None
    explanation: Optional[str] = None
    rows: Optional[list[dict]] = None
    error: Optional[str] = None
```

**API Route**:

```python
from fastapi import APIRouter, HTTPException
import logging
from uuid import uuid4

from eduscale.nlq.llm_sql import generate_sql_from_nl, SqlGenerationError, SqlSafetyError
from eduscale.nlq.bq_query_engine import run_analytics_query, QueryExecutionError
from eduscale.core.config import settings

router = APIRouter(prefix="/api/v1/nlq", tags=["nlq"])
logger = logging.getLogger(__name__)

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Natural language query chat endpoint.
    
    Accepts conversation messages, generates SQL from latest user message,
    executes query, and returns results formatted as assistant message.
    
    Args:
        request: ChatRequest with conversation messages
        
    Returns:
        ChatResponse with updated messages, SQL, and results
        
    Raises:
        HTTPException: 400 for invalid requests, 500 for server errors
    """
    # Generate correlation ID for tracing
    correlation_id = str(uuid4())
    
    # Check feature toggle
    if not settings.NLQ_ENABLED:
        logger.warning("NLQ feature disabled", extra={"correlation_id": correlation_id})
        raise HTTPException(
            status_code=503,
            detail="Natural language query feature is currently disabled"
        )
    
    # Validate request
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    # Extract latest user message
    user_messages = [msg for msg in request.messages if msg.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found")
    
    latest_user_message = user_messages[-1]
    user_query = latest_user_message.content
    
    logger.info("Chat request received", extra={
        "correlation_id": correlation_id,
        "user_query": user_query,
        "message_count": len(request.messages)
    })
    
    # Build conversation history (optional for MVP)
    history = [{"role": msg.role, "content": msg.content} for msg in request.messages[:-1]]
    
    try:
        # Step 1: Generate SQL from user query
        sql_result = generate_sql_from_nl(user_query, history=history)
        sql = sql_result["sql"]
        explanation = sql_result["explanation"]
        
        logger.info("SQL generated successfully", extra={
            "correlation_id": correlation_id,
            "sql_length": len(sql)
        })
        
        # Step 2: Execute query
        rows = run_analytics_query(sql)
        
        logger.info("Query executed successfully", extra={
            "correlation_id": correlation_id,
            "row_count": len(rows)
        })
        
        # Step 3: Build assistant response
        row_count_text = f"{len(rows)} rows" if len(rows) > 0 else "No results"
        assistant_content = f"{explanation}\n\n{row_count_text} returned."
        
        assistant_message = ChatMessage(role="assistant", content=assistant_content)
        updated_messages = request.messages + [assistant_message]
        
        # Step 4: Return successful response
        return ChatResponse(
            messages=updated_messages,
            sql=sql,
            explanation=explanation,
            rows=rows[:20],  # Limit preview to 20 rows
            error=None
        )
        
    except (SqlGenerationError, SqlSafetyError) as e:
        # LLM or safety check failed
        logger.warning("SQL generation failed", extra={
            "correlation_id": correlation_id,
            "error_type": type(e).__name__,
            "error_message": str(e)
        })
        
        error_message = f"I couldn't generate a valid query: {str(e)}"
        assistant_message = ChatMessage(
            role="assistant",
            content=error_message
        )
        updated_messages = request.messages + [assistant_message]
        
        return ChatResponse(
            messages=updated_messages,
            sql=None,
            explanation=None,
            rows=None,
            error=str(e)
        )
        
    except QueryExecutionError as e:
        # BigQuery execution failed
        logger.error("Query execution failed", extra={
            "correlation_id": correlation_id,
            "sql": sql,
            "error_message": str(e)
        })
        
        error_message = f"Query execution failed: {str(e)}"
        assistant_message = ChatMessage(
            role="assistant",
            content=error_message
        )
        updated_messages = request.messages + [assistant_message]
        
        return ChatResponse(
            messages=updated_messages,
            sql=sql,  # Include attempted SQL for debugging
            explanation=explanation,
            rows=None,
            error=str(e)
        )
        
    except Exception as e:
        # Unexpected error
        logger.error("Unexpected error in chat endpoint", extra={
            "correlation_id": correlation_id,
            "error_type": type(e).__name__,
            "error_message": str(e)
        }, exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail="Internal server error. Please try again."
        )
```

**Register Route in `main.py`**:

```python
# src/eduscale/main.py

from eduscale.api.v1.routes_nlq import router as nlq_router

def create_app() -> FastAPI:
    # ... existing code
    
    # Register NLQ router
    app.include_router(nlq_router)
    
    return app
```

### 5. Chat User Interface (`ui/templates/chat.html`)

**Purpose**: Simple web UI for chat interaction

**HTML Structure**:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EduScale Analytics Chat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        
        h1 { margin-bottom: 20px; color: #333; }
        
        #chat-history {
            border: 1px solid #ddd;
            border-radius: 8px;
            height: 500px;
            overflow-y: auto;
            padding: 20px;
            background: #f9f9f9;
            margin-bottom: 20px;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 12px;
            border-radius: 8px;
            max-width: 80%;
        }
        
        .message.user {
            background: #007bff;
            color: white;
            margin-left: auto;
        }
        
        .message.assistant {
            background: white;
            border: 1px solid #ddd;
        }
        
        .message-role {
            font-weight: bold;
            margin-bottom: 5px;
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        .error-message {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 12px;
            border-radius: 8px;
            margin-top: 10px;
        }
        
        .sql-block {
            background: #f4f4f4;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            margin-top: 10px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            overflow-x: auto;
        }
        
        .sql-toggle {
            cursor: pointer;
            color: #007bff;
            text-decoration: underline;
            margin-top: 10px;
            display: inline-block;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 0.9em;
        }
        
        table th {
            background: #f0f0f0;
            padding: 8px;
            text-align: left;
            border: 1px solid #ddd;
        }
        
        table td {
            padding: 8px;
            border: 1px solid #ddd;
        }
        
        #input-area {
            display: flex;
            gap: 10px;
        }
        
        #user-input {
            flex: 1;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 1em;
        }
        
        #send-button {
            padding: 12px 24px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
        }
        
        #send-button:hover {
            background: #0056b3;
        }
        
        #send-button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .loading {
            color: #666;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>EduScale Analytics Chat</h1>
        <div id="chat-history"></div>
        <div id="input-area">
            <input 
                type="text" 
                id="user-input" 
                placeholder="Ask a question about your data..."
                autocomplete="off"
            />
            <button id="send-button">Send</button>
        </div>
    </div>

    <script>
        // Chat state
        let messages = [];
        
        // DOM elements
        const chatHistory = document.getElementById('chat-history');
        const userInput = document.getElementById('user-input');
        const sendButton = document.getElementById('send-button');
        
        // Event listeners
        sendButton.addEventListener('click', sendMessage);
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
        
        async function sendMessage() {
            const userText = userInput.value.trim();
            if (!userText) return;
            
            // Add user message to state
            messages.push({ role: 'user', content: userText });
            
            // Clear input and disable button
            userInput.value = '';
            sendButton.disabled = true;
            
            // Render user message
            renderMessages();
            
            // Show loading
            showLoading();
            
            try {
                // Call API
                const response = await fetch('/api/v1/nlq/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ messages })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                // Update messages from server response
                messages = data.messages;
                
                // Render all messages
                renderMessages();
                
                // Render results table if available
                if (data.rows && data.rows.length > 0) {
                    renderResultsTable(data.rows);
                }
                
                // Render SQL if available
                if (data.sql) {
                    renderSql(data.sql);
                }
                
                // Show error if present
                if (data.error) {
                    showError(data.error);
                }
                
            } catch (error) {
                console.error('Error calling chat API:', error);
                showError(`Failed to send message: ${error.message}`);
            } finally {
                // Re-enable button
                sendButton.disabled = false;
                userInput.focus();
            }
        }
        
        function renderMessages() {
            chatHistory.innerHTML = '';
            
            messages.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${msg.role}`;
                
                const roleDiv = document.createElement('div');
                roleDiv.className = 'message-role';
                roleDiv.textContent = msg.role === 'user' ? 'You' : 'Assistant';
                
                const contentDiv = document.createElement('div');
                contentDiv.textContent = msg.content;
                
                messageDiv.appendChild(roleDiv);
                messageDiv.appendChild(contentDiv);
                chatHistory.appendChild(messageDiv);
            });
            
            // Scroll to bottom
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
        
        function renderResultsTable(rows) {
            if (rows.length === 0) return;
            
            const lastMessage = chatHistory.lastElementChild;
            
            const table = document.createElement('table');
            
            // Header row
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            Object.keys(rows[0]).forEach(key => {
                const th = document.createElement('th');
                th.textContent = key;
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            table.appendChild(thead);
            
            // Data rows (limit to 10)
            const tbody = document.createElement('tbody');
            rows.slice(0, 10).forEach(row => {
                const tr = document.createElement('tr');
                Object.values(row).forEach(value => {
                    const td = document.createElement('td');
                    td.textContent = value !== null ? value : '(null)';
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });
            table.appendChild(tbody);
            
            lastMessage.appendChild(table);
            
            if (rows.length > 10) {
                const moreText = document.createElement('div');
                moreText.textContent = `... and ${rows.length - 10} more rows`;
                moreText.style.marginTop = '10px';
                moreText.style.fontStyle = 'italic';
                lastMessage.appendChild(moreText);
            }
        }
        
        function renderSql(sql) {
            const lastMessage = chatHistory.lastElementChild;
            
            const toggleLink = document.createElement('div');
            toggleLink.className = 'sql-toggle';
            toggleLink.textContent = 'Show SQL ▼';
            
            const sqlBlock = document.createElement('div');
            sqlBlock.className = 'sql-block';
            sqlBlock.textContent = sql;
            sqlBlock.style.display = 'none';
            
            toggleLink.addEventListener('click', () => {
                if (sqlBlock.style.display === 'none') {
                    sqlBlock.style.display = 'block';
                    toggleLink.textContent = 'Hide SQL ▲';
                } else {
                    sqlBlock.style.display = 'none';
                    toggleLink.textContent = 'Show SQL ▼';
                }
            });
            
            lastMessage.appendChild(toggleLink);
            lastMessage.appendChild(sqlBlock);
        }
        
        function showLoading() {
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message assistant loading';
            loadingDiv.id = 'loading-message';
            loadingDiv.textContent = 'Thinking...';
            chatHistory.appendChild(loadingDiv);
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
        
        function showError(errorText) {
            const lastMessage = chatHistory.lastElementChild;
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = `Error: ${errorText}`;
            
            lastMessage.appendChild(errorDiv);
        }
        
        // Remove loading message when rendering results
        const originalRender = renderMessages;
        renderMessages = function() {
            const loading = document.getElementById('loading-message');
            if (loading) loading.remove();
            originalRender();
        };
    </script>
</body>
</html>
```

**UI Route**:

```python
# In routes_nlq.py

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

templates = Jinja2Templates(directory="src/eduscale/ui/templates")

@router.get("/chat", response_class=HTMLResponse)
async def chat_ui(request: Request):
    """Render chat UI page."""
    return templates.TemplateResponse("chat.html", {"request": request})
```

### 6. Configuration Updates

**Settings Class Extensions** (`core/config.py`):

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # NLQ Configuration
    NLQ_ENABLED: bool = True
    LLM_MODEL: str = "llama3.2:1b"
    LLM_ENDPOINT: str = "http://localhost:11434"
    BQ_MAX_BYTES_BILLED: Optional[int] = None  # None = no limit
    NLQ_MAX_RESULTS: int = 100
    NLQ_QUERY_TIMEOUT_SECONDS: int = 60
```

**Environment Variables** (`.env.example`):

```bash
# NLQ Feature Configuration
NLQ_ENABLED=true
LLM_MODEL=llama3.2:1b
LLM_ENDPOINT=http://localhost:11434
BQ_MAX_BYTES_BILLED=1000000000  # 1GB limit (optional)
NLQ_MAX_RESULTS=100
NLQ_QUERY_TIMEOUT_SECONDS=60
```

### 7. Container and Deployment

**Dockerfile Updates**:

```dockerfile
# Use existing Python base image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ /app/src/
COPY config/ /app/config/
WORKDIR /app

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Starting Ollama service..."\n\
ollama serve &\n\
OLLAMA_PID=$!\n\
\n\
echo "Waiting for Ollama to be ready..."\n\
for i in {1..30}; do\n\
  if curl -s http://localhost:11434/api/tags > /dev/null; then\n\
    echo "Ollama is ready!"\n\
    break\n\
  fi\n\
  if [ $i -eq 30 ]; then\n\
    echo "Ollama failed to start"\n\
    exit 1\n\
  fi\n\
  sleep 1\n\
done\n\
\n\
echo "Pulling LLM model..."\n\
ollama pull ${LLM_MODEL:-llama3.2:1b}\n\
\n\
echo "Starting FastAPI application..."\n\
exec uvicorn eduscale.main:app --host 0.0.0.0 --port ${PORT:-8080}' > /start.sh \
&& chmod +x /start.sh

# Use startup script as entrypoint
CMD ["/start.sh"]
```

**Cloud Run Configuration**:

```yaml
# infra/nlq-config.yaml (example Cloud Run config)
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: eduscale-engine
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: '10'
        autoscaling.knative.dev/minScale: '0'
    spec:
      containerConcurrency: 5
      timeoutSeconds: 300
      containers:
      - image: gcr.io/PROJECT_ID/eduscale-engine:latest
        resources:
          limits:
            memory: 8Gi
            cpu: '2'
        env:
        - name: NLQ_ENABLED
          value: 'true'
        - name: LLM_MODEL
          value: 'llama3.2:1b'
        - name: LLM_ENDPOINT
          value: 'http://localhost:11434'
        - name: GCP_PROJECT_ID
          value: 'PROJECT_ID'
        - name: BIGQUERY_DATASET_ID
          value: 'jedouscale_core'
        - name: BQ_MAX_BYTES_BILLED
          value: '1000000000'  # 1GB
        - name: NLQ_MAX_RESULTS
          value: '100'
```

## Testing Strategy

### Unit Tests

#### 1. Schema Context Tests (`tests/test_schema_context.py`)

```python
def test_load_schema_context():
    """Test schema context loading."""
    context = load_schema_context()
    assert context.dataset_id == settings.BIGQUERY_DATASET_ID
    assert len(context.tables) > 0
    assert "fact_assessment" in [t.table_name for t in context.tables]

def test_system_prompt_contains_safety_rules():
    """Test system prompt includes safety rules."""
    prompt = get_system_prompt()
    assert "ONLY generate SELECT" in prompt
    assert "NEVER use: INSERT" in prompt
    assert "LIMIT" in prompt

def test_few_shot_examples_valid():
    """Test few-shot examples are valid SQL."""
    context = load_schema_context()
    for example in context.few_shot_examples:
        assert "sql" in example
        assert "explanation" in example
        assert example["sql"].strip().lower().startswith("select")
```

#### 2. LLM SQL Generation Tests (`tests/test_llm_sql.py`)

```python
@pytest.fixture
def mock_ollama_response():
    """Mock successful Ollama response."""
    return {
        "response": json.dumps({
            "sql": "SELECT * FROM jedouscale_core.fact_assessment LIMIT 100",
            "explanation": "This query retrieves assessment data"
        })
    }

def test_generate_sql_success(mocker, mock_ollama_response):
    """Test successful SQL generation."""
    mocker.patch("requests.post", return_value=MockResponse(200, mock_ollama_response))
    
    result = generate_sql_from_nl("Show me test scores")
    
    assert "sql" in result
    assert "explanation" in result
    assert "SELECT" in result["sql"]

def test_generate_sql_rejects_insert(mocker):
    """Test safety check rejects INSERT."""
    mocker.patch("requests.post", return_value=MockResponse(200, {
        "response": json.dumps({
            "sql": "INSERT INTO table VALUES (1)",
            "explanation": "Inserting data"
        })
    }))
    
    with pytest.raises(SqlSafetyError, match="Only SELECT"):
        generate_sql_from_nl("Add a record")

def test_generate_sql_adds_limit(mocker):
    """Test LIMIT clause is added if missing."""
    mocker.patch("requests.post", return_value=MockResponse(200, {
        "response": json.dumps({
            "sql": "SELECT * FROM jedouscale_core.fact_assessment",
            "explanation": "Get all data"
        })
    }))
    
    result = generate_sql_from_nl("Show all scores")
    
    assert "LIMIT" in result["sql"]
```

#### 3. BigQuery Engine Tests (`tests/test_bq_query_engine.py`)

```python
def test_run_query_success(mocker):
    """Test successful query execution."""
    mock_client = mocker.MagicMock()
    mock_result = [
        {"region_id": "A", "avg_score": 85.5},
        {"region_id": "B", "avg_score": 82.3}
    ]
    mock_client.query.return_value.result.return_value = [
        mocker.MagicMock(items=lambda: row.items()) for row in mock_result
    ]
    
    mocker.patch("google.cloud.bigquery.Client", return_value=mock_client)
    
    rows = run_analytics_query("SELECT * FROM table LIMIT 100")
    
    assert len(rows) == 2
    assert rows[0]["region_id"] == "A"

def test_run_query_handles_error(mocker):
    """Test query execution error handling."""
    mock_client = mocker.MagicMock()
    mock_client.query.side_effect = GoogleCloudError("Table not found")
    
    mocker.patch("google.cloud.bigquery.Client", return_value=mock_client)
    
    with pytest.raises(QueryExecutionError, match="not found"):
        run_analytics_query("SELECT * FROM nonexistent LIMIT 100")
```

### Integration Tests

#### 4. Chat Endpoint Tests (`tests/test_routes_nlq.py`)

```python
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    """Test client for FastAPI app."""
    from eduscale.main import app
    return TestClient(app)

def test_chat_endpoint_success(client, mocker):
    """Test successful chat interaction."""
    # Mock LLM response
    mocker.patch("eduscale.nlq.llm_sql.generate_sql_from_nl", return_value={
        "sql": "SELECT * FROM jedouscale_core.fact_assessment LIMIT 10",
        "explanation": "Retrieved assessment data"
    })
    
    # Mock BigQuery response
    mocker.patch("eduscale.nlq.bq_query_engine.run_analytics_query", return_value=[
        {"region_id": "A", "test_score": 85},
        {"region_id": "B", "test_score": 90}
    ])
    
    response = client.post("/api/v1/nlq/chat", json={
        "messages": [
            {"role": "user", "content": "Show me test scores"}
        ]
    })
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) == 2
    assert data["messages"][1]["role"] == "assistant"
    assert data["sql"] is not None
    assert len(data["rows"]) == 2

def test_chat_endpoint_handles_llm_error(client, mocker):
    """Test chat endpoint handles LLM errors gracefully."""
    mocker.patch("eduscale.nlq.llm_sql.generate_sql_from_nl", side_effect=SqlGenerationError("LLM failed"))
    
    response = client.post("/api/v1/nlq/chat", json={
        "messages": [
            {"role": "user", "content": "Invalid question"}
        ]
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["error"] is not None
    assert data["sql"] is None

def test_chat_endpoint_feature_disabled(client, mocker):
    """Test endpoint returns 503 when feature is disabled."""
    mocker.patch("eduscale.core.config.settings.NLQ_ENABLED", False)
    
    response = client.post("/api/v1/nlq/chat", json={
        "messages": [{"role": "user", "content": "Test"}]
    })
    
    assert response.status_code == 503
```

## Performance Considerations

### Expected Performance

- **Cold Start**: 30-60 seconds (Ollama startup + model loading)
- **Warm Request**: 5-15 seconds end-to-end
  - LLM Inference: 2-5 seconds (CPU-only, Llama 3.2 1B)
  - BigQuery Execution: 1-5 seconds (typical queries)
  - Network + Processing: 1-3 seconds

### Optimization Strategies

1. **Model Caching**: Ollama keeps model in memory after first load
2. **BigQuery Caching**: Leverage BigQuery's automatic result caching
3. **Client Pooling**: Reuse BigQuery client connection (singleton pattern)
4. **Concurrency Limits**: Set concurrency=5 to prevent memory exhaustion
5. **LIMIT Enforcement**: Always cap result sets to 100 rows

### Monitoring Metrics

Log key metrics for performance tuning:

```python
logger.info("Performance metrics", extra={
    "correlation_id": correlation_id,
    "llm_inference_ms": llm_end - llm_start,
    "query_execution_ms": query_end - query_start,
    "total_request_ms": total_end - total_start,
    "bytes_processed": query_job.total_bytes_processed,
    "cache_hit": query_job.cache_hit
})
```

## Security Considerations

### SQL Injection Prevention

- **Parameterization**: Not applicable (LLM generates full query, no user input interpolation)
- **Validation**: Multi-layer safety checks (regex, keyword detection, table allowlist)
- **Least Privilege**: Service account has `bigquery.dataViewer` (read-only), not `dataEditor`

### Data Privacy

- **Local LLM**: No user queries sent to external APIs
- **No Logging of Data**: Only metadata (query structure, row counts)
- **GCP Region**: All processing within configured region

### Cost Controls

- **LIMIT Clause**: Enforced on all queries (max 100 rows)
- **Bytes Billed**: Optional `BQ_MAX_BYTES_BILLED` cap
- **Timeout**: 60-second query timeout prevents runaway queries

## Deployment Checklist

- [ ] Ollama installed in Docker image
- [ ] Llama 3.2 1B model pulled during startup
- [ ] Cloud Run memory configured to 8GB
- [ ] Cloud Run CPU configured to 2 vCPUs
- [ ] Cloud Run concurrency set to 5
- [ ] Cloud Run timeout set to 300 seconds
- [ ] Service account has `bigquery.jobUser` and `bigquery.dataViewer` roles
- [ ] Environment variables configured (NLQ_ENABLED, LLM_MODEL, etc.)
- [ ] Few-shot examples tested against staging data
- [ ] Demo queries documented and validated
- [ ] Logs enabled with correlation IDs
- [ ] Error handling tested for common scenarios

## Future Enhancements (Out of Scope for MVP)

1. **Conversation History**: Store chat sessions in database with TTL
2. **Query Caching**: Cache common queries in Redis
3. **Query Suggestions**: Suggest questions based on schema
4. **Visualization**: Auto-generate charts from query results
5. **Multi-Language Support**: Support Czech/English prompts
6. **GPU Acceleration**: Use GPU-enabled Cloud Run for faster inference
7. **Fine-Tuned Model**: Fine-tune Llama on EduScale-specific queries
8. **Query Optimization**: Suggest index creation or query rewrites
9. **Data Export**: Export results to CSV/Excel
10. **Collaborative Features**: Share queries with team members

## Success Metrics

The NL→SQL Chat Interface MVP is successful when:

1. ✅ Users can query BigQuery using natural language
2. ✅ 3-5 demo queries work reliably (< 5s execution time)
3. ✅ System prevents data modification (100% SQL validation accuracy)
4. ✅ Performance meets targets (P95 < 15s end-to-end)
5. ✅ Code coverage >= 80%
6. ✅ Feature is demo-ready for pitch (UI + examples)
7. ✅ Documentation enables junior developer onboarding in < 30 min

