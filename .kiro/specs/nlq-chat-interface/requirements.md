# Requirements Document: NL→SQL Chat Interface

## Introduction

The NL→SQL Chat Interface is an MVP feature that enables users to query BigQuery analytics data using natural language questions. The system translates user questions into safe SQL queries using a local LLM (Llama via Ollama), executes them against BigQuery, and returns results in a conversational chat format. This feature democratizes access to analytics by removing the need for SQL knowledge while maintaining strict safety controls.

The interface operates within the existing FastAPI application on Google Cloud Run, leveraging Application Default Credentials for BigQuery access and Ollama for local LLM inference.

## Glossary

- **NLQ**: Natural Language Query - user questions in plain text
- **Ollama**: Local LLM runtime for running Llama models without external API calls
- **Schema Context**: Metadata about BigQuery tables and columns provided to the LLM
- **System Prompt**: Instructions given to the LLM defining its behavior and output format
- **Few-Shot Examples**: Sample questions and SQL queries included in the prompt to guide the LLM
- **SQL Safety Check**: Validation logic that ensures generated SQL is read-only and safe
- **Query Runner**: Component that executes SQL against BigQuery
- **Chat Session**: Stateless conversation (MVP does not persist history)

## Requirements

### Requirement 1: Schema Context Definition

**User Story:** As an AI engineer, I want a clear schema description for the LLM, so that it generates accurate SQL queries targeting the correct tables and columns.

#### Acceptance Criteria

1. THE Schema Context Module SHALL define BigQuery dataset name using BIGQUERY_DATASET_ID from settings
2. THE Schema Context Module SHALL document all analytics tables: fact_assessment, fact_intervention, fact_attendance, dim_region, dim_school, dim_time, observations
3. THE Schema Context Module SHALL include column names and data types for each table
4. THE Schema Context Module SHALL provide business descriptions for key columns (e.g., region_id, test_score, intervention_type)
5. THE Schema Context Module SHALL include join relationships between fact and dimension tables
6. THE Schema Context Module SHALL construct a system prompt that explains the LLM's role as a "BigQuery SQL generator for EduScale analytics"
7. THE Schema Context Module SHALL define strict SQL generation rules in the system prompt:
   - Only SELECT statements allowed
   - No data modification operations (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, MERGE)
   - Must use dataset prefix (e.g., jedouscale_core.) when referencing tables
   - Must include LIMIT clause (default 100 if not specified by user)
8. THE Schema Context Module SHALL specify JSON output format for LLM responses: {"sql": "...", "explanation": "..."}
9. THE Schema Context Module SHALL include 3-5 few-shot examples of common questions with ideal SQL and explanations
10. THE Schema Context Module SHALL provide examples relevant to educational analytics (region comparisons, intervention effectiveness, score trends)

### Requirement 2: LLM-Based SQL Generation

**User Story:** As a data analyst, I want natural language questions translated to SQL, so that I can query data without writing SQL manually.

#### Acceptance Criteria

1. THE SQL Generation Module SHALL implement function generate_sql_from_nl(user_query: str, history: list[dict] | None) -> dict
2. THE SQL Generation Module SHALL call Ollama via HTTP POST to /v1/chat or /api/generate endpoint
3. THE SQL Generation Module SHALL use LLM model specified in settings.LLM_MODEL (default: "llama3.2:1b")
4. THE SQL Generation Module SHALL use Ollama endpoint from settings.LLM_ENDPOINT (default: "http://localhost:11434")
5. THE SQL Generation Module SHALL compose messages with: system prompt (schema + rules) and user message (user_query)
6. THE SQL Generation Module SHALL parse LLM response as JSON to extract "sql" and "explanation" fields
7. WHEN JSON parsing fails, THE SQL Generation Module SHALL raise SqlGenerationError with details
8. WHEN "sql" or "explanation" keys are missing, THE SQL Generation Module SHALL raise SqlGenerationError
9. THE SQL Generation Module SHALL apply safety checks to generated SQL before returning
10. THE SQL Generation Module SHALL normalize SQL (strip whitespace, lowercase for checks)
11. THE SQL Generation Module SHALL verify SQL starts with "select" (case-insensitive)
12. THE SQL Generation Module SHALL reject SQL containing forbidden keywords: insert, update, delete, drop, alter, create, truncate, merge
13. THE SQL Generation Module SHALL verify SQL references only known table names from schema context
14. WHEN SQL does not contain LIMIT clause, THE SQL Generation Module SHALL append "LIMIT 100"
15. THE SQL Generation Module SHALL return dict: {"sql": safe_sql_string, "explanation": explanation_string}
16. THE SQL Generation Module SHALL log LLM calls with query, generated SQL, and safety check results
17. WHEN history parameter is provided, THE SQL Generation Module MAY include recent messages for context (MVP: optional)

### Requirement 3: BigQuery Query Execution

**User Story:** As a system engineer, I want generated SQL executed safely against BigQuery, so that users see actual data results.

#### Acceptance Criteria

1. THE Query Engine Module SHALL implement function run_analytics_query(sql: str) -> list[dict]
2. THE Query Engine Module SHALL initialize BigQuery client using default credentials: bigquery.Client(project=settings.GCP_PROJECT_ID)
3. THE Query Engine Module SHALL create QueryJobConfig with use_legacy_sql=False (Standard SQL)
4. THE Query Engine Module SHALL set maximum_bytes_billed from settings.BQ_MAX_BYTES_BILLED (if configured)
5. THE Query Engine Module SHALL execute query: client.query(sql, job_config=query_config)
6. THE Query Engine Module SHALL wait for query completion: job.result()
7. THE Query Engine Module SHALL convert result rows to list of dictionaries: [dict(row.items()) for row in result]
8. THE Query Engine Module SHALL limit returned rows to maximum 100 for chat display
9. WHEN BigQuery API errors occur, THE Query Engine Module SHALL log SQL and error details
10. WHEN BigQuery API errors occur, THE Query Engine Module SHALL raise QueryExecutionError with user-friendly message
11. THE Query Engine Module SHALL log query metadata: bytes_processed, cache_hit, execution_time_ms
12. THE Query Engine Module SHALL handle timeout errors gracefully

### Requirement 4: Chat API Endpoint

**User Story:** As a frontend developer, I want a REST API endpoint for chat interactions, so that I can build a conversational UI.

#### Acceptance Criteria

1. THE Chat API SHALL define Pydantic model ChatMessage with fields: role (Literal["user", "assistant"]), content (str)
2. THE Chat API SHALL define Pydantic model ChatRequest with field: messages (List[ChatMessage])
3. THE Chat API SHALL define Pydantic model ChatResponse with fields: messages (List[ChatMessage]), sql (Optional[str]), explanation (Optional[str]), rows (Optional[List[Dict]]), error (Optional[str])
4. THE Chat API SHALL implement POST endpoint at /api/v1/nlq/chat
5. WHEN request is received, THE Chat API SHALL extract latest user message (last item with role="user")
6. WHEN user message is extracted, THE Chat API SHALL call generate_sql_from_nl(user_text, history)
7. WHEN SQL generation succeeds, THE Chat API SHALL call run_analytics_query(sql)
8. WHEN query execution succeeds, THE Chat API SHALL build assistant message with explanation and key insights from results
9. WHEN query execution succeeds, THE Chat API SHALL append assistant message to messages list
10. WHEN query execution succeeds, THE Chat API SHALL return ChatResponse with: messages, sql, explanation, rows (preview), error=None
11. WHEN SQL generation fails, THE Chat API SHALL return ChatResponse with: user message, assistant error message, error details, sql=None, rows=None
12. WHEN query execution fails, THE Chat API SHALL return ChatResponse with: user message, assistant error message, error details, sql (attempted), rows=None
13. THE Chat API SHALL log all requests with user_query, generated_sql, row_count, and error (if any)
14. THE Chat API SHALL use correlation IDs for tracing requests across components
15. THE Chat API SHALL return HTTP 200 for successful responses (with or without errors in error field)
16. THE Chat API SHALL return HTTP 400 for malformed requests (invalid JSON, missing fields)
17. THE Chat API SHALL return HTTP 500 for unexpected server errors

### Requirement 5: Chat User Interface

**User Story:** As a data analyst, I want a simple web UI to type questions and see answers, so that I can interact with the NLQ system without API tools.

#### Acceptance Criteria

1. THE Chat UI SHALL provide HTML page served at /nlq/chat
2. THE Chat UI SHALL display scrollable chat history area showing all messages
3. THE Chat UI SHALL provide text input or textarea for user to type questions
4. THE Chat UI SHALL provide "Send" button to submit questions
5. THE Chat UI SHALL maintain client-side array of messages: [{role: "user"|"assistant", content: "..."}]
6. WHEN user clicks Send, THE Chat UI SHALL push user message to messages array
7. WHEN user clicks Send, THE Chat UI SHALL POST to /api/v1/nlq/chat with {messages: [...]}
8. WHEN response is received, THE Chat UI SHALL replace messages array with response.messages
9. WHEN response is received, THE Chat UI SHALL render all messages in chat area
10. WHEN response.rows is present, THE Chat UI SHALL render simple HTML table with first 10-20 rows
11. THE Chat UI SHALL optionally show response.sql in collapsible "Show SQL" block for transparency
12. THE Chat UI SHALL display response.error in red error message box if present
13. THE Chat UI SHALL use minimal styling (can be plain HTML/CSS, no complex framework required)
14. THE Chat UI SHALL handle loading state (disable Send button while request is pending)
15. THE Chat UI SHALL scroll to bottom of chat history when new messages appear
16. THE Chat UI SHALL clear input field after sending message

### Requirement 6: Configuration Management

**User Story:** As a DevOps engineer, I want all NLQ settings configurable via environment variables, so that the same code runs in different environments.

#### Acceptance Criteria

1. THE Settings class SHALL include LLM_MODEL: str with default "llama3.2:1b"
2. THE Settings class SHALL include LLM_ENDPOINT: str with default "http://localhost:11434"
3. THE Settings class SHALL include BQ_MAX_BYTES_BILLED: Optional[int] with default None (no limit)
4. THE Settings class SHALL include NLQ_ENABLED: bool with default True (feature toggle)
5. THE Settings class SHALL include NLQ_MAX_RESULTS: int with default 100
6. THE Settings class SHALL include NLQ_QUERY_TIMEOUT_SECONDS: int with default 60
7. THE Settings class SHALL ensure GCP_PROJECT_ID is set (required for BigQuery client)
8. THE Settings class SHALL ensure BIGQUERY_DATASET_ID is set (required for schema context)
9. WHEN NLQ_ENABLED is False, THE Chat API endpoint SHALL return 503 Service Unavailable with message "NLQ feature is disabled"
10. ALL configuration values SHALL be loaded from environment variables via Pydantic Settings

### Requirement 7: Safety and Security

**User Story:** As a security engineer, I want strict controls on generated SQL, so that users cannot modify data or access unauthorized tables.

#### Acceptance Criteria

1. THE SQL Generation Module SHALL ONLY allow SELECT statements (verified by checking normalized SQL starts with "select")
2. THE SQL Generation Module SHALL reject SQL containing: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, MERGE (case-insensitive)
3. THE SQL Generation Module SHALL verify table names match allowed schema: fact_assessment, fact_intervention, fact_attendance, dim_region, dim_school, dim_time, observations
4. THE SQL Generation Module SHALL reject SQL attempting to access tables outside BIGQUERY_DATASET_ID
5. THE Query Engine Module SHALL use read-only BigQuery permissions (service account should have bigquery.jobUser and bigquery.dataViewer, not dataEditor)
6. THE Query Engine Module SHALL set maximum_bytes_billed to prevent runaway query costs
7. THE Query Engine Module SHALL enforce LIMIT clause on all queries (append if missing)
8. THE Query Engine Module SHALL log all generated SQL and execution results for audit trail
9. THE System SHALL NOT expose raw error messages from BigQuery to users (sanitize to prevent information leakage)
10. THE System SHALL rate-limit chat requests (optional MVP enhancement)

### Requirement 8: Error Handling and Logging

**User Story:** As a support engineer, I want clear error messages and logs, so that I can debug issues quickly.

#### Acceptance Criteria

1. THE System SHALL define custom exception classes: SqlGenerationError, QueryExecutionError, InvalidRequestError
2. WHEN LLM fails to generate valid SQL, THE System SHALL log: user_query, llm_response_raw, parsing_error
3. WHEN SQL safety check fails, THE System SHALL log: user_query, generated_sql, failed_check_reason
4. WHEN BigQuery query fails, THE System SHALL log: sql, bigquery_error, bytes_scanned
5. THE System SHALL use structured logging with fields: component, operation, status, duration_ms, error_details
6. THE System SHALL return user-friendly error messages in ChatResponse.error field
7. THE System SHALL NOT expose internal implementation details (file paths, stack traces) to users
8. THE System SHALL include correlation_id in all logs for tracing requests across components
9. THE System SHALL log successful queries with metadata: user_query, generated_sql, row_count, bytes_processed, execution_time_ms

### Requirement 9: Testing Coverage

**User Story:** As a software engineer, I want comprehensive tests, so that I can confidently deploy and maintain the NLQ feature.

#### Acceptance Criteria

1. THE Test Suite SHALL include unit tests for schema_context module (system prompt generation, few-shot examples)
2. THE Test Suite SHALL include unit tests for llm_sql module with mocked Ollama responses
3. THE Test Suite SHALL verify SQL safety checks reject forbidden operations: INSERT, UPDATE, DELETE, DROP
4. THE Test Suite SHALL verify SQL safety checks reject unknown table names
5. THE Test Suite SHALL verify LIMIT clause is appended when missing
6. THE Test Suite SHALL include unit tests for bq_query_engine with mocked BigQuery client
7. THE Test Suite SHALL include integration tests for /api/v1/nlq/chat endpoint
8. THE Test Suite SHALL verify chat endpoint returns correct ChatResponse structure
9. THE Test Suite SHALL verify chat endpoint handles LLM errors gracefully
10. THE Test Suite SHALL verify chat endpoint handles BigQuery errors gracefully
11. THE Test Suite SHALL include fixtures for sample user queries and expected SQL outputs
12. THE Test Suite SHALL achieve minimum 80% code coverage for NLQ modules

### Requirement 10: Ollama Integration and Deployment

**User Story:** As a platform engineer, I want Ollama running reliably in the Cloud Run container, so that LLM inference works in production.

#### Acceptance Criteria

1. THE Dockerfile SHALL install Ollama using official installation script
2. THE Dockerfile SHALL pull llama3.2:1b model during image build or container startup
3. THE Container startup script SHALL start Ollama service in background (ollama serve &)
4. THE Container startup script SHALL wait for Ollama to be ready before starting FastAPI
5. THE Container startup script SHALL verify Ollama health with GET /api/tags
6. THE Container SHALL allocate sufficient memory for Ollama + model (minimum 4GB, recommended 8GB)
7. THE Cloud Run configuration SHALL set concurrency to 1-5 (lower due to LLM memory usage)
8. THE Cloud Run configuration SHALL set CPU allocation to "always" (Ollama needs CPU during inference)
9. THE Cloud Run configuration SHALL set request timeout to 300 seconds (LLM inference can be slow on CPU)
10. THE System SHALL log Ollama startup time and model loading status
11. WHEN Ollama fails to start, THE Container SHALL exit with non-zero code and log error details
12. THE System SHALL document cold start time increase (~30-60 seconds for Ollama + model loading)

### Requirement 11: BigQuery Schema Context Accuracy

**User Story:** As a data analyst, I want the LLM to generate accurate SQL using the correct schema, so that queries return meaningful results.

#### Acceptance Criteria

1. THE Schema Context SHALL match the actual BigQuery tables provisioned by Terraform (fact_assessment, fact_intervention, fact_attendance, dim_region, dim_school, dim_time, observations, ingest_runs)
2. THE Schema Context SHALL document partition and clustering keys for query optimization hints
3. THE Schema Context SHALL include example JOIN patterns (e.g., fact_assessment JOIN dim_region ON region_id)
4. THE Schema Context SHALL document common filters (e.g., date ranges, region filters)
5. THE Schema Context SHALL include column data types for type-safe query generation
6. THE Schema Context SHALL provide examples of aggregations (AVG, SUM, COUNT) for analytics queries
7. THE Schema Context SHALL document observations table structure for free-form text queries
8. THE Schema Context SHALL be version-controlled and updated when schema changes
9. THE Schema Context SHALL include comments explaining business meaning of key fields (e.g., test_score = normalized score 0-100)
10. THE Schema Context SHALL prioritize tables most relevant for analytics (fact tables and key dimensions)

### Requirement 12: Demo-Ready Example Queries

**User Story:** As a product manager, I want reliable demo queries, so that I can showcase the NLQ feature during pitches.

#### Acceptance Criteria

1. THE Documentation SHALL provide 3-5 example queries that work reliably
2. THE Example queries SHALL cover key use cases:
   - Regional comparison: "Compare Region A and Region B by average test performance in the first 6 months after joining"
   - Intervention effectiveness: "Which interventions produced the largest improvement in Region A?"
   - Trend analysis: "Show the trend of Region A's math scores over the last year"
   - Observations search: "Find feedback mentioning specific teachers or experiments"
3. THE Example queries SHALL be tested against actual data in staging environment
4. THE Example queries SHALL complete in < 5 seconds with typical dataset sizes
5. THE Example queries SHALL demonstrate key SQL patterns: JOIN, GROUP BY, aggregations, date filtering
6. THE Documentation SHALL include expected output preview for each example query
7. THE Demo script SHALL include troubleshooting steps for common issues (Ollama not responding, empty results)

### Requirement 13: Performance and Scalability

**User Story:** As a system architect, I want the NLQ feature to scale gracefully, so that multiple users can query simultaneously.

#### Acceptance Criteria

1. THE System SHALL complete typical queries (< 1000 rows scanned) in < 10 seconds end-to-end
2. THE System SHALL handle concurrent requests with Cloud Run autoscaling (concurrency=1-5 per instance)
3. THE LLM inference SHALL complete in < 5 seconds for typical queries on Cloud Run CPU
4. THE BigQuery query execution SHALL complete in < 5 seconds for optimized queries
5. THE System SHALL cache Ollama model in memory (no re-download per request)
6. THE System SHALL reuse BigQuery client connections (connection pooling)
7. THE System SHALL log performance metrics: llm_inference_ms, query_execution_ms, total_request_ms
8. WHEN performance degrades, THE System SHALL provide actionable metrics for optimization (e.g., bytes_scanned, query_plan)
9. THE System SHALL document expected cold start time (~30-60s) and warm request time (~5-15s)

### Requirement 14: Privacy and Compliance

**User Story:** As a compliance officer, I want user queries and data handled securely, so that we meet GDPR and data protection requirements.

#### Acceptance Criteria

1. THE System SHALL process all data within GCP region specified by settings (data locality)
2. THE System SHALL use local Ollama instance (no external API calls to OpenAI, Anthropic, etc.)
3. THE System SHALL NOT send user queries or BigQuery results to external services
4. THE System SHALL log only metadata (query structure, row counts), not raw data values
5. THE System SHALL enforce BigQuery IAM permissions (service account should have least-privilege access)
6. THE System SHALL NOT persist chat history (MVP: stateless, no database storage)
7. WHEN chat history persistence is added, THE System SHALL implement data retention policies (e.g., 30-day TTL)
8. THE System SHALL document data flows in architecture diagram (user → FastAPI → Ollama → BigQuery)
9. THE System SHALL sanitize error messages to prevent leaking sensitive information
10. THE System SHALL support disabling NLQ feature via NLQ_ENABLED flag for compliance audits

### Requirement 15: Documentation and Developer Experience

**User Story:** As a developer, I want clear documentation, so that I can understand and extend the NLQ feature.

#### Acceptance Criteria

1. THE Documentation SHALL provide architecture overview with component diagram
2. THE Documentation SHALL explain LLM prompt engineering (system prompt, few-shot examples)
3. THE Documentation SHALL document SQL safety checks and rationale
4. THE Documentation SHALL include setup instructions for local development (running Ollama)
5. THE Documentation SHALL provide API usage examples (curl, Python requests, JavaScript fetch)
6. THE Documentation SHALL explain environment variables and configuration options
7. THE Documentation SHALL document Cloud Run deployment process
8. THE Documentation SHALL include troubleshooting guide for common issues:
   - Ollama connection errors
   - BigQuery permission errors
   - LLM generating invalid SQL
   - Query timeout errors
9. THE Documentation SHALL provide guidelines for extending schema context (adding new tables)
10. THE Documentation SHALL include performance tuning tips (BigQuery optimization, LLM temperature tuning)

## Non-Functional Requirements

### Performance

- **Response Time**: P95 < 15 seconds end-to-end (LLM inference + query execution)
- **Concurrency**: Support 10 concurrent users (Cloud Run autoscaling with concurrency=5)
- **Cold Start**: < 60 seconds (Ollama startup + model loading)
- **Query Limits**: Maximum 100 rows returned per query

### Scalability

- **Horizontal Scaling**: Cloud Run autoscaling up to 10 instances
- **Data Volume**: Support BigQuery datasets up to 1TB (limited by query cost controls)
- **Request Rate**: Handle 100 requests/hour (typical demo usage)

### Availability

- **Uptime**: 99% (Cloud Run SLA)
- **Error Rate**: < 5% (excluding user errors like invalid questions)
- **Graceful Degradation**: Feature toggle to disable NLQ without affecting other services

### Security

- **Authentication**: Use existing Cloud Run authentication (IAM, Cloud IAP)
- **Authorization**: Read-only BigQuery access via service account
- **SQL Injection**: Prevented by parameterized queries and safety checks
- **Data Leakage**: No logging of raw data values

### Maintainability

- **Code Quality**: Follow existing project conventions (FastAPI routers, Pydantic models, structured logging)
- **Testing**: Minimum 80% code coverage
- **Documentation**: Code docstrings and README updates
- **Monitoring**: Log-based metrics in Cloud Logging

## Dependencies

### Internal Dependencies

- **BigQuery Infrastructure**: Requires core and staging datasets from terraform-gcp-infrastructure spec
- **Configuration System**: Extends eduscale.core.config.Settings
- **Logging System**: Uses eduscale.core.logging patterns
- **Storage Backend**: Reads BigQuery using google-cloud-bigquery client

### External Dependencies

- **Ollama**: Local LLM runtime (installed in Dockerfile)
- **Llama 3.2 1B**: Open-source LLM model (pulled via Ollama)
- **BigQuery API**: Google Cloud BigQuery for query execution
- **Python Libraries**: google-cloud-bigquery>=3.11.0, requests>=2.31.0

### Infrastructure Dependencies

- **Cloud Run**: Hosting platform with 4-8GB memory, 2 vCPUs
- **BigQuery**: Data warehouse with read access
- **Application Default Credentials**: IAM authentication for BigQuery

## License Compliance

- **Ollama**: MIT License
- **Llama 3.2**: Open-source (Meta Llama 3 Community License)
- **google-cloud-bigquery**: Apache 2.0
- **requests**: Apache 2.0

All dependencies use permissive licenses compatible with commercial deployment.

## Success Criteria

The NL→SQL Chat Interface MVP is considered successful when:

1. ✅ Users can type natural language questions and receive SQL-generated results
2. ✅ 3-5 demo queries work reliably in staging environment
3. ✅ System enforces read-only SQL with no data modification
4. ✅ Queries complete in < 15 seconds P95
5. ✅ Code coverage >= 80% for NLQ modules
6. ✅ Feature is demo-ready for pitch presentations
7. ✅ Documentation enables junior developer to understand system in < 30 minutes

