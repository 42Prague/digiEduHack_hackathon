# Tabular Service

## Overview

The Tabular Service is a microservice within the EduScale event-driven data processing architecture that transforms extracted text into normalized, validated data in BigQuery. The service uses AI-powered classification and mapping to automatically understand table types and column semantics, ensuring data quality across diverse educational data sources.

## Architecture

### Event-Driven Flow

```
User Upload → Backend → Cloud Storage
    ↓
Eventarc Trigger (uploads/*)
    ↓
MIME Decoder → Transformer
    ↓
Transformer saves text → gs://bucket/text/file_id.txt
    ↓
Eventarc Trigger (text/*.txt) ⭐
    ↓
Tabular Service (this component)
    ↓
BigQuery → Status to Backend → UI
```

### Processing Paths

The service automatically routes content to appropriate processing:

**TABULAR PATH** (CSV, Excel, JSON arrays):
1. Load DataFrame
2. AI Table Classification (ATTENDANCE, ASSESSMENT, FEEDBACK, INTERVENTION, RELATIONSHIP)
3. AI Column Mapping to canonical concepts
4. Entity Resolution (normalize names/IDs)
5. Data Normalization
6. Pandera Validation
7. Clean Layer Write (Parquet)
8. BigQuery Load (Staging → MERGE → Core)

**FREE_FORM PATH** (PDF, Audio transcripts, plain text):
1. Entity Extraction using LLM
2. Entity Resolution
3. Sentiment Analysis
4. Store in observations table
5. Create observation_targets junction records

## AI Models

### BGE-M3 Embeddings
- **Model**: BAAI/bge-m3
- **Size**: ~2.2GB
- **Dimensions**: 1024
- **Purpose**: Semantic understanding of table types and column meanings
- **Languages**: 100+ including Czech and English

### Llama 3.2 1B (via Ollama)
- **Model**: llama3.2:1b
- **Size**: ~1.3GB
- **Purpose**: Entity extraction and sentiment analysis
- **Temperature**: 0.1 (deterministic outputs)

**Total Model Size**: ~3.5GB  
**Cold Start Time**: 20-30 seconds

## Configuration

### Environment Variables

```bash
# GCP Configuration
GCP_PROJECT_ID=your-project-id
GCP_REGION=europe-west1
STORAGE_BACKEND=gcs
GCS_BUCKET_NAME=your-bucket-name

# BigQuery Configuration
BIGQUERY_PROJECT_ID=your-project-id
BIGQUERY_DATASET_ID=jedouscale_core
BIGQUERY_STAGING_DATASET_ID=jedouscale_staging
CLEAN_LAYER_BASE_PATH=gs://your-bucket/clean
CONCEPT_CATALOG_PATH=/app/config/concepts.yaml

# AI Models
EMBEDDING_MODEL_NAME=BAAI/bge-m3
LLM_MODEL_NAME=llama3.2:1b
LLM_ENDPOINT=http://localhost:11434
LLM_ENABLED=true

# Ingestion Settings
INGEST_MAX_ROWS=200000
PSEUDONYMIZE_IDS=false

# AI Analysis Settings
FEEDBACK_ANALYSIS_ENABLED=true
ENTITY_RESOLUTION_THRESHOLD=0.85
FEEDBACK_TARGET_THRESHOLD=0.65
MAX_TARGETS_PER_FEEDBACK=10
ENTITY_CACHE_TTL_SECONDS=3600
```

## API Endpoints

### 1. CloudEvents Handler (Primary)

**POST /**

Receives CloudEvents from Eventarc when ANY file is created in GCS uploads bucket.
The service filters for `text/*.txt` files in the code.

**CloudEvent Payload**:
```json
{
  "id": "event-123",
  "type": "google.cloud.storage.object.v1.finalized",
  "data": {
    "bucket": "your-bucket",
    "name": "text/file-id.txt"
  }
}
```

**Response (for text files)**:
```json
{
  "status": "success",
  "file_id": "file-id",
  "table_type": "ASSESSMENT",
  "rows_loaded": "10"
}
```

**Response (for non-text files)**:
```json
{
  "status": "skipped",
  "reason": "not_text_file"
}
```

**Note**: Eventarc triggers on ALL files in the bucket. Path filtering (`text/*.txt`) 
is done in the service code because GCS direct events only support `type` and `bucket` 
attributes for filtering.

### 2. Direct API (Testing)

**POST /api/v1/tabular/analyze**

Direct API endpoint for testing without Eventarc.

**Request**:
```json
{
  "file_id": "test-file-123",
  "region_id": "region-cz-01",
  "text_uri": "gs://bucket/text/test-file-123.txt",
  "original_content_type": "text/csv"
}
```

**Response**:
```json
{
  "file_id": "test-file-123",
  "status": "INGESTED",
  "table_type": "ASSESSMENT",
  "rows_loaded": 10,
  "bytes_processed": 1000,
  "cache_hit": false,
  "error_message": null,
  "warnings": [],
  "processing_time_ms": 250
}
```

### 3. Health Check

**GET /health**

Returns service status and model information.

**Response**:
```json
{
  "status": "ok",
  "service": "tabular-service",
  "version": "1.0.0",
  "models": {
    "embedding_model": "BAAI/bge-m3",
    "llm_model": "llama3.2:1b",
    "llm_enabled": true
  }
}
```

## Deployment

### Prerequisites

1. GCP Project with enabled APIs:
   - Cloud Run
   - Eventarc
   - BigQuery
   - Cloud Storage
   - Artifact Registry

2. Service Accounts:
   - `tabular-service@PROJECT_ID.iam.gserviceaccount.com`
   - `eventarc-trigger@PROJECT_ID.iam.gserviceaccount.com`

3. IAM Permissions:
   - BigQuery Data Editor
   - BigQuery Job User
   - Storage Object Viewer

### Build and Deploy

```bash
# Build Docker image
docker build -f docker/Dockerfile.tabular \
  -t europe-west1-docker.pkg.dev/PROJECT_ID/repo/tabular-service:latest .

# Push to Artifact Registry
docker push europe-west1-docker.pkg.dev/PROJECT_ID/repo/tabular-service:latest

# Deploy to Cloud Run
gcloud run services replace infra/tabular-config.yaml \
  --region europe-west1 \
  --platform managed

# Create Eventarc trigger
terraform apply -target=google_eventarc_trigger.tabular_text_files
```

### CI/CD

The service uses GitHub Actions for automated deployment:

```bash
# Trigger deployment
git push origin main

# Or manually trigger
gh workflow run deploy-tabular.yml
```

## Resource Requirements

- **Memory**: 4GB minimum (for AI models)
- **CPU**: 2 vCPUs
- **Concurrency**: 5 (lower due to memory-intensive models)
- **Timeout**: 300 seconds
- **Startup Time**: 20-30 seconds (model loading)

## Monitoring

### Key Metrics

- Request latency (p50, p95, p99)
- Error rate
- Memory usage
- CPU utilization
- Cold start frequency
- Model inference time

### Logs

All logs are structured JSON with correlation IDs:

```json
{
  "timestamp": "2025-01-14T10:30:00Z",
  "severity": "INFO",
  "message": "Pipeline completed",
  "event_id": "event-123",
  "file_id": "file-456",
  "status": "INGESTED",
  "table_type": "ASSESSMENT",
  "processing_time_ms": 250
}
```

## Troubleshooting

### Common Issues

**1. Model Loading Timeout**
- Increase `timeoutSeconds` in Cloud Run config
- Pre-download models in Dockerfile

**2. Out of Memory**
- Increase memory limit to 4GB or higher
- Reduce `containerConcurrency`

**3. Low Classification Confidence**
- Review concepts catalog
- Add more synonyms for concepts
- Check table structure

**4. Entity Resolution Failures**
- Verify entity cache is loaded
- Check fuzzy matching threshold
- Review entity names in BigQuery

## Development

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama
ollama serve &

# Pull Llama model
ollama pull llama3.2:1b

# Run tests
pytest tests/test_*tabular*.py -v

# Start service locally
uvicorn eduscale.main:app --reload --port 8080
```

### Testing CloudEvents

```bash
# Send test CloudEvent
curl -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-event",
    "type": "google.cloud.storage.object.v1.finalized",
    "data": {
      "bucket": "test-bucket",
      "name": "text/test-file.txt"
    }
  }'
```

## References

- [Design Document](../.kiro/specs/tabular-ingestion-pipeline/design.md)
- [Requirements](../.kiro/specs/tabular-ingestion-pipeline/requirements.md)
- [Tasks](../.kiro/specs/tabular-ingestion-pipeline/tasks.md)
- [Concepts Catalog](../config/concepts.yaml)
