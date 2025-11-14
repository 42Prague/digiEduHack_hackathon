# Natural Language Query (NLQ) Feature

## Overview

The Natural Language Query (NLQ) feature enables users to query BigQuery analytics data using plain English questions. The system translates user questions into safe, read-only SQL queries using **Llama 3.1 8B Instruct** via **Featherless.ai API**, executes them against BigQuery, and returns results in a conversational chat interface.

### Key Features

- **Natural Language to SQL**: Translate plain English questions to BigQuery SQL
- **Safety-First**: Multi-layer validation ensures read-only, safe queries
- **Serverless LLM**: Uses Featherless.ai API (no local model management required)
- **BigQuery Integration**: Direct execution against EduScale data warehouse
- **Interactive UI**: Beautiful chat interface with result tables and SQL transparency
- **Standard Cloud Run**: Runs on standard Cloud Run configuration (2GB RAM, 1 vCPU)

## Architecture

```
┌─────────────────────────────────────────────────┐
│            User Browser                         │
│  ┌──────────────────────────────────────────┐  │
│  │  Chat UI (chat.html)                     │  │
│  │  - Message input/display                 │  │
│  │  - Result tables                         │  │
│  │  - SQL transparency (show/hide)          │  │
│  └──────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────┘
                 │ POST /api/v1/nlq/chat
                 ▼
┌─────────────────────────────────────────────────┐
│     FastAPI Application (Cloud Run)             │
│  ┌──────────────────────────────────────────┐  │
│  │  Chat API Endpoint                       │  │
│  │  (routes_nlq.py)                         │  │
│  └──────────┬──────────────┬────────────────┘  │
│             │              │                    │
│             ▼              ▼                    │
│  ┌──────────────┐  ┌──────────────┐           │
│  │ LLM SQL Gen  │  │ BigQuery     │           │
│  │ (llm_sql.py) │  │ Engine       │           │
│  │              │  │ (bq_query    │           │
│  │ • Schema ctx │  │  _engine.py) │           │
│  │ • Validation │  │              │           │
│  └──────┬───────┘  └──────┬───────┘           │
└─────────┼──────────────────┼───────────────────┘
          │                  │
          ▼                  ▼
┌──────────────────┐  ┌──────────────────┐
│ Featherless.ai   │  │ Google BigQuery  │
│ API              │  │ (EU)             │
│ (Llama 3.1 8B)   │  │                  │
└──────────────────┘  └──────────────────┘
```

### Components

1. **Schema Context** (`nlq/schema_context.py`)
   - Defines BigQuery table schemas
   - Generates system prompts for LLM
   - Includes few-shot examples

2. **LLM SQL Generator** (`nlq/llm_sql.py`)
   - Calls Featherless.ai API
   - Validates and fixes generated SQL
   - Enforces safety rules (read-only, LIMIT clause)

3. **BigQuery Engine** (`nlq/bq_query_engine.py`)
   - Executes validated SQL queries
   - Converts results to JSON format
   - Handles errors gracefully

4. **Chat API** (`api/v1/routes_nlq.py`)
   - REST endpoint for chat messages
   - Orchestrates LLM and BigQuery calls
   - Returns structured responses

5. **Chat UI** (`ui/templates/chat.html`)
   - Interactive chat interface
   - Result table display
   - Collapsible SQL view

## Setup & Configuration

### Environment Variables

Add these to your `.env` file or Cloud Run configuration:

```bash
# NLQ Configuration
NLQ_MAX_RESULTS=100                      # Maximum rows returned
NLQ_QUERY_TIMEOUT_SECONDS=60             # Query timeout
BQ_MAX_BYTES_BILLED=1000000000           # Optional: 1GB limit

# LLM Configuration (Featherless.ai)
LLM_ENABLED=true
FEATHERLESS_API_KEY=your-api-key-here
FEATHERLESS_BASE_URL=https://api.featherless.ai/v1
FEATHERLESS_LLM_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct

# BigQuery Configuration
GCP_PROJECT_ID=your-project-id
BIGQUERY_DATASET_ID=jedouscale_core
```

### Getting Featherless.ai API Key

1. Visit [featherless.ai](https://featherless.ai)
2. Sign up for an account
3. Navigate to API settings
4. Generate an API key
5. Store it in Secret Manager (recommended) or environment variable

### Secret Manager Setup (Production)

```bash
# Create secret
echo -n "your-api-key" | gcloud secrets create featherless-api-key \
    --data-file=- \
    --replication-policy="automatic"

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding featherless-api-key \
    --member="serviceAccount:YOUR-SERVICE-ACCOUNT@PROJECT-ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## Local Development

### Prerequisites

- Python 3.11+
- Google Cloud SDK (for BigQuery access)
- Featherless.ai API key

### Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your credentials
   ```

3. **Authenticate with Google Cloud**:
   ```bash
   gcloud auth application-default login
   gcloud config set project YOUR-PROJECT-ID
   ```

4. **Run the application**:
   ```bash
   uvicorn eduscale.main:app --reload --host 0.0.0.0 --port 8080
   ```

5. **Access the chat UI**:
   - Open browser: http://localhost:8080/nlq/chat
   - Or use API directly: http://localhost:8080/docs

### Testing Locally

```bash
# Run all tests
pytest

# Run NLQ tests only
pytest tests/test_schema_context.py tests/test_llm_sql.py tests/test_bq_query_engine.py tests/test_routes_nlq.py

# Run with coverage
pytest --cov=eduscale.nlq --cov-report=html
```

## API Usage

### Chat Endpoint

**POST** `/api/v1/nlq/chat`

#### Request Body

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Show me average test scores by region"
    }
  ]
}
```

#### Response Body

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Show me average test scores by region"
    },
    {
      "role": "assistant",
      "content": "This query calculates the average test score for each region. Found 3 result(s)."
    }
  ],
  "sql": "SELECT region_id, AVG(test_score) as avg_score FROM `jedouscale_core.fact_assessment` GROUP BY region_id ORDER BY avg_score DESC LIMIT 100",
  "explanation": "This query calculates the average test score for each region from the fact_assessment table, ordered by highest average score first.",
  "rows": [
    {"region_id": "A", "avg_score": 85.5},
    {"region_id": "B", "avg_score": 82.3},
    {"region_id": "C", "avg_score": 79.8}
  ],
  "total_rows": 3,
  "error": null
}
```

### Example Queries

#### Using curl

```bash
curl -X POST http://localhost:8080/api/v1/nlq/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Show me recent interventions"}
    ]
  }'
```

#### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8080/api/v1/nlq/chat",
    json={
        "messages": [
            {"role": "user", "content": "What are the top performing schools?"}
        ]
    }
)

data = response.json()
print(f"SQL: {data['sql']}")
print(f"Results: {data['total_rows']} rows")
for row in data['rows']:
    print(row)
```

#### Using JavaScript

```javascript
const response = await fetch('/api/v1/nlq/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    messages: [
      {role: 'user', content: 'Find feedback mentioning teachers'}
    ]
  })
});

const data = await response.json();
console.log('SQL:', data.sql);
console.log('Results:', data.rows);
```

## Demo Queries

Here are 5 demo queries ready for presentations:

### 1. Regional Performance Overview

**Query**: "Show me average test scores by region"

**Generated SQL**:
```sql
SELECT region_id, AVG(test_score) as avg_score 
FROM `jedouscale_core.fact_assessment` 
GROUP BY region_id 
ORDER BY avg_score DESC 
LIMIT 100
```

**Talking Points**:
- Natural language to SQL translation
- Automatic aggregation and grouping
- Read-only safety validation

### 2. Recent Activity

**Query**: "List interventions in the last 30 days"

**Generated SQL**:
```sql
SELECT date, region_id, school_name, intervention_type, participants_count 
FROM `jedouscale_core.fact_intervention` 
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) 
ORDER BY date DESC 
LIMIT 100
```

**Talking Points**:
- Date filtering with relative dates
- BigQuery Standard SQL functions

### 3. Unstructured Data Search

**Query**: "Find feedback mentioning teachers"

**Generated SQL**:
```sql
SELECT o.file_id, o.text_content, o.sentiment_score, ot.target_type 
FROM `jedouscale_core.observations` o 
JOIN `jedouscale_core.observation_targets` ot ON o.file_id = ot.observation_id 
WHERE ot.target_type = 'teacher' 
LIMIT 100
```

**Talking Points**:
- Join across multiple tables
- Searching observations table
- Entity target filtering

### 4. Ranking and Ordering

**Query**: "What are the top performing schools?"

**Generated SQL**:
```sql
SELECT school_name, AVG(test_score) as avg_score, COUNT(*) as assessment_count 
FROM `jedouscale_core.fact_assessment` 
GROUP BY school_name 
HAVING assessment_count > 10 
ORDER BY avg_score DESC 
LIMIT 100
```

**Talking Points**:
- Ranking with ORDER BY DESC
- HAVING clause for filtering
- Statistical significance (>10 assessments)

### 5. Time Series Analysis

**Query**: "Show intervention participation trends by month"

**Generated SQL**:
```sql
SELECT t.year, t.month, SUM(i.participants_count) as total_participants 
FROM `jedouscale_core.fact_intervention` i 
JOIN `jedouscale_core.dim_time` t ON i.date = t.date 
GROUP BY t.year, t.month 
ORDER BY t.year, t.month 
LIMIT 100
```

**Talking Points**:
- Dimension table join (dim_time)
- Time-based aggregation
- Trend analysis support

## Available BigQuery Tables

### Dimension Tables

1. **dim_region**
   - `region_id` (STRING): Region identifier
   - `region_name` (STRING): Region name
   - `from_date`, `to_date` (DATE): Validity period

2. **dim_school**
   - `school_name` (STRING): School name
   - `region_id` (STRING): Foreign key to dim_region
   - `from_date`, `to_date` (DATE): Validity period

3. **dim_time**
   - `date` (DATE): Calendar date
   - `year`, `month`, `day`, `quarter`, `day_of_week` (INTEGER): Date components

### Fact Tables

4. **fact_assessment**
   - `date` (DATE): Assessment date
   - `region_id` (STRING): Foreign key to dim_region
   - `school_name` (STRING): School name
   - `student_id`, `student_name` (STRING): Student info
   - `subject` (STRING): Subject/course
   - `test_score` (FLOAT): Numeric score
   - `file_id` (STRING): Source file
   - `ingest_timestamp` (TIMESTAMP): Ingestion time
   - **Partitioned by**: `date`
   - **Clustered by**: `region_id`

5. **fact_intervention**
   - `date` (DATE): Intervention date
   - `region_id` (STRING): Foreign key to dim_region
   - `school_name` (STRING): School name
   - `intervention_type` (STRING): Type of intervention
   - `participants_count` (INTEGER): Number of participants
   - `file_id` (STRING): Source file
   - `ingest_timestamp` (TIMESTAMP): Ingestion time
   - **Partitioned by**: `date`
   - **Clustered by**: `region_id`

### Observation Tables

6. **observations**
   - `file_id` (STRING): Observation identifier
   - `region_id` (STRING): Foreign key to dim_region
   - `text_content` (STRING): Full text content
   - `detected_entities` (JSON): Detected entities
   - `sentiment_score` (FLOAT64): Sentiment (-1 to 1)
   - `original_content_type` (STRING): File type
   - `audio_duration_ms`, `audio_confidence`, `audio_language`: Audio metadata
   - `page_count` (INT64): Document pages
   - `ingest_timestamp` (TIMESTAMP): Ingestion time
   - **Partitioned by**: `ingest_timestamp`
   - **Clustered by**: `region_id`

7. **observation_targets**
   - `observation_id` (STRING): Foreign key to observations
   - `target_type` (STRING): Entity type (teacher, student, subject)
   - `target_id` (STRING): Entity ID
   - `relevance_score` (FLOAT64): Relevance (0-1)
   - `confidence` (STRING): Confidence level
   - `ingest_timestamp` (TIMESTAMP): Ingestion time
   - **Partitioned by**: `ingest_timestamp`
   - **Clustered by**: `observation_id`, `target_type`

## Safety & Security

### SQL Safety Checks

The system implements multiple layers of SQL validation:

1. **Statement Type Check**: Only SELECT queries allowed
2. **Forbidden Keywords**: Rejects INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, MERGE, GRANT, REVOKE
3. **LIMIT Enforcement**: Automatically adds or reduces LIMIT clause (max: 100 rows)
4. **Dataset Validation**: Verifies queries target correct dataset

### BigQuery Permissions

The Cloud Run service account should have:
- `roles/bigquery.dataViewer` - Read access to datasets
- `roles/bigquery.jobUser` - Execute queries

**DO NOT GRANT**:
- `bigquery.dataEditor` or higher (write permissions)
- `bigquery.admin` (admin permissions)

### Privacy & Compliance

- **Data Sent to Featherless.ai**: Only user questions (NOT query results)
- **Data Storage**: Query logs stored in Cloud Logging (retention: 30 days)
- **GDPR Compliance**: BigQuery in EU region, no PII sent to external APIs

## Deployment

### Build Docker Image

```bash
# Set project ID
export GCP_PROJECT_ID=your-project-id

# Build image
docker build -f docker/Dockerfile -t gcr.io/$GCP_PROJECT_ID/eduscale-engine:latest .

# Push to GCR
docker push gcr.io/$GCP_PROJECT_ID/eduscale-engine:latest
```

### Deploy to Cloud Run

```bash
# Update nlq-config.yaml with your PROJECT_ID

# Deploy using config file
gcloud run services replace infra/nlq-config.yaml --region=europe-west1

# Or deploy using gcloud command
gcloud run deploy eduscale-engine \
  --image=gcr.io/$GCP_PROJECT_ID/eduscale-engine:latest \
  --region=europe-west1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=1 \
  --concurrency=80 \
  --timeout=60 \
  --set-env-vars="LLM_ENABLED=true,NLQ_MAX_RESULTS=100" \
  --set-secrets="FEATHERLESS_API_KEY=featherless-api-key:latest"
```

### Verify Deployment

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe eduscale-engine --region=europe-west1 --format='value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Test NLQ endpoint
curl -X POST $SERVICE_URL/api/v1/nlq/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Show me test scores"}]}'
```

## Troubleshooting

### Common Issues

#### 1. "LLM API key not configured"

**Solution**: Ensure `FEATHERLESS_API_KEY` is set in environment or Secret Manager.

```bash
# Check if secret exists
gcloud secrets describe featherless-api-key

# Verify service account has access
gcloud secrets get-iam-policy featherless-api-key
```

#### 2. "Table not found" errors

**Solution**: Verify BigQuery dataset and tables exist, and service account has access.

```bash
# List datasets
bq ls

# List tables in dataset
bq ls jedouscale_core

# Check IAM permissions
gcloud projects get-iam-policy $GCP_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*cloudrun*"
```

#### 3. "Query execution timeout"

**Solution**: Increase `NLQ_QUERY_TIMEOUT_SECONDS` or optimize queries.

```bash
# Update timeout
gcloud run services update eduscale-engine \
  --region=europe-west1 \
  --set-env-vars="NLQ_QUERY_TIMEOUT_SECONDS=120"
```

#### 4. Featherless.ai API rate limits

**Solution**: Implement retry logic or upgrade Featherless.ai plan.

Check logs for rate limit errors:
```bash
gcloud logging read "resource.type=cloud_run_revision AND textPayload=~\"rate limit\"" \
  --limit=50 \
  --format=json
```

## Performance

### Expected Latency

- **Cold start**: 5-10 seconds (first request after deploy)
- **Warm requests**: 3-8 seconds (subsequent requests)
  - LLM API call: 1-3 seconds
  - BigQuery execution: 1-4 seconds
  - Response formatting: <1 second

### Optimization Tips

1. **Use date filters**: Leverage partitioning fields (date, ingest_timestamp)
2. **Filter by region**: Use clustering field (region_id) in WHERE clause
3. **Limit aggregations**: Keep GROUP BY columns minimal
4. **Cache-friendly queries**: Identical queries benefit from BigQuery caching

## Monitoring

### Key Metrics

Monitor these in Cloud Run metrics:

- **Request count**: Total NLQ API calls
- **Request latency (P95)**: Should be <10 seconds
- **Error rate**: Should be <1%
- **CPU utilization**: Should be <70%
- **Memory utilization**: Should be <80%

### Logging

Check logs in Cloud Logging:

```bash
# View recent NLQ requests
gcloud logging read "resource.type=cloud_run_revision AND textPayload=~\"Chat request received\"" \
  --limit=20 \
  --format=json

# View errors
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit=50 \
  --format=json
```

### Alerts

Recommended alerts:

1. **High error rate**: >5% errors in 5 minutes
2. **High latency**: P95 latency >15 seconds
3. **API quota exceeded**: Featherless.ai rate limits hit

## Future Enhancements

- [ ] Conversation history persistence (Firestore)
- [ ] Query result caching (Redis)
- [ ] Auto-visualization (charts from query results)
- [ ] Query suggestions based on schema
- [ ] Multi-language support (Czech prompts)
- [ ] Export results to CSV/Excel
- [ ] Collaborative features (share queries)
- [ ] Advanced analytics (query optimization recommendations)

## Support

For issues or questions:
- Check logs in Cloud Logging
- Review troubleshooting section above
- Contact: eduscale-support@example.com

## License

[Add your license here]

