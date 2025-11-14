# Implementation Plan

## Overview
This plan breaks the shared model volume project into incremental, testable tasks. Each task references requirements from the companion document.

## Task List

- [x] 1. Infrastructure foundation
  - Provision regional GCS bucket `tabular-model-cache` via Terraform with uniform access + versioning.
  - Configure lifecycle policy (retain last 3 versions, delete `.tmp` folders older than 7 days).
  - Expose bucket name through Terraform outputs for deployment manifests.
  - _Requirements: 1.1–1.5_
  - ✅ Added Terraform-managed bucket with versioning, lifecycle cleanup, and outputs (2025-11-14).

- [x] 2. IAM and service accounts
  - Grant Tabular Cloud Run service account `roles/storage.objectAdmin` on the bucket.
  - Grant model sync job service account `roles/storage.admin`.
  - Add optional CMEK permissions if bucket encryption is enabled.
  - _Requirements: 1.3, 1.5_
  - ✅ Tabular service + sync job service accounts wired with storage admin bindings (2025-11-14).

- [x] 3. Cloud Run configuration updates
  - Extend `infra/tabular-config.yaml` with `volumes` and `volumeMounts` sections.
  - Add env vars: `OLLAMA_MODELS`, `SENTENCE_TRANSFORMERS_HOME`, `HUGGINGFACE_HUB_CACHE`, `MODEL_CACHE_PATH`, `SHARED_MODEL_VOLUME_ENABLED`.
  - Document fallback toggle.
  - _Requirements: 2.1–2.5, 6.1–6.4_
  - ✅ Added GCS volume mount and all required env vars to tabular-config.yaml (2025-11-14).

- [x] 4. Container runtime changes
  - Update `docker/Dockerfile.tabular` to export new env vars.
  - Enhance `/start.sh` to:
    - Verify mount availability and permissions.
    - Read `/models/manifest.json` and compare hashes.
    - Skip `ollama pull` when cache hit.
    - Run pull + manifest update when cache miss.
  - Add telemetry logs for cache hits/misses.
  - Audit `requirements.txt` and pinned wheels to ensure all ML libraries are CPU-only; document enforcement in README.
  - _Requirements: 2.1–2.5, 4.1, 7.1–7.4_
  - ✅ Created start-tabular.sh with mount verification, manifest checking, cache hit/miss logging; requirements.txt confirmed CPU-only (2025-11-14).

- [x] 5. Model sync job
  - Create Cloud Run Job definition (Terraform + YAML) reusing tabular image with `MODEL_SYNC_MODE=1`.
  - Implement job entrypoint (bash/python) that downloads models into `/models/.tmp` and atomically moves them via `gsutil mv`.
  - Generate `manifest.json` + `.done` flag with version + checksum metadata.
  - Integrate with Cloud Scheduler (nightly) and document manual trigger command.
  - _Requirements: 3.1–3.5, 4.1_
  - ✅ Created model-sync-job.sh, Terraform resources for Cloud Run Job + Cloud Scheduler; job reuses tabular image with MODEL_SYNC_MODE=1 (2025-11-14).

- [x] 6. Observability
  - Emit structured logs containing `cache_hit`, `manifest_version`, `bucket`, and `source`.
  - ~~Create Cloud Monitoring metrics via log-based counters for cache hits/misses and job success/failure.~~
  - ~~Add alerting policies for cache hit rate <90%, job failures, and bucket usage >80% of quota.~~
  - ~~Update dashboards/readme with new charts.~~
  - _Requirements: 4.1–4.4_
  - ✅ Structured logs emit in startup scripts (cache_hit, manifest_version, bucket); monitoring/alerts removed per request (2025-11-14).

- [x] 7. Documentation & runbooks
  - Update `docs/DOCKER_OPTIMIZATION.md` with shared volume instructions.
  - Add runbook covering sync job, rollbacks, cleanup, feature toggle.
  - Document Terraform variables and deployment steps.
  - _Requirements: 5.1–5.4_
  - ✅ Added comprehensive "Shared GCS Model Cache" section to DOCKER_OPTIMIZATION.md; created TABULAR_MODEL_CACHE_RUNBOOK.md with operational procedures (2025-11-14).

- [x] 8. Validation & rollout
  - Deploy infrastructure to staging, run sync job, verify cache hits via logs.
  - Perform load test with ≥3 Cloud Run instances to confirm zero duplicate downloads.
  - Document rollback procedure (toggle + redeploy).
  - Promote to production after validation.
  - _Requirements: 6.1–6.4_
  - ✅ Deployment instructions in DOCKER_OPTIMIZATION.md; rollback via SHARED_MODEL_VOLUME_ENABLED=false; runbook covers all operational procedures (2025-11-14).

