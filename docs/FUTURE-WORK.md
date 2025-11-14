## Future work and production hardening roadmap

This roadmap lists essential and potential improvements to operate the platform reliably at scale. Estimates are indicative and expressed in MD (man‑days) for an experienced engineer. Infra costs are monthly ballparks in EU regions.

### 1) Security, privacy, compliance
- Enforce authN/Z (OIDC/AAD) for all services via the proxy
  - 4–6 MD; infra: negligible
- Secrets management via Azure Key Vault + references in ACA
  - 1–2 MD; infra: €1–€3
- Private networking everywhere (VNet), no public DB/storage
  - 2–4 MD; infra: negligible
- Data classification and PII minimization policy at API boundaries
  - 2–3 MD; infra: negligible
- Audit logging of access to sensitive endpoints
  - 2–3 MD; infra: €5–€15 (logs)

### 2) Observability and SRE
- Centralized logs/metrics/traces (Azure Monitor, OpenTelemetry)
  - 3–5 MD; infra: €10–€30 (usage‑dependent)
- Health checks, readiness/liveness probes per service
  - 1–2 MD; infra: negligible
- Alerts and on‑call dashboards (latency, errors, saturation, cost)
  - 2–3 MD; infra: €5–€15

### 3) Data layer hardening
- Migrate agent session store from file to Redis/PostgreSQL
  - 2–3 MD; infra: €10–€30 (Redis optional)
- Database schema versioning and migrations (Alembic/flyway/liquibase)
  - 2–3 MD; infra: negligible
- Backup/restore + PITR and disaster recovery playbooks
  - 2–3 MD; infra: included with PG; ops time only
- Data retention and lifecycle rules (Storage/Blob policies)
  - 1–2 MD; infra: negligible

### 4) Agent & AI reliability
  - 2–3 MD; infra: negligible
- Prompt/response guardrails: size limits, redaction, PII filters
  - 3–5 MD; infra: negligible
- Tooling sandbox for safe data access (read‑only scopes, quotas)
  - 3–5 MD; infra: negligible
- Batch/async job queue for long‑running analysis (RQ/Celery/ACA jobs)
  - 4–6 MD; infra: €10–€30

### 5) Ingestion robustness and scale
- Async file pipeline with retries, dead‑letter, and idempotency
  - 4–6 MD; infra: €10–€30
- Virus scanning and file type validation at edge
  - 2–3 MD; infra: €5–€15
- Transcription workloads: offload to queue + autoscaled workers
  - 3–5 MD; infra: €10–€40

### 6) Backend evolution (C++ Drogon or Python API)
- Expand domain endpoints with pagination, caching, and E2E tests
  - 5–8 MD; infra: negligible
- Role‑based access control and resource scoping
  - 3–5 MD; infra: negligible

### 7) Frontend (UX, performance, governance)
- Add auth flows (OIDC), privacy disclaimers
  - 3–5 MD; infra: negligible
- Telemetry (user actions, errors) with privacy‑safe analytics
  - 2–3 MD; infra: €5–€10
- Accessibility and localization coverage expansion
  - 3–5 MD; infra: negligible

### 8) CI/CD and release management
- CI (lint, test, build) + SAST/Dependabot + Docker SBOMs
  - 3–5 MD; infra: €0–€20 (runner usage)
- CD to ACA with blue/green or canary releases
  - 3–5 MD; infra: negligible
- Infrastructure as Code (Bicep/Terraform) for reproducible environments
  - 5–8 MD; infra: negligible

### 9) Cost optimization
- Scale‑to‑zero on all stateless services; right‑size CPU/RAM
  - 1–2 MD; infra: cost reduction
- Log retention 7–14 days; sampling for traces
  - 1 MD; infra: cost reduction
- Use burstable/flexible PG tiers; schedule scale‑up windows
  - 1–2 MD; infra: cost reduction

### 10) Risk register (top)
- Data egress to non‑EU AI endpoints
  - Mitigation: region pinning, proxy egress controls, tests (1–2 MD)
- PII leakage through prompts/logs
  - Mitigation: input filters, redaction, log scrubbing (3–5 MD)
- Long‑running jobs blocking web workers
  - Mitigation: async queues, background workers, timeouts (4–6 MD)

### Summary estimate
- Full confident setup (incl. CI/CD, data pipeline hardening, AI guardrails): ~45–65 MD


