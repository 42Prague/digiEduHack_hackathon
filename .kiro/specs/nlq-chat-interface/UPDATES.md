# NLQ Chat Interface Specification - Key Updates for Current Architecture

## Critical Architecture Changes

### 1. LLM Provider: Featherless.ai (NOT Ollama!)

**Current Reality:**
- Uses **Featherless.ai API** via OpenAI Python client
- Model: **Llama 3.1 8B Instruct** (meta-llama/Meta-Llama-3.1-8B-Instruct)
- Authentication: `FEATHERLESS_API_KEY` environment variable
- Endpoint: `https://api.featherless.ai/v1`
- Library: `openai>=1.0.0` (already in requirements.txt)

**Existing Implementation to Reuse:**
- `src/eduscale/tabular/analysis/llm_client.py` - existing LLMClient pattern
- Uses OpenAI Python client with custom base_url
- Already handles authentication, retries, error handling

**Configuration Variables (already exist):**
```python
FEATHERLESS_API_KEY: str = ""
FEATHERLESS_BASE_URL: str = "https://api.featherless.ai/v1"
FEATHERLESS_LLM_MODEL: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"
LLM_ENABLED: bool = True
```

### 2. Actual BigQuery Schema (from terraform/bigquery.tf)

**fact_assessment** (partitioned by date, clustered by region_id):
- date: DATE (REQUIRED, partition key)
- region_id: STRING (REQUIRED, cluster key)
- school_name: STRING
- student_id: STRING
- student_name: STRING
- subject: STRING
- test_score: FLOAT
- file_id: STRING (REQUIRED)
- ingest_timestamp: TIMESTAMP (REQUIRED)

**fact_intervention** (partitioned by date, clustered by region_id):
- date: DATE (REQUIRED, partition key)
- region_id: STRING (REQUIRED, cluster key)
- school_name: STRING
- intervention_type: STRING
- participants_count: INTEGER
- file_id: STRING (REQUIRED)
- ingest_timestamp: TIMESTAMP (REQUIRED)

**observations** (partitioned by ingest_timestamp, clustered by region_id):
- file_id: STRING (REQUIRED)
- region_id: STRING (REQUIRED, cluster key)
- observation_text: STRING
- source_table_type: STRING
- ingest_timestamp: TIMESTAMP (REQUIRED, partition key)

**dim_region**:
- region_id: STRING (REQUIRED)
- region_name: STRING
- from_date: DATE
- to_date: DATE

**dim_school**:
- school_name: STRING (REQUIRED)
- region_id: STRING
- from_date: DATE
- to_date: DATE

**dim_time**:
- date: DATE (REQUIRED)
- year: INTEGER
- month: INTEGER
- day: INTEGER
- quarter: INTEGER
- day_of_week: INTEGER

**ingest_runs** (partitioned by created_at, clustered by region_id, status):
- file_id: STRING (REQUIRED)
- region_id: STRING (REQUIRED)
- status: STRING (REQUIRED)
- step: STRING
- error_message: STRING
- created_at: TIMESTAMP (REQUIRED, partition key)
- updated_at: TIMESTAMP (REQUIRED)

### 3. LLM SQL Generator Implementation (Featherless.ai)

**DO NOT use Ollama HTTP API!** Use OpenAI Python client instead:

```python
from openai import OpenAI
from eduscale.core.config import settings

def generate_sql_from_nl(user_query: str, history: list[dict] | None = None) -> dict:
    """Generate SQL from natural language using Featherless.ai API.
    
    Args:
        user_query: User's question in plain text
        history: Optional conversation history (MVP: unused)
        
    Returns:
        dict with keys: "sql" (validated SQL), "explanation" (user-friendly text)
    """
    # 1. Load system prompt
    system_prompt = get_system_prompt()
    
    # 2. Initialize Featherless.ai client (OpenAI-compatible)
    client = OpenAI(
        base_url=settings.FEATHERLESS_BASE_URL,
        api_key=settings.FEATHERLESS_API_KEY,
    )
    
    # 3. Call LLM API
    try:
        response = client.chat.completions.create(
            model=settings.FEATHERLESS_LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            max_tokens=500,
            temperature=0.1,  # Low temperature for deterministic SQL
        )
        
        response_text = response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Featherless.ai API call failed: {e}")
        raise SqlGenerationError(f"LLM service unavailable: {e}")
    
    # 4. Parse JSON response
    try:
        response_json = json.loads(response_text.strip())
        sql = response_json["sql"]
        explanation = response_json["explanation"]
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Invalid LLM response: {response_text}")
        raise SqlGenerationError(f"LLM returned invalid response: {e}")
    
    # 5. Apply safety checks
    safe_sql = _validate_and_fix_sql(sql, user_query)
    
    return {"sql": safe_sql, "explanation": explanation}
```

### 4. Configuration Updates (Add to existing config.py)

**Only add these new variables:**
```python
# NLQ Feature Configuration (add to Settings class)
NLQ_MAX_RESULTS: int = 100
NLQ_QUERY_TIMEOUT_SECONDS: int = 60
BQ_MAX_BYTES_BILLED: Optional[int] = None  # None = no limit
```

**Reuse existing variables:**
- `FEATHERLESS_API_KEY`
- `FEATHERLESS_BASE_URL`
- `FEATHERLESS_LLM_MODEL`
- `LLM_ENABLED`
- `GCP_PROJECT_ID`
- `BIGQUERY_DATASET_ID` (default: "jedouscale_core")

### 5. Deployment Changes

**NO Dockerfile changes needed!**
- No Ollama installation
- No model downloading
- No special memory requirements
- Standard Cloud Run configuration (concurrency=80, standard memory/CPU)

**Cloud Run Configuration:**
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: eduscale-engine
spec:
  template:
    spec:
      containerConcurrency: 80  # Standard concurrency
      timeoutSeconds: 60  # Normal timeout (not 300)
      containers:
      - image: gcr.io/PROJECT_ID/eduscale-engine:latest
        resources:
          limits:
            memory: 2Gi  # Standard memory (not 8Gi!)
            cpu: '1'     # Standard CPU (not 2)
        env:
        - name: FEATHERLESS_API_KEY
          valueFrom:
            secretKeyRef:
              name: featherless-api-key
              key: api-key
        - name: LLM_ENABLED
          value: 'true'
        - name: NLQ_MAX_RESULTS
          value: '100'
        - name: BQ_MAX_BYTES_BILLED
          value: '1000000000'  # 1GB
```

### 6. Dependencies (NO NEW PACKAGES!)

All required dependencies already in `requirements.txt`:
- ✅ `openai>=1.0.0` (for Featherless.ai API)
- ✅ `google-cloud-bigquery>=3.11.0` (for BigQuery)
- ✅ `fastapi>=0.115.0` (existing)
- ✅ `pydantic>=2.10.0` (existing)

**DO NOT ADD:**
- ❌ Ollama (not needed)
- ❌ requests (use openai library instead)
- ❌ Any other LLM libraries

### 7. Performance Expectations

**With Featherless.ai (serverless):**
- Cold start: ~5-10s (FastAPI only, no model loading)
- Warm request: ~3-8s (API call + BigQuery)
- LLM API latency: ~1-3s (Featherless.ai serverless)
- Concurrency: 80 per instance (standard Cloud Run)

**NOT like Ollama:**
- ~~No 30-60s cold start for model loading~~
- ~~No 5GB+ memory requirement~~
- ~~No concurrency=5 limitation~~

### 8. Testing Considerations

**Mock Featherless.ai API calls using:**
```python
from unittest.mock import Mock, patch

@patch('openai.OpenAI')
def test_generate_sql(mock_openai):
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content='{"sql": "SELECT...", "explanation": "..."}'))
    ]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client
    
    result = generate_sql_from_nl("Show test scores")
    assert "sql" in result
```

**DO NOT mock:**
- ~~Ollama HTTP endpoints~~
- ~~requests.post calls~~

### 9. Key Implementation Differences

| Aspect | Original Spec | Current Reality |
|--------|---------------|-----------------|
| LLM Provider | Ollama (local) | Featherless.ai (API) |
| LLM Model | Llama 3.2 1B | Llama 3.1 8B Instruct |
| API Client | requests library | openai library |
| Deployment | Docker + Ollama install | Standard Cloud Run |
| Memory | 8GB required | 2GB sufficient |
| Concurrency | 5 per instance | 80 per instance |
| Cold Start | 30-60s | 5-10s |
| Dependencies | Add requests | Already have openai |
| Configuration | LLM_MODEL, LLM_ENDPOINT | FEATHERLESS_LLM_MODEL, FEATHERLESS_BASE_URL |

### 10. Implementation Priorities

**Must do:**
1. ✅ Update schema context with actual BigQuery tables from terraform
2. ✅ Use OpenAI client for Featherless.ai API calls
3. ✅ Reuse existing LLMClient pattern where possible
4. ✅ Add only NLQ_MAX_RESULTS, NLQ_QUERY_TIMEOUT_SECONDS, BQ_MAX_BYTES_BILLED to config
5. ✅ Standard Cloud Run deployment (no Dockerfile changes)

**Must NOT do:**
1. ❌ Install Ollama in Docker
2. ❌ Use requests library for LLM calls
3. ❌ Create custom LLM client from scratch (reuse existing)
4. ❌ Increase Cloud Run memory/CPU beyond standard
5. ❌ Change existing FEATHERLESS_* configuration variables

## Summary

The NLQ Chat Interface should:
- Use **Featherless.ai API** (not Ollama)
- Reuse **existing LLMClient pattern**
- Use **actual BigQuery schema** from terraform
- Require **no Docker/deployment changes**
- Add **minimal new configuration** (3 variables)
- Achieve **faster cold starts** (~5-10s vs 30-60s)
- Support **higher concurrency** (80 vs 5 per instance)

This makes implementation **simpler and faster** than the original Ollama-based design!

