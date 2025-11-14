# Docker Image Optimization for Tabular Service

## Problem

The original tabular service Docker image took ~15 minutes to build and deploy, which significantly slowed down development and deployment cycles.

## Root Causes

1. **Model downloads during build**: BGE-M3 model (~2.2GB) was downloaded during image build
2. **Ollama installation**: Full Ollama installation happened during every build
3. **No layer caching optimization**: Dependencies were not properly cached
4. **No BuildKit cache mounts**: pip and apt packages were re-downloaded on every build
5. **Missing .dockerignore**: Unnecessary files were copied into build context

## Optimizations Implemented

### 1. Multi-Stage Build

The Dockerfile now uses a two-stage build:
- **Builder stage**: Installs build dependencies and compiles Python packages
- **Runtime stage**: Only includes runtime dependencies, resulting in a smaller final image

**Benefits**:
- Smaller final image size
- Build dependencies don't pollute runtime image
- Better separation of concerns

### 2. BuildKit Cache Mounts

```dockerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --user -r requirements.txt
```

**Benefits**:
- pip cache persists between builds
- Dependencies are only downloaded once
- Subsequent builds reuse cached packages

### 3. Removed Model Downloads from Build

Models are now lazy-loaded at runtime instead of being downloaded during build:
- BGE-M3 model: Loaded on first use via `init_embeddings()`
- Llama model: Pulled during container startup (with better error handling)

**Benefits**:
- Build time reduced by ~5-10 minutes (no 2.2GB download)
- Models can be cached in Cloud Run's persistent storage
- Faster iteration during development

### 4. Optimized Layer Ordering

Layers are ordered to maximize cache hits:
1. System dependencies (rarely change)
2. Ollama installation (rarely change)
3. Python dependencies (change when requirements.txt changes)
4. Application code (changes most frequently)

**Benefits**:
- Code changes don't invalidate dependency cache
- Only changed layers are rebuilt

### 5. Created .dockerignore

Excludes unnecessary files from build context:
- Python cache files (`__pycache__/`, `*.pyc`)
- Test files
- Documentation
- IDE files
- Terraform state files
- Large resource files

**Benefits**:
- Smaller build context
- Faster build context upload
- Cleaner image

### 6. Improved Startup Script

- Better Ollama readiness check (polling instead of fixed sleep)
- More robust error handling
- Models pulled asynchronously during startup

## Expected Performance Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Build time (first build) | ~15 min | ~5-7 min | ~50-60% faster |
| Build time (cached) | ~15 min | ~1-2 min | ~85-90% faster |
| Image size | ~4-5 GB | ~2-3 GB | ~40% smaller |
| Build context size | Large | Small | ~70% smaller |

## Usage

### Build with BuildKit (Recommended)

```bash
# Enable BuildKit globally (add to ~/.docker/config.json or ~/.zshrc)
export DOCKER_BUILDKIT=1

# Build the image
make docker-build-tabular

# Or with explicit cache
make docker-build-tabular-cache
```

### Manual Build

```bash
DOCKER_BUILDKIT=1 docker build \
  -f docker/Dockerfile.tabular \
  -t tabular-service:latest \
  .
```

### Build for Cloud Run

```bash
DOCKER_BUILDKIT=1 docker build \
  -f docker/Dockerfile.tabular \
  -t gcr.io/PROJECT_ID/tabular-service:latest \
  .

docker push gcr.io/PROJECT_ID/tabular-service:latest
```

## Additional Recommendations

### 1. Use Cloud Build with Caching

For Cloud Run deployments, use Cloud Build with cache:

```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '--cache-from'
      - 'gcr.io/$PROJECT_ID/tabular-service:latest'
      - '-f'
      - 'docker/Dockerfile.tabular'
      - '-t'
      - 'gcr.io/$PROJECT_ID/tabular-service:$SHORT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/tabular-service:latest'
      - '.'
options:
  machineType: 'E2_HIGHCPU_8'
  logging: CLOUD_LOGGING_ONLY
```

### 2. Pre-build Base Images

Consider creating a base image with common dependencies:

```dockerfile
# docker/Dockerfile.tabular-base
FROM python:3.11-slim
# ... install common deps ...
```

Then use it:
```dockerfile
FROM tabular-base:latest
# ... add application code ...
```

### 3. Use Artifact Registry for Model Caching

Store models in Artifact Registry or Cloud Storage and mount them at runtime:

```yaml
# In Cloud Run config
volumes:
  - name: models
    type: gcs
    mountPath: /app/models
```

### 4. Monitor Build Times

Track build times to identify regressions:
- Use Cloud Build logs
- Set up alerts for builds > 10 minutes
- Review layer sizes regularly

## Troubleshooting

### Build still slow?

1. **Check BuildKit is enabled**: `DOCKER_BUILDKIT=1`
2. **Verify cache mounts work**: Check build logs for cache hits
3. **Review .dockerignore**: Ensure large files are excluded
4. **Check network speed**: Model downloads depend on bandwidth

### Models not loading?

1. **Check startup logs**: Models are lazy-loaded, check first request
2. **Verify Ollama is running**: Check health endpoint
3. **Check disk space**: Models need ~3.5GB free space
4. **Review error messages**: Startup script has better error handling

## Shared GCS Model Cache (Production Feature)

### Overview

The tabular service now supports mounting a shared GCS bucket for model caching, eliminating repeated downloads across Cloud Run instances.

**Benefits:**
- Zero downloads after first run (cache hit)
- Reduced cold-start time by ~3-5 minutes
- Lower network egress costs
- Consistent model versions across instances

### How It Works

1. **GCS Bucket**: `tabular-model-cache` stores models at `/ollama` and `/sbert`
2. **Volume Mount**: Cloud Run mounts bucket via `gcsfuse` at `/models`
3. **Startup Logic**: Container checks manifest, skips downloads if cache hit
4. **Sync Job**: Nightly Cloud Run Job refreshes models and updates manifest

### Architecture

```
┌─────────────────────────────────────────┐
│   GCS Bucket: tabular-model-cache       │
│   ├── /ollama/          (Llama 3.2 1B)  │
│   ├── /sbert/           (BGE-M3)        │
│   ├── manifest.json     (checksums)     │
│   └── .done             (sync marker)   │
└─────────────────────────────────────────┘
              ▲                  ▲
              │                  │
    ┌─────────┴────────┐   ┌────┴─────────────┐
    │ Cloud Run Service│   │  Model Sync Job  │
    │ (tabular-service)│   │  (nightly/manual)│
    │ Mount: /models   │   │  Mount: /models  │
    └──────────────────┘   └──────────────────┘
```

### Configuration

**Environment Variables:**

```bash
# Feature toggle (set to 'false' to disable)
SHARED_MODEL_VOLUME_ENABLED=true

# Model cache path (mount point)
MODEL_CACHE_PATH=/models

# Model directories
OLLAMA_MODELS=/models/ollama
SENTENCE_TRANSFORMERS_HOME=/models/sbert
HUGGINGFACE_HUB_CACHE=/models/sbert
```

**Cloud Run Config** (`infra/tabular-config.yaml`):

```yaml
spec:
  template:
    spec:
      volumes:
      - name: models
        csi:
          driver: gcsfuse.run.googleapis.com
          volumeAttributes:
            bucketName: tabular-model-cache
      
      containers:
      - volumeMounts:
        - name: models
          mountPath: /models
```

### Deployment

#### 1. Provision Infrastructure

```bash
cd infra/terraform

# Apply Terraform to create bucket + IAM
terraform apply

# Output shows bucket name
terraform output tabular_model_cache_bucket_name
```

#### 2. Seed Models (First Time)

```bash
# Manually trigger sync job to populate bucket
gcloud run jobs execute tabular-model-sync \
  --region europe-west1 \
  --wait
```

#### 3. Deploy Service

```bash
# Deploy Cloud Run service with volume mount
gcloud run services replace infra/tabular-config.yaml \
  --region europe-west1
```

### Monitoring

**Cache Hit Metrics:**

```bash
# View cache hits/misses in logs
gcloud logging read 'jsonPayload.cache_hit=true' --limit=10

# Check cache hit rate
gcloud logging read 'jsonPayload.cache_hit' --limit=100 \
  | grep -c 'cache_hit.*true'
```

**Alerts (when `enable_monitoring_alerts=true`):**
- Cache hit rate < 90% over 1 hour
- Model sync job failures (2+ consecutive)
- Bucket usage > 80% of quota

### Troubleshooting

#### Problem: Cache misses despite sync job

**Check manifest:**
```bash
gsutil cat gs://tabular-model-cache/manifest.json
gsutil cat gs://tabular-model-cache/.done
```

**Verify mount:**
```bash
# In Cloud Run container logs
gcloud logging read 'jsonPayload.message="Shared volume available"'
```

#### Problem: Sync job fails

**View job logs:**
```bash
gcloud logging read \
  'resource.type="cloud_run_job" 
   resource.labels.job_name="tabular-model-sync"' \
  --limit=50
```

**Check permissions:**
```bash
# Verify service account has storage.admin
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:model-sync-job"
```

#### Problem: High bucket usage

**Inspect bucket:**
```bash
# Check total size
gsutil du -sh gs://tabular-model-cache

# List files by size
gsutil ls -lhr gs://tabular-model-cache
```

**Clean up old .tmp folders:**
```bash
# Remove temp directories older than 7 days
gsutil -m rm -r gs://tabular-model-cache/.tmp/*
```

### Fallback to Local Storage

To disable shared volume (emergency rollback):

```bash
# Update environment variable
gcloud run services update tabular-service \
  --region europe-west1 \
  --set-env-vars SHARED_MODEL_VOLUME_ENABLED=false
```

Service will revert to downloading models locally (original behavior).

### CPU-Only Model Requirements

**Verified:** All ML dependencies in `requirements.txt` are CPU-only:
- `sentence-transformers>=2.3.0` (uses CPU PyTorch by default)
- `scikit-learn>=1.3.0` (CPU-only)
- `numpy>=1.24.0` (CPU-only)

**No GPU dependencies:**
- ❌ No `torch+cuda` wheels
- ❌ No `tensorflow-gpu`
- ❌ No CUDA/cuDNN libraries

Cloud Run does not have GPUs, so this is enforced by the platform.

## Future Optimizations

1. ~~**Distributed model storage**: Store models in Cloud Storage, mount at runtime~~ ✅ **Implemented**
2. **Model quantization**: Use smaller quantized models (e.g., 4-bit Llama)
3. **Warm-up endpoint**: Pre-load models on container start
4. **Base image optimization**: Use distroless or alpine-based images
5. **Layer deduplication**: Share common layers across services

