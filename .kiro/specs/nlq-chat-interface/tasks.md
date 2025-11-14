# Implementation Plan: NL→SQL Chat Interface

## Overview

This plan breaks the NL→SQL Chat Interface project into incremental, testable tasks. Each task builds on previous work and can be validated independently. The implementation follows a bottom-up approach: core modules first, then API integration, finally UI.

**KEY**: This implementation uses **Featherless.ai API** (NOT Ollama) and **reuses existing infrastructure**, making it significantly simpler than originally planned.

## Estimated Timeline

- **Total Development**: 8-12 hours (reduced from 12-16!)
- **Testing & Polish**: 3-4 hours (reduced from 4-6)
- **Documentation**: 1-2 hours (reduced from 2-3)
- **Total**: 12-18 hours (1.5-2 days for single developer)

**Why faster?** No Docker changes, no Ollama setup, reuses existing LLMClient pattern, standard Cloud Run config.

## Task List

### Phase 1: Foundation & Configuration (1-2 hours, REDUCED!)

- [ ] **Task 1.1**: Extend configuration settings (MINIMAL changes!)
  - Open `src/eduscale/core/config.py`
  - **ONLY ADD these 3 variables** to Settings class:
    ```python
    NLQ_MAX_RESULTS: int = 100
    NLQ_QUERY_TIMEOUT_SECONDS: int = 60
    BQ_MAX_BYTES_BILLED: Optional[int] = None
    ```
  - **DO NOT ADD**: `NLQ_ENABLED`, `LLM_MODEL`, `LLM_ENDPOINT` (already exist as `LLM_ENABLED`, `FEATHERLESS_LLM_MODEL`, `FEATHERLESS_BASE_URL`)
  - Verify existing settings are present: `GCP_PROJECT_ID`, `BIGQUERY_DATASET_ID`, `FEATHERLESS_API_KEY`, `LLM_ENABLED`
  - _Requirements: 6.1-6.11_
  - _Validation_: Import settings and verify: `settings.NLQ_MAX_RESULTS`, `settings.FEATHERLESS_API_KEY`, `settings.LLM_ENABLED`

- [ ] **Task 1.2**: Create NLQ module structure
  - Create directory `src/eduscale/nlq/`
  - Create `__init__.py` with module-level exports
  - Create placeholder files: `schema_context.py`, `llm_sql.py`, `bq_query_engine.py`
  - _Requirements: N/A (project structure)_
  - _Validation_: Import `from eduscale.nlq import schema_context` succeeds

- [ ] **Task 1.3**: Verify dependencies (NO NEW PACKAGES!)
  - **Verify existing** dependencies in `requirements.txt`:
    - ✅ `openai>=1.0.0` (for Featherless.ai API client)
    - ✅ `google-cloud-bigquery>=3.11.0` (for BigQuery)
    - ✅ `fastapi>=0.115.0`, `pydantic>=2.10.0` (existing)
  - **DO NOT ADD**: requests, ollama, or any other packages
  - _Requirements: Dependencies section_
  - _Validation_: `pip install -r requirements.txt` succeeds (no changes needed)

### Phase 2: Core NLQ Modules (3-4 hours, REDUCED!)

- [ ] **Task 2.1**: Implement Schema Context module (WITH ACTUAL BigQuery schema!)
  - Create `src/eduscale/nlq/schema_context.py`
  - Define `TableSchema` and `SchemaContext` dataclasses
  - **Document ACTUAL BigQuery tables from terraform/bigquery.tf**:
    - **fact_assessment** (9 columns): date, region_id, school_name, student_id, student_name, subject, test_score (FLOAT!), file_id, ingest_timestamp
    - **fact_intervention** (7 columns): date, region_id, school_name, intervention_type, participants_count (INTEGER!), file_id, ingest_timestamp
    - **observations** (12 columns): file_id, region_id, text_content (STRING, NOT observation_text!), detected_entities (JSON), sentiment_score, original_content_type, audio_duration_ms, audio_confidence, audio_language, page_count, source_table_type, ingest_timestamp
    - **observation_targets** (6 columns): observation_id, target_type, target_id, relevance_score, confidence, ingest_timestamp
    - **dim_region** (4 columns): region_id, region_name, from_date, to_date
    - **dim_school** (4 columns): school_name, region_id, from_date, to_date
    - **dim_time** (6 columns): date, year (INTEGER), month (INTEGER), day (INTEGER), quarter (INTEGER), day_of_week (INTEGER)
    - **ingest_runs** (7 columns): file_id, region_id, status, step, error_message, created_at, updated_at
  - Include partition keys (date/ingest_timestamp) and clustering (region_id) in descriptions
  - Build system prompt template with schema context, safety rules, and JSON output format
  - Include 3-5 few-shot examples with REAL table names and columns
  - Implement `load_schema_context() -> SchemaContext` function
  - Implement `get_system_prompt() -> str` function
  - Use `settings.BIGQUERY_DATASET_ID` (default: "jedouscale_core") for dataset references
  - _Requirements: 1.1-1.10, 11.1-11.10_
  - _Validation_: 
    - Call `get_system_prompt()` and verify it contains actual table names and columns
    - Verify "text_content" (not "observation_text"), "participants_count INTEGER" (not INT64)
    - Verify "test_score FLOAT" (not FLOAT64), "year INTEGER" (not INT64)
    - Verify dataset ID is "jedouscale_core" from settings
    - Verify observations table has 12 columns (including audio_*, page_count, etc.)

- [ ] **Task 2.2**: Implement LLM SQL Generation module (Using Featherless.ai!)
  - Create `src/eduscale/nlq/llm_sql.py`
  - Define custom exceptions: `SqlGenerationError`, `SqlSafetyError`
  - Implement `generate_sql_from_nl(user_query: str, history: list | None) -> dict` function:
    - Load system prompt from schema context
    - **Initialize OpenAI client with Featherless.ai endpoint**:
      ```python
      from openai import OpenAI
      client = OpenAI(
          base_url=settings.FEATHERLESS_BASE_URL,
          api_key=settings.FEATHERLESS_API_KEY,
      )
      ```
    - **Call Featherless.ai API** using `client.chat.completions.create()`:
      - model=`settings.FEATHERLESS_LLM_MODEL` ("meta-llama/Meta-Llama-3.1-8B-Instruct")
      - messages=[system_prompt, user_query]
      - temperature=0.1, max_tokens=500
    - Parse JSON response to extract "sql" and "explanation"
    - Handle JSON parsing errors with clear exception messages
    - Handle API errors (timeout, rate limit, auth failure)
    - Call `_validate_and_fix_sql(sql)` for safety checks
    - Return dict with validated SQL and explanation
  - Implement `_validate_and_fix_sql(sql: str, user_query: str) -> str` helper:
    - Normalize SQL (strip, lowercase for checks)
    - Verify starts with "select" (case-insensitive)
    - Reject forbidden keywords: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, MERGE, GRANT, REVOKE
    - Use regex with word boundaries: `\b{keyword}\b`
    - Verify dataset prefix present ("jedouscale_core")
    - Append "LIMIT {settings.NLQ_MAX_RESULTS}" if no LIMIT clause
    - Reduce LIMIT if > NLQ_MAX_RESULTS
    - Log all checks and modifications
  - Add comprehensive logging with correlation IDs
  - **Alternative**: Consider reusing existing `LLMClient` from `eduscale.tabular.analysis.llm_client` (see design.md)
  - _Requirements: 2.1-2.17, 10.1-10.12_
  - _Validation_:
    - Unit test with mocked OpenAI client (patch `openai.OpenAI`)
    - Verify safety checks reject INSERT, UPDATE, DELETE
    - Verify LIMIT is appended when missing
    - Test error handling for invalid JSON, missing keys, API timeout
    - Test with actual Featherless.ai API key in integration test

- [ ] **Task 2.3**: Implement BigQuery Query Engine
  - Create `src/eduscale/nlq/bq_query_engine.py`
  - Define custom exception: `QueryExecutionError`
  - Implement `run_analytics_query(sql: str) -> list[dict]` function:
    - Initialize BigQuery client: `bigquery.Client(project=settings.GCP_PROJECT_ID)`
    - Create QueryJobConfig with `use_legacy_sql=False`
    - Set `maximum_bytes_billed` if `settings.BQ_MAX_BYTES_BILLED` is configured
    - Execute query and wait for results
    - Convert rows to list of dicts: `[dict(row.items()) for row in result]`
    - Limit to `settings.NLQ_MAX_RESULTS` rows
    - Log query metadata: bytes_processed, bytes_billed, cache_hit, execution_time
    - Handle BigQuery errors with `_sanitize_bigquery_error()`
  - Implement `_sanitize_bigquery_error(error: Exception) -> str` helper:
    - Map common error patterns to user-friendly messages
    - "not found" → "Table or column not found"
    - "permission" → "Permission denied"
    - "timeout" → "Query took too long"
    - "quota" → "Query limit exceeded"
    - "syntax" → "Invalid SQL"
    - Default → "Query execution failed"
  - Optional: Implement `get_bigquery_client()` singleton for connection pooling
  - _Requirements: 3.1-3.12_
  - _Validation_:
    - Unit test with mocked BigQuery client
    - Test successful query execution
    - Test error handling for various BigQuery errors
    - Verify row limit enforcement

### Phase 3: API Integration (3-4 hours)

- [ ] **Task 3.1**: Implement Chat API endpoint
  - Create `src/eduscale/api/v1/routes_nlq.py`
  - Define Pydantic models: `ChatMessage`, `ChatRequest`, `ChatResponse`
  - Create APIRouter with prefix `/api/v1/nlq`
  - Implement `POST /chat` endpoint:
    - Generate correlation ID with `uuid4()`
    - Check `settings.NLQ_ENABLED` feature toggle (return 503 if disabled)
    - Validate request (non-empty messages, at least one user message)
    - Extract latest user message
    - Build conversation history (optional for MVP)
    - Call `generate_sql_from_nl(user_query, history)`
    - Call `run_analytics_query(sql)`
    - Build assistant message with explanation and row count
    - Return ChatResponse with messages, sql, explanation, rows (limited to 20)
    - Handle `SqlGenerationError`: return error in ChatResponse with error field
    - Handle `QueryExecutionError`: return error with attempted SQL for debugging
    - Handle unexpected errors: return HTTP 500 with sanitized message
    - Log all requests with correlation ID, user query, SQL, row count, errors
  - Add comprehensive logging at each step
  - _Requirements: 4.1-4.17_
  - _Validation_:
    - Unit test with mocked `generate_sql_from_nl` and `run_analytics_query`
    - Test successful flow returns correct ChatResponse structure
    - Test error handling for LLM failures
    - Test error handling for BigQuery failures
    - Test feature toggle (503 when disabled)
    - Test invalid requests (400 for missing messages)

- [ ] **Task 3.2**: Register NLQ router in main app
  - Update `src/eduscale/main.py`
  - Import `from eduscale.api.v1.routes_nlq import router as nlq_router`
  - Add `app.include_router(nlq_router)` in `create_app()`
  - Ensure NLQ routes are registered with proper tags
  - _Requirements: N/A (integration)_
  - _Validation_:
    - Start application and verify `/api/v1/nlq/chat` endpoint is accessible
    - Check OpenAPI docs at `/docs` include NLQ endpoints

### Phase 4: User Interface (2-3 hours)

- [ ] **Task 4.1**: Create Chat UI HTML template
  - Create `src/eduscale/ui/templates/chat.html`
  - Implement responsive layout with:
    - Header with title "EduScale Analytics Chat"
    - Scrollable chat history div (500px height)
    - Message bubbles styled differently for user (blue, right-aligned) and assistant (white, left-aligned)
    - Text input and Send button at bottom
  - Add CSS styling:
    - Use system fonts for clean look
    - Responsive design (max-width 1200px, centered)
    - Message bubbles with border-radius
    - Table styling for results
    - Error message styling (red background)
    - SQL code block styling (monospace font, collapsible)
  - Implement JavaScript client:
    - Maintain messages array in client state
    - Handle Send button click and Enter key press
    - POST to `/api/v1/nlq/chat` with messages array
    - Update messages from response
    - Render messages in chat history
    - Render results table (limit to 10 rows, show "... X more rows")
    - Render collapsible SQL block ("Show SQL" toggle)
    - Display error messages in red box
    - Show loading indicator while request is pending
    - Disable Send button during request
    - Auto-scroll to bottom when new messages appear
    - Clear input after sending
  - _Requirements: 5.1-5.16_
  - _Validation_:
    - Open `/nlq/chat` in browser
    - Send test query and verify response renders correctly
    - Verify table displays up to 10 rows
    - Verify SQL toggle works
    - Verify error messages display properly
    - Test on mobile viewport (responsive)

- [ ] **Task 4.2**: Add Chat UI route
  - Update `src/eduscale/api/v1/routes_nlq.py`
  - Add `GET /nlq/chat` route returning HTMLResponse
  - Use Jinja2Templates to render `chat.html`
  - Pass request object to template context
  - _Requirements: 5.1_
  - _Validation_:
    - Navigate to `/nlq/chat` and verify page loads
    - Verify no console errors in browser DevTools

### Phase 5: Deployment (NO DOCKER CHANGES!) (1-2 hours, DRASTICALLY REDUCED!)

- [ ] **Task 5.0**: Create NLQ Service Account in Terraform (NEW!)
  - Copy `.kiro/specs/nlq-chat-interface/terraform/nlq-service-account.tf` to `infra/terraform/`
  - Apply Terraform: `cd infra/terraform && terraform apply`
  - Verify service account created: `gcloud iam service-accounts list | grep nlq-service`
  - Verify IAM roles: `roles/bigquery.dataViewer` and `roles/bigquery.jobUser`
  - Get service account email: `terraform output nlq_service_account_email`
  - **CRITICAL**: This service account has READ-ONLY access (no dataEditor!)
  - _Requirements: 7.1-7.10 (Security)_
  - _Validation_:
    - Service account exists: `nlq-service@PROJECT_ID.iam.gserviceaccount.com`
    - Has exactly 2 roles (dataViewer + jobUser)
    - Can execute SELECT queries
    - **CANNOT** INSERT/UPDATE/DELETE data (test this!)

- [ ] **Task 5.1**: Verify Dockerfile (NO CHANGES NEEDED!)
  - **DO NOT MODIFY Dockerfile** - use existing as-is
  - Verify existing Dockerfile has:
    - ✅ Python 3.11
    - ✅ FastAPI/Uvicorn
    - ✅ All dependencies from requirements.txt (including openai)
  - **DO NOT ADD**:
    - ❌ Ollama installation
    - ❌ Model downloading
    - ❌ Special startup scripts
  - _Requirements: 10.1-10.12_
  - _Validation_:
    - Existing Dockerfile works without modifications
    - `docker build -t eduscale-engine .` succeeds (unchanged)
    - No "Ollama" mentions in Dockerfile

- [ ] **Task 5.2**: Create Cloud Run configuration (STANDARD config, not specialized!)
  - Create or update `infra/nlq-config.yaml` with STANDARD Cloud Run service definition
  - **Set STANDARD resource limits**: memory=2Gi, cpu=1 (NOT 8Gi/2!)
  - **Set STANDARD concurrency**: 80 (NOT 5!)
  - **Set STANDARD timeout**: 60 seconds (NOT 300!)
  - **Set service account**: `serviceAccountName: nlq-service@PROJECT_ID.iam.gserviceaccount.com`
  - Set environment variables:
    - FEATHERLESS_API_KEY (from Secret Manager)
    - NLQ_MAX_RESULTS=100
    - NLQ_QUERY_TIMEOUT_SECONDS=60
    - BQ_MAX_BYTES_BILLED=1000000000 (optional)
  - **DO NOT SET**: LLM_MODEL, LLM_ENDPOINT (use existing FEATHERLESS_*)
  - Set autoscaling: minScale=0, maxScale=10
  - _Requirements: 10.1-10.12_
  - _Validation_:
    - Config file has standard Cloud Run resources
    - Service account is `nlq-service` (read-only!)
    - No "Ollama" mentions in config
    - Featherless.ai API key from Secret Manager

- [ ] **Task 5.3**: Test Featherless.ai integration locally
  - Set environment variables in `.env`:
    - FEATHERLESS_API_KEY=your-key
    - LLM_ENABLED=true
    - NLQ_MAX_RESULTS=100
  - Run FastAPI app locally: `uvicorn eduscale.main:app --reload`
  - Test `/api/v1/nlq/chat` endpoint with real Featherless.ai API
  - Verify LLM generates valid SQL
  - _Requirements: 10.1-10.12_
  - _Validation_:
    - Send test query: `curl -X POST localhost:8080/api/v1/nlq/chat -H "Content-Type: application/json" -d '{"messages": [{"role": "user", "content": "Show test scores"}]}'`
    - Verify response contains SQL and explanation
    - Check logs show "Featherless.ai API call succeeded"
    - Verify no "Ollama" connection errors

### Phase 6: Testing & Validation (3-4 hours)

- [ ] **Task 6.1**: Write unit tests for Schema Context
  - Create `tests/test_schema_context.py`
  - Test `load_schema_context()` returns valid SchemaContext
  - Test system prompt contains safety rules and table schemas
  - Test few-shot examples are valid SQL
  - Test dataset ID injection from settings
  - _Requirements: 9.1_
  - _Validation_: `pytest tests/test_schema_context.py -v` passes with 100% coverage

- [ ] **Task 6.2**: Write unit tests for LLM SQL Generator (Mock Featherless.ai!)
  - Create `tests/test_llm_sql.py`
  - **Mock OpenAI client** with `@patch('openai.OpenAI')`:
    ```python
    @patch('openai.OpenAI')
    def test_generate_sql(mock_openai):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"sql": "SELECT...", "explanation": "..."}'))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        result = generate_sql_from_nl("Show test scores")
        assert "sql" in result
    ```
  - Test successful SQL generation flow
  - Test JSON parsing errors raise `SqlGenerationError`
  - Test safety checks reject INSERT, UPDATE, DELETE, DROP
  - Test safety checks reject unknown table names (optional)
  - Test LIMIT clause is appended when missing
  - Test LIMIT clause is reduced if > NLQ_MAX_RESULTS
  - Test Featherless.ai API timeout handling
  - Test Featherless.ai API connection errors (auth failure, rate limit)
  - **DO NOT mock requests.post** (use openai client mocking!)
  - _Requirements: 9.2-9.5_
  - _Validation_: `pytest tests/test_llm_sql.py -v` passes with >= 80% coverage

- [ ] **Task 6.3**: Write unit tests for BigQuery Engine
  - Create `tests/test_bq_query_engine.py`
  - Mock BigQuery client with `google.cloud.bigquery.Client`
  - Test successful query execution
  - Test row conversion to list of dicts
  - Test row limit enforcement
  - Test BigQuery error handling (not found, permission, timeout, quota)
  - Test error message sanitization
  - _Requirements: 9.6_
  - _Validation_: `pytest tests/test_bq_query_engine.py -v` passes with >= 80% coverage

- [ ] **Task 6.4**: Write integration tests for Chat API
  - Create `tests/test_routes_nlq.py`
  - Use FastAPI TestClient
  - Test successful chat flow (mock LLM and BigQuery)
  - Test ChatResponse structure is correct
  - Test error handling for LLM failures
  - Test error handling for BigQuery failures
  - Test feature toggle (503 when NLQ_ENABLED=false)
  - Test invalid requests (400 for empty messages)
  - Test correlation ID in logs
  - _Requirements: 9.7-9.11_
  - _Validation_: `pytest tests/test_routes_nlq.py -v` passes with >= 80% coverage

- [ ] **Task 6.5**: Create test fixtures
  - Create `tests/fixtures/nlq_test_queries.json` with sample queries and expected SQL
  - Include examples: region comparison, intervention effectiveness, score trends, observations search
  - Include edge cases: queries without LIMIT, queries with forbidden keywords
  - _Requirements: 9.11_
  - _Validation_: Fixtures can be loaded and used in tests

- [ ] **Task 6.6**: End-to-end testing with staging data (Real Featherless.ai + BigQuery)
  - Deploy to staging environment (no Ollama needed!)
  - Configure FEATHERLESS_API_KEY in staging environment
  - Test 3-5 demo queries against actual BigQuery staging dataset:
    1. "Compare regions by average test scores"
    2. "Show interventions in Region A"
    3. "Find observations mentioning teachers"
  - Verify SQL is generated correctly (check against actual schema)
  - Verify queries complete in < 5 seconds (improved from original!)
  - Verify results are correct (manual validation)
  - Document any issues and fix
  - _Requirements: 12.1-12.7_
  - _Validation_: All demo queries work reliably in staging with < 5s latency

### Phase 7: Documentation & Polish (2-3 hours)

- [ ] **Task 7.1**: Create NLQ README
  - Create `docs/NLQ_FEATURE.md` with:
    - Feature overview and architecture diagram
    - Setup instructions (local development with Ollama)
    - Configuration reference (all environment variables)
    - API usage examples (curl, Python, JavaScript)
    - Demo queries (3-5 examples with expected results)
    - Troubleshooting guide (Ollama errors, BigQuery errors, timeout issues)
    - Performance tuning tips
    - Security considerations
  - _Requirements: 15.1-15.10_
  - _Validation_: Junior developer can follow README and understand feature in < 30 minutes

- [ ] **Task 7.2**: Update main README
  - Update `README.md` to mention NLQ feature
  - Add link to `docs/NLQ_FEATURE.md`
  - Add NLQ to feature list
  - _Requirements: 15.1_
  - _Validation_: README accurately reflects project capabilities

- [ ] **Task 7.3**: Add docstrings and code comments
  - Add module-level docstrings to all NLQ modules
  - Add function docstrings with Args, Returns, Raises sections
  - Add inline comments for complex logic (safety checks, SQL parsing)
  - Follow Google Python Style Guide
  - _Requirements: 15.9_
  - _Validation_: `pydoc eduscale.nlq` generates readable documentation

- [ ] **Task 7.4**: Prepare demo script
  - Create `docs/NLQ_DEMO_SCRIPT.md` with:
    - Pre-demo checklist (Ollama running, staging data loaded)
    - 3-5 demo queries with expected outputs
    - Troubleshooting steps for common demo issues
    - Talking points for each query (explain SQL generation, safety, results)
  - _Requirements: 12.1-12.7_
  - _Validation_: Demo script can be followed successfully during pitch

- [ ] **Task 7.5**: Update .env.example
  - Add NLQ configuration section
  - Include all NLQ environment variables with comments
  - Provide example values
  - _Requirements: 6.1-6.10_
  - _Validation_: New developers can copy .env.example and get started

### Phase 8: Deployment & Validation (2-3 hours)

- [ ] **Task 8.1**: Deploy to staging
  - Build Docker image with Ollama: `docker build -t gcr.io/PROJECT_ID/eduscale-nlq:staging .`
  - Push to Google Container Registry: `docker push gcr.io/PROJECT_ID/eduscale-nlq:staging`
  - Deploy to Cloud Run staging: `gcloud run services replace infra/nlq-config-staging.yaml`
  - Configure environment variables via Cloud Run UI or gcloud
  - Verify service starts and Ollama initializes successfully
  - _Requirements: 10.1-10.12_
  - _Validation_: Cloud Run service shows "READY" status, logs show "Ollama is ready"

- [ ] **Task 8.2**: Run staging smoke tests
  - Test health endpoint: `curl https://staging-url/health`
  - Test chat UI: navigate to `https://staging-url/nlq/chat`
  - Test API endpoint with curl: `curl -X POST https://staging-url/api/v1/nlq/chat -d '...'`
  - Run all 3-5 demo queries
  - Verify results are correct
  - Check logs for errors or warnings
  - _Requirements: 12.1-12.7_
  - _Validation_: All smoke tests pass

- [ ] **Task 8.3**: Performance testing (Expect BETTER performance!)
  - Measure cold start time (first request after deploy) - **expect ~5-10s, not 30-60s!**
  - Measure warm request time (subsequent requests) - **expect ~3-8s, not 5-15s!**
  - Test concurrent requests (20-50 simultaneous queries) - **more than original 5-10!**
  - Verify P95 latency < 10 seconds (improved from 15s!)
  - Document performance metrics:
    - Cold start time
    - Featherless.ai API latency
    - BigQuery query execution time
    - Total request time
  - _Requirements: 13.1-13.9_
  - _Validation_: Performance meets improved targets (< 10s P95)

- [ ] **Task 8.4**: Security audit (Plus Featherless.ai API security)
  - Verify service account has read-only BigQuery permissions
  - Test SQL injection attempts (should be rejected by safety checks)
  - Verify no sensitive data logged (check Cloud Logging)
  - Test feature toggle (disable LLM_ENABLED and verify 503 response)
  - Review IAM permissions for Cloud Run service
  - **Verify Featherless.ai API key stored in Secret Manager** (not plain text env var)
  - **Review what data is sent to Featherless.ai**: user questions only, NOT BigQuery results
  - Document privacy implications of external API usage
  - _Requirements: 7.1-7.10, 14.1-14.12_
  - _Validation_: Security checklist complete, API key secured, privacy documented

- [ ] **Task 8.5**: Deploy to production
  - Build production Docker image: `docker build -t gcr.io/PROJECT_ID/eduscale-nlq:prod .`
  - Push to GCR: `docker push gcr.io/PROJECT_ID/eduscale-nlq:prod`
  - Deploy to Cloud Run production: `gcloud run services replace infra/nlq-config-prod.yaml`
  - Configure environment variables for production
  - Smoke test in production
  - Monitor logs and metrics
  - _Requirements: N/A (deployment)_
  - _Validation_: Production service is healthy, demo queries work

## Task Dependencies

```
Phase 1: Foundation (SIMPLIFIED!)
  1.1 (Add 3 config vars) → 1.2 (Create module structure)
  1.3 (Verify deps) - parallel to 1.1, 1.2

Phase 2: Core Modules (FASTER with Featherless.ai!)
  2.1 (Schema Context with REAL BigQuery schema) → 2.2 (LLM SQL with Featherless.ai) → 2.3 (BigQuery Engine)
  Depends on: 1.1, 1.2
  Note: 2.2 can reuse existing LLMClient pattern

Phase 3: API Integration
  3.1 (API Endpoint) depends on 2.2, 2.3
  3.2 (Register Router) depends on 3.1

Phase 4: UI
  4.1 (Chat UI) → 4.2 (UI Route)
  4.2 depends on 3.1

Phase 5: Deployment (NO DOCKER WORK!)
  5.1 (Verify Dockerfile - NO CHANGES) - quick check
  5.2 (Standard Cloud Run Config) - simple yaml
  5.3 (Test Featherless.ai locally) - faster than Ollama setup
  Depends on: All previous phases

Phase 6: Testing (Mock OpenAI client, not Ollama HTTP)
  6.1-6.4 (Unit/Integration Tests) can run in parallel
  6.5 (Fixtures) supports 6.1-6.4
  6.6 (E2E Tests with real Featherless.ai) depends on 5.3

Phase 7: Documentation (LESS to document!)
  7.1-7.5 can run in parallel
  Note: No Ollama setup docs needed
  Depends on: All implementation phases

Phase 8: Deployment & Validation (FASTER cold starts!)
  8.1 → 8.2 → 8.3 (expect better performance!) → 8.4 (+ API security) → 8.5
  Depends on: All previous phases
```

**Key Simplifications:**
- ✅ No Dockerfile changes (Phase 5 reduced from 3-4h to 1-2h)
- ✅ No Ollama setup/testing (saves ~2h)
- ✅ Standard Cloud Run config (saves ~1h)
- ✅ Can reuse existing LLMClient (saves ~1h in Phase 2)
- ✅ Faster testing (mock OpenAI client simpler than mock Ollama HTTP)

## Testing Strategy

### Unit Tests (Target: 80%+ coverage)

- `tests/test_schema_context.py`: Test schema loading and prompt generation
- `tests/test_llm_sql.py`: Test SQL generation and safety checks (with mocked Ollama)
- `tests/test_bq_query_engine.py`: Test query execution (with mocked BigQuery)
- `tests/test_routes_nlq.py`: Test API endpoints (with mocked LLM and BigQuery)

### Integration Tests

- Test full flow: user message → LLM → BigQuery → response
- Test error handling at each integration point
- Test feature toggle and configuration

### End-to-End Tests

- Test with actual Ollama instance (local or staging)
- Test with BigQuery staging dataset
- Validate demo queries produce correct results

### Manual Testing

- UI testing in browser (Chrome, Firefox, Safari)
- Mobile responsiveness testing
- Accessibility testing (keyboard navigation, screen readers)
- Performance testing (cold start, warm requests, concurrent users)

## Rollout Plan

### Stage 1: Local Development (Days 1-2)

- Complete Phases 1-4 (Foundation, Core, API, UI)
- Test locally with Ollama running on host
- Validate against BigQuery staging dataset

### Stage 2: Staging Deployment (Day 3)

- Complete Phase 5 (Ollama integration in Docker)
- Deploy to Cloud Run staging
- Run smoke tests and E2E tests
- Fix any issues

### Stage 3: Testing & Polish (Day 3)

- Complete Phase 6 (comprehensive testing)
- Complete Phase 7 (documentation)
- Prepare demo script

### Stage 4: Production Deployment (Day 3)

- Complete Phase 8 (production deployment)
- Monitor logs and performance
- Ready for demo/pitch

## Risk Mitigation

### Risk: Featherless.ai API unavailable or rate-limited

- **Mitigation**: 
  - Implement retry logic with exponential backoff
  - Handle API errors gracefully (return user-friendly message)
  - Monitor API latency and error rates
  - Have backup plan (document fallback to disable feature)
  - Test API limits during load testing

### Risk: LLM generates invalid SQL

- **Mitigation**:
  - Implement multi-layer safety checks
  - Use strict JSON output format
  - Include extensive few-shot examples with REAL table names
  - Log all generated SQL for debugging
  - Test with diverse queries
  - Use actual BigQuery schema in system prompt

### Risk: BigQuery queries timeout or cost too much

- **Mitigation**:
  - Enforce LIMIT clause on all queries
  - Set BQ_MAX_BYTES_BILLED=1GB limit
  - Set query timeout to 60 seconds
  - Test with realistic dataset sizes
  - Document query optimization patterns

### Risk: Featherless.ai API key leaked

- **Mitigation**:
  - Store API key in Secret Manager (not env var)
  - Never log API key values
  - Use Cloud Run service account for access
  - Rotate keys regularly
  - Monitor API usage for anomalies

### Risk: Privacy concerns with external API

- **Mitigation**:
  - Document what data is sent (user questions only, NOT BigQuery results)
  - Include privacy notice in UI
  - Provide toggle to disable feature (LLM_ENABLED=false)
  - Review Featherless.ai privacy policy
  - Consider on-prem LLM for sensitive deployments (future)

## Success Criteria

The implementation is complete when:

- ✅ All tasks in Phases 1-7 are complete
- ✅ Unit tests achieve >= 80% code coverage
- ✅ Integration tests pass
- ✅ E2E tests with staging data pass
- ✅ 3-5 demo queries work reliably (< 5s execution)
- ✅ Deployed to staging and production
- ✅ Documentation enables junior developer onboarding in < 30 min
- ✅ Feature is demo-ready for hackathon pitch
- ✅ No critical security vulnerabilities
- ✅ Performance meets targets (P95 < 15s end-to-end)

## Post-MVP Enhancements (Future Work)

- [ ] Conversation history persistence (store sessions in Firestore)
- [ ] Query result caching (Redis for common queries)
- [ ] Auto-visualization (generate charts from query results)
- [ ] Query suggestions (suggest questions based on schema)
- [ ] Multi-language support (Czech/English prompts)
- [ ] Fine-tune Llama on EduScale-specific queries
- [ ] GPU acceleration for faster inference
- [ ] Export results to CSV/Excel
- [ ] Collaborative features (share queries with team)
- [ ] Advanced analytics (query optimization recommendations)

