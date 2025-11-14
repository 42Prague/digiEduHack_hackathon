# Tabular Model Cache Runbook

## Overview

This runbook covers operational procedures for managing the shared model cache for the Tabular service.

**Components:**
- GCS Bucket: `tabular-model-cache` (stores Ollama + SentenceTransformers models)
- Cloud Run Service: `tabular-service` (mounts bucket at `/models`)
- Cloud Run Job: `tabular-model-sync` (refreshes models nightly or on-demand)
- Cloud Scheduler: `tabular-model-sync-nightly` (triggers sync at 2 AM UTC)

## Quick Reference

| Task | Command |
|------|---------|
| Manual sync | `gcloud run jobs execute tabular-model-sync --region europe-west1` |
| Check manifest | `gsutil cat gs://tabular-model-cache/manifest.json` |
| View cache hits | `gcloud logging read 'jsonPayload.cache_hit=true' --limit=10` |
| Disable feature | `gcloud run services update tabular-service --set-env-vars SHARED_MODEL_VOLUME_ENABLED=false --region europe-west1` |
| Bucket size | `gsutil du -sh gs://tabular-model-cache` |

## Operational Procedures

### 1. Manual Model Sync

**When to use:**
- After updating model versions in Terraform
- Before major releases
- When cache hit rate is low
- If sync job failed

**Steps:**

```bash
# 1. Trigger sync job
gcloud run jobs execute tabular-model-sync \
  --region europe-west1 \
  --wait

# 2. Check job status
gcloud run jobs executions list \
  --job tabular-model-sync \
  --region europe-west1 \
  --limit 5

# 3. Verify manifest was updated
gsutil cat gs://tabular-model-cache/manifest.json | jq .

# 4. Check for .done marker
gsutil cat gs://tabular-model-cache/.done

# 5. Verify models exist
gsutil ls gs://tabular-model-cache/ollama/
gsutil ls gs://tabular-model-cache/sbert/
```

**Expected output:**
- Job execution status: `SUCCEEDED`
- Manifest contains `version`, `created_at`, models with checksums
- `.done` file contains version timestamp

### 2. Rollback to Previous Model Version

**Scenario:** New model version has issues, need to revert.

**Steps:**

```bash
# 1. List available versions in .tmp (if retained)
gsutil ls gs://tabular-model-cache/.tmp/

# 2. Option A: Restore from backup (if versioning enabled)
gsutil ls -a gs://tabular-model-cache/manifest.json

# Get previous version number
PREV_VERSION="<generation-number>"
gsutil cp "gs://tabular-model-cache/manifest.json#${PREV_VERSION}" \
  gs://tabular-model-cache/manifest.json

# 3. Option B: Re-run sync job with old model version
# Update Terraform variables first:
cd infra/terraform
# Edit terraform.tfvars: tabular_llm_model_name = "llama3.2:1b"
terraform apply

# Then trigger sync
gcloud run jobs execute tabular-model-sync \
  --region europe-west1 \
  --wait

# 4. Restart Cloud Run instances to pick up changes
gcloud run services update tabular-service \
  --region europe-west1 \
  --update-labels rollback=true

# 5. Verify cache hits with old model
gcloud logging read 'jsonPayload.manifest_version' --limit=10
```

### 3. Feature Toggle (Enable/Disable Shared Volume)

**Disable (emergency fallback):**

```bash
# Service will download models locally
gcloud run services update tabular-service \
  --region europe-west1 \
  --set-env-vars SHARED_MODEL_VOLUME_ENABLED=false

# Verify change
gcloud run services describe tabular-service \
  --region europe-west1 \
  --format='value(spec.template.spec.containers[0].env.find(SHARED_MODEL_VOLUME_ENABLED))'
```

**Re-enable:**

```bash
# Ensure models are synced first
gcloud run jobs execute tabular-model-sync --region europe-west1 --wait

# Re-enable shared volume
gcloud run services update tabular-service \
  --region europe-west1 \
  --set-env-vars SHARED_MODEL_VOLUME_ENABLED=true
```

### 4. Cleanup Old Model Versions

**When to use:**
- Bucket usage alert triggered
- Storage costs optimization
- Regular maintenance

**Steps:**

```bash
# 1. Check current bucket size
gsutil du -sh gs://tabular-model-cache
gsutil du -h gs://tabular-model-cache/

# 2. List .tmp directories
gsutil ls gs://tabular-model-cache/.tmp/

# 3. Remove old .tmp directories (older than 7 days)
# Note: Lifecycle policy should auto-delete, but manual cleanup if needed
gsutil -m rm -r gs://tabular-model-cache/.tmp/20241101-*

# 4. Verify bucket versioning (keep last 3)
gsutil versioning get gs://tabular-model-cache

# 5. Manually delete old object versions if needed
gsutil ls -a gs://tabular-model-cache/manifest.json
# Delete specific version:
# gsutil rm gs://tabular-model-cache/manifest.json#<generation>
```

### 5. Update Model Versions

**Scenario:** Upgrading from Llama 3.2 1B to 3B, or changing embedding model.

**Steps:**

```bash
# 1. Update Terraform variables
cd infra/terraform
vim terraform.tfvars

# Change:
# tabular_llm_model_name = "llama3.2:3b"
# tabular_embedding_model_name = "BAAI/bge-m3"

# 2. Apply Terraform (updates Cloud Run Job env vars)
terraform apply

# 3. Trigger sync job with new models
gcloud run jobs execute tabular-model-sync \
  --region europe-west1 \
  --wait

# 4. Monitor sync job logs
gcloud logging read \
  'resource.type="cloud_run_job"
   resource.labels.job_name="tabular-model-sync"' \
  --limit=100 \
  --format=json | jq '.[] | {time:.timestamp, message:.jsonPayload.message}'

# 5. Verify new models in bucket
gsutil ls -lh gs://tabular-model-cache/ollama/
gsutil cat gs://tabular-model-cache/manifest.json | jq '.models'

# 6. Deploy updated Cloud Run service (if env vars changed)
gcloud run services replace infra/tabular-config.yaml --region europe-west1

# 7. Verify cache hits with new models
gcloud logging read 'jsonPayload.cache_hit' --limit=20
```

### 6. Verify Cache Health

**Regular health check (run weekly):**

```bash
#!/bin/bash
# cache-health-check.sh

echo "=== Tabular Model Cache Health Check ==="
echo

# 1. Check manifest
echo "1. Manifest status:"
gsutil cat gs://tabular-model-cache/manifest.json | jq '{version, created_at, models}'
echo

# 2. Check .done marker
echo "2. Sync completion marker:"
gsutil cat gs://tabular-model-cache/.done
echo

# 3. Check bucket size
echo "3. Bucket storage:"
gsutil du -sh gs://tabular-model-cache
echo

# 4. Check cache hit rate (last 100 startups)
echo "4. Cache hit rate (last 100 logs):"
TOTAL=$(gcloud logging read 'jsonPayload.cache_hit' --limit=100 --format=json | jq '. | length')
HITS=$(gcloud logging read 'jsonPayload.cache_hit=true' --limit=100 --format=json | jq '. | length')
RATE=$(echo "scale=2; $HITS * 100 / $TOTAL" | bc)
echo "   Hits: $HITS / $TOTAL ($RATE%)"
echo

# 5. Check last sync job execution
echo "5. Last sync job:"
gcloud run jobs executions list \
  --job tabular-model-sync \
  --region europe-west1 \
  --limit 1 \
  --format='table(name,status,startTime)'
echo

# 6. Check alert policies
echo "6. Active alerts:"
gcloud alpha monitoring policies list \
  --filter='displayName~"Tabular"' \
  --format='table(displayName,enabled)'

echo
echo "=== Health Check Complete ==="
```

### 7. Disaster Recovery

**Scenario:** Bucket accidentally deleted or corrupted.

**Steps:**

```bash
# 1. Verify bucket exists
gsutil ls -L -b gs://tabular-model-cache

# 2. If bucket missing, recreate via Terraform
cd infra/terraform
terraform apply -target=google_storage_bucket.tabular_model_cache

# 3. Re-populate bucket
gcloud run jobs execute tabular-model-sync \
  --region europe-west1 \
  --wait

# 4. If job fails, disable shared volume temporarily
gcloud run services update tabular-service \
  --region europe-west1 \
  --set-env-vars SHARED_MODEL_VOLUME_ENABLED=false

# 5. Service continues running with local downloads

# 6. Once bucket is healthy, re-enable
gcloud run services update tabular-service \
  --region europe-west1 \
  --set-env-vars SHARED_MODEL_VOLUME_ENABLED=true
```

## Monitoring and Alerts

### Key Metrics

**Log-based metrics** (created by Terraform):
- `tabular_model_cache_hits`: Count of successful cache hits
- `tabular_model_cache_misses`: Count of cache misses with reasons
- `tabular_model_sync_success`: Successful sync job completions
- `tabular_model_sync_failure`: Failed sync job executions

**Alert policies** (when `enable_monitoring_alerts=true`):
1. **Low Cache Hit Rate**: Triggers if <90% over 1 hour
2. **Sync Job Failures**: Triggers on 2+ consecutive failures
3. **High Bucket Usage**: Triggers if >80% of quota

### Viewing Metrics

```bash
# Cache hit rate over last hour
gcloud logging read \
  'jsonPayload.cache_hit
   timestamp>="'"$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)"'"' \
  --format=json \
  | jq '[.[] | .jsonPayload.cache_hit] | group_by(.) | map({key: .[0], count: length})'

# Sync job history
gcloud run jobs executions list \
  --job tabular-model-sync \
  --region europe-west1 \
  --limit 10 \
  --format='table(name,status,startTime,completionTime)'

# Bucket storage over time (via Cloud Monitoring)
gcloud monitoring timeseries list \
  --filter='metric.type="storage.googleapis.com/storage/total_bytes" 
            resource.label.bucket_name="tabular-model-cache"' \
  --format='table(points.interval.endTime,points.value.int64Value)'
```

## Terraform Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `tabular_model_cache_capacity_gb` | `10` | Bucket capacity (for alerts) |
| `tabular_llm_model_name` | `llama3.2:1b` | Ollama model to download |
| `tabular_embedding_model_name` | `BAAI/bge-m3` | SentenceTransformers model |
| `enable_model_sync_schedule` | `false` | Enable nightly Cloud Scheduler |
| `enable_monitoring_alerts` | `false` | Enable alert policies |

## Troubleshooting

See `docs/DOCKER_OPTIMIZATION.md` → "Shared GCS Model Cache" → "Troubleshooting" for common issues.

## Related Documentation

- [DOCKER_OPTIMIZATION.md](./DOCKER_OPTIMIZATION.md) - Detailed feature documentation
- [Terraform README](../infra/terraform/README.md) - Infrastructure setup
- [Design Document](../.kiro/specs/tabular-shared-model-volumes/design.md) - Architecture
- [Requirements](../.kiro/specs/tabular-shared-model-volumes/requirements.md) - Feature requirements

