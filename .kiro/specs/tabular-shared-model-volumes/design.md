# Design Document

## Overview

This design explains how the Tabular service shares heavy AI model artifacts (Ollama Llama 3.2 1B weights and SentenceTransformer BGE-M3 cache) across all Cloud Run instances by mounting a Cloud Storage (GCS) bucket via the new Cloud Run `cloudStorage` volume feature. Instead of every replica downloading ~3.5 GB during startup, models are stored once in a dedicated bucket (`gs://tabular-model-cache`) and exposed inside containers at `/models`. Ollama and sentence-transformers cache directories point to that mount so downloads happen once and are reused across scale events, reducing cold-start time, network egress, and duplicated storage while keeping the runtime CPU-only.

### Goals

1. Eliminate repeated downloads of Llama and BGE-M3 artifacts per Cloud Run instance.
2. Keep models available across deployments and scale events without rebuilding the container.
3. Preserve deterministic model versions with centralized lifecycle management.
4. Avoid introducing external SaaS dependencies; stay within GCP managed services.
5. Keep the runtime CPU-only to match Cloud Run’s capabilities (no GPU drivers or CUDA wheels).

### Non-Goals

- Replacing Ollama with an external inference API.
- Changing Tabular inference logic (LLM prompts, embeddings usage).
- Supporting GPU workloads.

## Architecture

### High-Level Components

```
+-------------------------+      +--------------------------+
| Cloud Storage Bucket    |<---->| Cloud Run cloudStorage   |
| (tabular-model-cache)   |      | volume mounted at /models|
+-------------------------+      +--------------------------+
           ^                                   ^
           |                                   |
   Cloud Run Job (sync)              Cloud Run Service (Tabular)
```

1. **GCS Bucket (`tabular-model-cache`)**: Stores `/ollama`, `/sbert`, and `manifest.json`.
2. **Cloud Run Tabular Service**: Mounts the bucket via `cloudStorage` at `/models` and sets `OLLAMA_MODELS`, `SENTENCE_TRANSFORMERS_HOME`, and `HUGGINGFACE_HUB_CACHE` to subdirectories.
3. **Model Sync Job**: Cloud Run Job that refreshes the bucket contents (pulls models, writes manifests, manages versions).

### Sequence Diagram

```
Admin/CI     Model Sync Job     GCS Bucket         Tabular Instance
   |               |                |                     |
1. trigger job ---->                |                     |
   |               | 2. mount /models (GCS)               |
   |               |-------------------->                 |
   |               | 3. ollama pull/write temp objects    |
   |               |-------------------->                 |
   |               | 4. atomic rename + manifest update   |
   |               |-------------------->                 |
   |               |                |                     |
   |               |                | 5. mount /models    |
   |               |                |<--------------------|
   |               |                | 6. start Ollama     |
   |               |                |-------------------->|
   |               |                | 7. cache hit        |
```

### Data Flows

1. The sync job downloads models to `/models/.tmp/<version>` (GCS temp prefix) and, after checksum validation, renames to `/models/ollama/<version>` and updates `manifest.json`.
2. Tabular service instances mount the bucket read-write; on startup they compare the manifest hash with local metadata to decide whether an `ollama pull` is necessary. If files exist, Ollama immediately serves without internet downloads.
3. Versions are tracked through folder naming (`/models/ollama/llama3.2-1b-2025-11-14`). An env var indicates which version is active; rollback just points to the previous prefix.

## Detailed Design

### 1. Infrastructure (Terraform)

- Create a dedicated bucket `tabular-model-cache` with:
  - Region `europe-west1`.
  - Uniform bucket-level access enabled.
  - Versioning enabled for safety.
- Grant the Tabular Cloud Run service account `roles/storage.objectAdmin` on the bucket (read/write) and the sync job account `roles/storage.admin`.
- Update Cloud Run deployment spec to mount the bucket:
  ```yaml
  volumes:
    - name: models
      cloudStorage:
        bucket: tabular-model-cache
        readOnly: false
  containers:
    - volumeMounts:
        - name: models
          mountPath: /models
  ```
- No VPC connector or firewall changes are required; access goes over Google’s internal network.

### 2. Container Runtime Changes

- Update `docker/Dockerfile.tabular`:
  ```
  ENV OLLAMA_MODELS=/models/ollama \
      SENTENCE_TRANSFORMERS_HOME=/models/sbert \
      HUGGINGFACE_HUB_CACHE=/models/sbert \
      MODEL_CACHE_PATH=/models
  ```
- Startup script enhancements:
  1. Validate that `/models` is mounted (e.g., check for `.gcsfuse` marker).
  2. Download `manifest.json` (already on mount) and compare with local metadata.
  3. If manifest version matches, skip `ollama pull` and log `cache_hit=true`.
  4. If mismatch, run `ollama pull` once, write to `/models/ollama/<version>`, and update manifest (only when `SHARED_MODEL_VOLUME_ENABLED=true`).
  5. Handle GCS eventual consistency by using manifest-based gating: only trusted after checksum file exists.
- SentenceTransformer automatically reuses cached weights from `/models/sbert`; set env vars and ensure the manifest flow covers embedding cache too.
- Audit `requirements.txt` to keep ML dependencies CPU-only and document enforcement.

### 3. Model Sync Job

- Reuse the Tabular image with `MODEL_SYNC_MODE=1`.
- Job steps:
  1. Mount `/models` (GCS).
  2. Pull each target model into `/models/.tmp/<model>-<timestamp>`.
  3. Generate SHA256 checksums and write `manifest.json.tmp`.
  4. Atomically rename temp directories/files using `gsutil mv` (two-phase commit).
  5. Remove old versions beyond retention policy (e.g., keep last three).
- Job is invoked manually before releases and nightly via Cloud Scheduler (`gcloud scheduler jobs create http ...` hitting Cloud Run Job).

### 4. Configuration Updates

- `infra/tabular-config.yaml`:
  - Add `volumes`/`volumeMounts` with `cloudStorage`.
  - Set env vars: `OLLAMA_MODELS`, `SENTENCE_TRANSFORMERS_HOME`, `HUGGINGFACE_HUB_CACHE`, `MODEL_CACHE_PATH`, `SHARED_MODEL_VOLUME_ENABLED`.
- `docs/DOCKER_OPTIMIZATION.md`: new section “Shared GCS model cache” describing mount, sync job, and toggle.

### 5. Rollout Strategy

1. Provision bucket and grant IAM.
2. Run sync job to seed models (ensuring `.tmp` workflow succeeds).
3. Deploy Cloud Run revision with bucket mount + feature toggle enabled in staging.
4. Hit warm-up endpoint to ensure cache hits; confirm logs show `cache_hit=true`.
5. Load-test with ≥3 instances to verify zero duplicate downloads.
6. Enable in production and monitor metrics.

### Failure Modes & Mitigations

| Failure | Impact | Mitigation |
|---------|--------|------------|
| Bucket unavailable | Containers fail to read models | Startup exits early; Cloud Run restarts. Alert on 5xx spikes. |
| Eventual consistency delay | Manifest update not immediately visible | Use versioned objects with checksum guard; startup waits until manifest + `.done` file present. |
| Partial uploads | Corrupt models | Sync job writes to `.tmp` and only flips manifest after checksum; old version remains as fallback. |
| Permission misconfig | Read/write denied | Terraform-managed IAM; startup health check verifies access and logs actionable error. |

### Security Considerations

- Bucket uses uniform access; no ACLs.
- Service accounts limited to required roles.
- Manifest includes signed checksums to detect tampering.
- Optional CMEK (customer-managed key) can encrypt bucket if compliance requires.

### Open Questions

1. How aggressively should we garbage-collect old versions (size vs rollback needs)?
2. Do we need per-environment buckets (e.g., `-staging`, `-prod`) for isolation?
3. Should sync job be triggered automatically on code deploys or remain manual (CI pipeline step)?

