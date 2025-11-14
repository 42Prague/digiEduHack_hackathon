# Implementation Plan: NL→SQL Chat Interface

## Overview

This plan breaks the NL→SQL Chat Interface project into incremental, testable tasks. Each task builds on previous work and can be validated independently. The implementation follows a bottom-up approach: core modules first, then API integration, finally UI.

## Estimated Timeline

- **Total Development**: 12-16 hours
- **Testing & Polish**: 4-6 hours
- **Documentation**: 2-3 hours
- **Total**: 18-25 hours (2-3 days for single developer)

## Task List

### Phase 1: Foundation & Configuration (2-3 hours)

- [ ] **Task 1.1**: Extend configuration settings
  - Add NLQ-related settings to `src/eduscale/core/config.py`
  - Add fields: `NLQ_ENABLED`, `LLM_MODEL`, `LLM_ENDPOINT`, `BQ_MAX_BYTES_BILLED`, `NLQ_MAX_RESULTS`, `NLQ_QUERY_TIMEOUT_SECONDS`
  - Set sensible defaults: `LLM_MODEL="llama3.2:1b"`, `LLM_ENDPOINT="http://localhost:11434"`, `NLQ_MAX_RESULTS=100`
  - Add validation for required settings (GCP_PROJECT_ID, BIGQUERY_DATASET_ID)
  - _Requirements: 6.1-6.10_
  - _Validation_: Import settings and verify all NLQ fields are accessible

- [ ] **Task 1.2**: Create NLQ module structure
  - Create directory `src/eduscale/nlq/`
  - Create `__init__.py` with module-level exports
  - Create placeholder files: `schema_context.py`, `llm_sql.py`, `bq_query_engine.py`
  - _Requirements: N/A (project structure)_
  - _Validation_: Import `from eduscale.nlq import schema_context` succeeds

- [ ] **Task 1.3**: Update requirements.txt
  - Verify existing dependencies: `google-cloud-bigquery>=3.11.0`, `requests>=2.31.0`, `pydantic>=2.0.0`
  - No new Python dependencies needed (Ollama is system-level)
  - Document Ollama as system dependency in comments
  - _Requirements: N/A (dependencies)_
  - _Validation_: `pip install -r requirements.txt` succeeds

### Phase 2: Core NLQ Modules (4-5 hours)

- [ ] **Task 2.1**: Implement Schema Context module
  - Create `src/eduscale/nlq/schema_context.py`
  - Define `TableSchema` and `SchemaContext` dataclasses
  - Document all BigQuery tables: fact_assessment, fact_intervention, fact_attendance, dim_region, dim_school, dim_time, observations
  - Include column names, types, and business descriptions for each table
  - Build system prompt template with schema context, safety rules, and output format
  - Include 3-5 few-shot examples: region comparison, intervention effectiveness, score trends, observations search
  - Implement `load_schema_context() -> SchemaContext` function
  - Implement `get_system_prompt() -> str` function
  - Use `settings.BIGQUERY_DATASET_ID` for dataset references
  - _Requirements: 1.1-1.10_
  - _Validation_: 
    - Call `get_system_prompt()` and verify it contains safety rules, table schemas, and examples
    - Verify dataset ID is correctly injected from settings

- [ ] **Task 2.2**: Implement LLM SQL Generation module
  - Create `src/eduscale/nlq/llm_sql.py`
  - Define custom exceptions: `SqlGenerationError`, `SqlSafetyError`
  - Implement `generate_sql_from_nl(user_query: str, history: list | None) -> dict` function:
    - Load system prompt from schema context
    - Compose messages for Ollama (system + user)
    - Call `_call_ollama(messages)` helper
    - Parse JSON response to extract "sql" and "explanation"
    - Handle JSON parsing errors with clear exception messages
    - Call `_validate_and_fix_sql(sql)` for safety checks
    - Return dict with validated SQL and explanation
  - Implement `_call_ollama(messages: list) -> str` helper:
    - POST to `{settings.LLM_ENDPOINT}/api/generate`
    - Use model from `settings.LLM_MODEL`
    - Set temperature=0.1 for deterministic output
    - Set timeout from `settings.NLQ_QUERY_TIMEOUT_SECONDS`
    - Handle timeout and connection errors
  - Implement `_validate_and_fix_sql(sql: str, user_query: str) -> str` helper:
    - Normalize SQL (strip, lowercase for checks)
    - Verify starts with "select" (case-insensitive)
    - Reject forbidden keywords: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, MERGE, GRANT, REVOKE
    - Use regex with word boundaries: `\b{keyword}\b`
    - Verify dataset prefix present (warn if missing)
    - Append "LIMIT {NLQ_MAX_RESULTS}" if no LIMIT clause
    - Reduce LIMIT if > NLQ_MAX_RESULTS
    - Log all checks and modifications
  - Add comprehensive logging with correlation IDs
  - _Requirements: 2.1-2.17_
  - _Validation_:
    - Unit test with mocked Ollama responses
    - Verify safety checks reject INSERT, UPDATE, DELETE
    - Verify LIMIT is appended when missing
    - Test error handling for invalid JSON, missing keys, timeout

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

### Phase 5: Ollama Integration & Deployment (3-4 hours)

- [ ] **Task 5.1**: Update Dockerfile for Ollama
  - Update `docker/Dockerfile` (or create `Dockerfile.nlq` if separate)
  - Add curl installation: `apt-get install -y curl`
  - Install Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
  - Keep existing Python dependencies
  - Create startup script `/start.sh`:
    - Start Ollama in background: `ollama serve &`
    - Wait for Ollama to be ready: loop curl to `/api/tags` with 30 retries
    - Pull model: `ollama pull ${LLM_MODEL:-llama3.2:1b}`
    - Start FastAPI: `uvicorn eduscale.main:app --host 0.0.0.0 --port ${PORT:-8080}`
  - Make startup script executable: `chmod +x /start.sh`
  - Set CMD to `/start.sh`
  - _Requirements: 10.1-10.12_
  - _Validation_:
    - Build Docker image: `docker build -t eduscale-nlq .`
    - Run container: `docker run -e NLQ_ENABLED=true eduscale-nlq`
    - Check logs for "Ollama is ready", "Model pulled", "FastAPI started"
    - Verify container doesn't exit immediately

- [ ] **Task 5.2**: Create Cloud Run configuration
  - Create `infra/nlq-config.yaml` with Cloud Run service definition
  - Set resource limits: memory=8Gi, cpu=2
  - Set concurrency: 5 (lower due to LLM memory usage)
  - Set timeout: 300 seconds (allow for slow LLM inference)
  - Set environment variables: NLQ_ENABLED=true, LLM_MODEL, LLM_ENDPOINT, GCP_PROJECT_ID, BIGQUERY_DATASET_ID, BQ_MAX_BYTES_BILLED
  - Set autoscaling: minScale=0, maxScale=10
  - _Requirements: 10.1-10.12_
  - _Validation_:
    - Deploy to Cloud Run: `gcloud run services replace nlq-config.yaml`
    - Verify service starts successfully
    - Check logs for Ollama startup completion

- [ ] **Task 5.3**: Test Ollama integration locally
  - Create local docker-compose override for NLQ
  - Start Ollama service on host or in separate container
  - Set LLM_ENDPOINT to Ollama URL
  - Run FastAPI app and test `/api/v1/nlq/chat` endpoint
  - Verify LLM generates valid SQL
  - _Requirements: 10.1-10.12_
  - _Validation_:
    - Send test query: `curl -X POST localhost:8080/api/v1/nlq/chat -d '{"messages": [{"role": "user", "content": "Show test scores"}]}'`
    - Verify response contains SQL and explanation
    - Check logs for Ollama API call success

### Phase 6: Testing & Validation (3-4 hours)

- [ ] **Task 6.1**: Write unit tests for Schema Context
  - Create `tests/test_schema_context.py`
  - Test `load_schema_context()` returns valid SchemaContext
  - Test system prompt contains safety rules and table schemas
  - Test few-shot examples are valid SQL
  - Test dataset ID injection from settings
  - _Requirements: 9.1_
  - _Validation_: `pytest tests/test_schema_context.py -v` passes with 100% coverage

- [ ] **Task 6.2**: Write unit tests for LLM SQL Generator
  - Create `tests/test_llm_sql.py`
  - Mock Ollama responses with `requests.post`
  - Test successful SQL generation flow
  - Test JSON parsing errors raise `SqlGenerationError`
  - Test safety checks reject INSERT, UPDATE, DELETE, DROP
  - Test safety checks reject unknown table names (optional)
  - Test LIMIT clause is appended when missing
  - Test LIMIT clause is reduced if > NLQ_MAX_RESULTS
  - Test Ollama timeout handling
  - Test Ollama connection errors
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

- [ ] **Task 6.6**: End-to-end testing with staging data
  - Deploy to staging environment with Ollama running
  - Test 3-5 demo queries against actual BigQuery staging dataset
  - Verify SQL is generated correctly
  - Verify queries complete in < 5 seconds
  - Verify results are correct (manual validation)
  - Document any issues and fix
  - _Requirements: 12.1-12.7_
  - _Validation_: All demo queries work reliably in staging

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

- [ ] **Task 8.3**: Performance testing
  - Measure cold start time (first request after deploy)
  - Measure warm request time (subsequent requests)
  - Test concurrent requests (5-10 simultaneous queries)
  - Verify P95 latency < 15 seconds
  - Document performance metrics
  - _Requirements: 13.1-13.9_
  - _Validation_: Performance meets targets

- [ ] **Task 8.4**: Security audit
  - Verify service account has read-only BigQuery permissions
  - Test SQL injection attempts (should be rejected by safety checks)
  - Verify no sensitive data logged (check Cloud Logging)
  - Test feature toggle (disable NLQ and verify 503 response)
  - Review IAM permissions for Cloud Run service
  - _Requirements: 7.1-7.10_
  - _Validation_: Security checklist complete, no vulnerabilities found

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
Phase 1: Foundation
  1.1 → 1.2 → 1.3

Phase 2: Core Modules
  2.1 (Schema Context) → 2.2 (LLM SQL) → 2.3 (BigQuery Engine)
  Depends on: 1.1, 1.2

Phase 3: API Integration
  3.1 (API Endpoint) depends on 2.2, 2.3
  3.2 (Register Router) depends on 3.1

Phase 4: UI
  4.1 (Chat UI) → 4.2 (UI Route)
  4.2 depends on 3.1

Phase 5: Deployment
  5.1 (Dockerfile) → 5.2 (Cloud Run Config) → 5.3 (Local Test)
  Depends on: All previous phases

Phase 6: Testing
  6.1-6.4 (Unit/Integration Tests) can run in parallel
  6.5 (Fixtures) supports 6.1-6.4
  6.6 (E2E Tests) depends on 5.3

Phase 7: Documentation
  7.1-7.5 can run in parallel
  Depends on: All implementation phases

Phase 8: Deployment & Validation
  8.1 → 8.2 → 8.3 → 8.4 → 8.5 (sequential)
  Depends on: All previous phases
```

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

### Risk: Ollama fails to start in Cloud Run

- **Mitigation**: 
  - Add comprehensive startup logging
  - Implement health check retry logic
  - Test locally with Docker first
  - Document troubleshooting steps

### Risk: LLM generates invalid SQL

- **Mitigation**:
  - Implement multi-layer safety checks
  - Use strict JSON output format
  - Include extensive few-shot examples
  - Log all generated SQL for debugging
  - Test with diverse queries

### Risk: BigQuery queries timeout or cost too much

- **Mitigation**:
  - Enforce LIMIT clause on all queries
  - Set BQ_MAX_BYTES_BILLED limit
  - Set query timeout to 60 seconds
  - Test with realistic dataset sizes

### Risk: Performance too slow for demo

- **Mitigation**:
  - Use lightweight model (Llama 3.2 1B)
  - Set low temperature for faster inference
  - Leverage BigQuery caching
  - Test demo queries in advance

### Risk: Container exceeds memory limits

- **Mitigation**:
  - Allocate 8GB memory for Cloud Run
  - Set concurrency to 5 (not 80)
  - Monitor memory usage in logs
  - Consider smaller model if needed

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

