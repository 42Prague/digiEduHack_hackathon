# Requirements Document

## Introduction

The Tabular service currently downloads large AI models (Llama 3.2 1B via Ollama and BGE-M3 embeddings) on every Cloud Run instance startup. With autoscaling, this leads to duplicated network traffic, long cold starts, and unpredictable costs. This document defines the requirements for sharing model artifacts across instances through a common volume, ensuring that models are fetched once and reused by all replicas.

## Glossary

- **Shared Model Volume**: A Cloud Storage bucket mounted into Cloud Run containers via `cloudStorage` volumes to store model artifacts.
- **Model Sync Job**: A Cloud Run Job responsible for populating and refreshing the shared model volume.
- **Manifest**: Metadata file that records versions, checksums, and timestamps for cached models.
- **Cache Path**: Filesystem path mapped to the shared volume (e.g., `/models`).

## Requirements

### Requirement 1: Shared Storage Provisioning

**User Story:** As a DevOps engineer, I want a centralized storage location for model artifacts, so that multiple Cloud Run instances reuse the same files.

#### Acceptance Criteria

1. The infrastructure SHALL provision a dedicated GCS bucket (e.g., `tabular-model-cache`) in the same region as the Tabular service.
2. The bucket SHALL be mounted into Cloud Run via a `cloudStorage` volume at `/models`.
3. The Cloud Run service account SHALL have `storage.objectAdmin` access to the bucket; the sync job account SHALL have `storage.admin`.
4. Bucket versioning SHALL be enabled to protect against accidental overwrites.
5. Uniform bucket-level access SHALL be enforced (no legacy ACLs), and CMEK SHALL be optional but documented.

### Requirement 2: Container Integration

**User Story:** As a backend engineer, I want the Tabular container to use the shared volume for model caches, so that startup skips redundant downloads.

#### Acceptance Criteria

1. The container SHALL set `OLLAMA_MODELS=/models/ollama` before starting the Ollama daemon.
2. The container SHALL set `SENTENCE_TRANSFORMERS_HOME=/models/sbert` and `HUGGINGFACE_HUB_CACHE=/models/sbert`.
3. The startup script SHALL detect existing Ollama models and skip `ollama pull` if hashes match the manifest.
4. When the manifest indicates a newer model version, the startup script SHALL pull the new version and update the manifest.
5. The container SHALL fail fast (exit with non-zero code) if the shared volume is unavailable.

### Requirement 3: Model Sync Workflow

**User Story:** As a platform engineer, I want an automated workflow to populate models into the shared volume, so that deployments always use the intended versions.

#### Acceptance Criteria

1. A Cloud Run Job SHALL mount the same `/models` volume (GCS) and run on demand or by schedule.
2. The job SHALL download `llama3.2:1b` via `ollama pull` into `/models/.tmp/ollama-<version>` before promoting it.
3. The job SHALL download `BAAI/bge-m3` via sentence-transformers into `/models/.tmp/sbert-<version>`.
4. The job SHALL write/update `/models/manifest.json` with model name, version, checksum, timestamp, and a `.done` marker to signal consistency.
5. The job SHALL perform uploads via temporary prefixes and use atomic `gsutil mv` (or Storage Compose rename) to avoid partial files.

### Requirement 4: Observability & Alerts

**User Story:** As an SRE, I want visibility into model cache health, so that I can detect failures early.

#### Acceptance Criteria

1. Logs SHALL include model version, manifest checksum, and source (sync job vs startup) for every change.
2. Metrics SHALL record cache hit rate (number of startups skipping downloads vs total startups).
3. Cloud Monitoring alerts SHALL trigger when:
   - Cache hit rate falls below 90% over 1 hour.
   - Model sync job fails consecutively twice.
   - Bucket storage usage exceeds 80% of the configured quota.
4. Dashboards SHALL display current manifest info and last sync timestamp.

### Requirement 5: Documentation & Operations

**User Story:** As an on-call engineer, I need clear runbooks, so that I can manage model lifecycle safely.

#### Acceptance Criteria

1. Documentation SHALL describe how to run the sync job manually, update model versions, and roll back to previous versions.
2. The runbook SHALL outline procedures for:
   - Inspecting `/models/manifest.json`.
   - Cleaning up old model folders.
   - Verifying permissions for service accounts.
3. The README SHALL include prerequisites for enabling Cloud Storage volumes in Cloud Run (permissions, beta flag if applicable).
4. The Terraform README SHALL explain new variables (e.g., `tabular_models_capacity_gb`).

### Requirement 6: Backward Compatibility

**User Story:** As a release manager, I need the option to fall back to the previous behavior, so that we can recover quickly if shared volumes fail.

#### Acceptance Criteria

1. Environment variables SHALL allow disabling shared volume usage (`SHARED_MODEL_VOLUME_ENABLED=false`).
2. When disabled, the container SHALL revert to pulling models locally (current behavior).
3. Deployment pipelines SHALL expose a flag to toggle the feature per environment.
4. Documentation SHALL describe the toggle and trade-offs.

### Requirement 7: CPU-Only Dependency Footprint

**User Story:** As a platform engineer, I want the container image to include only CPU-compatible ML libraries, so that we avoid pulling unnecessary GPU runtimes on Cloud Run (which lacks GPUs).

#### Acceptance Criteria

1. The requirements list SHALL exclude CUDA/cuDNN or GPU-specific torch/transformers wheels.
2. The Dockerfile SHALL install only CPU variants of ML packages (e.g., `torch==...+cpu` if needed).
3. Documentation SHALL note that Cloud Run deployments are CPU-only and that GPU packages are unsupported.
4. During code review, any introduction of GPU dependencies SHALL be flagged as non-compliant with this spec.

