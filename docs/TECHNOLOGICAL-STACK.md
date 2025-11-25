## Technology stack and rationale

### Frontend (development/runtime)
- Angular 17 (TypeScript, RxJS)
  - Mature, batteries‑included framework with strong typing and structured architecture.
  - Built‑in routing, forms, and ecosystem support reduce custom glue code.
- @ngx-translate
  - Simple JSON‑based i18n to support multilingual UIs.

### Agentic analysis service
- Python FastAPI + Uvicorn
  - Fast development cycle, async I/O, Pydantic models for contracts.
- OpenAI/Azure OpenAI (Responses API via `openai` SDK)
  - Vendor‑switchable by configuration; leverages state‑of‑the‑art LLMs.
- pydantic‑settings, dotenv
  - Clean configuration via environment, suitable for containerized deployments.

### Ingestion service
- Python FastAPI + SQLAlchemy + Psycopg
  - Robust ORM for PostgreSQL; async‑friendly stack.
- File processing libraries
  - `pandas`, `openpyxl`, `xlrd` for tabular survey inputs.
  - `pdfplumber` for PDF extraction.
  - `faster-whisper` for audio transcription.

### Backend API (prototype)
- C++ Drogon
  - High‑performance HTTP server for future low‑latency endpoints.
  - Suits scenarios where throughput and efficiency are critical.

### Data layer
- PostgreSQL
  - Reliable, feature‑rich relational database with broad ecosystem support.

### Edge and routing
- Nginx reverse proxy
  - Stable, minimal overhead, easy upstream mapping and TLS termination.

### Containerization and orchestration
- Docker, Docker Compose (local)
  - Reproducible local environment; single command to bring up the stack.
- Azure Container Registry + Azure Container Apps (recommended prod)
  - Managed image hosting and autoscaling serverless containers with scale‑to‑zero.

### Observability and security (recommended prod)
- Azure Monitor (Log Analytics)
  - Centralized logs/metrics with adjustable retention to control costs.
- Azure Key Vault
  - Managed secrets for DB and API keys.

### Why this stack
- **Velocity**: FastAPI + Angular speed up iteration; clear contracts with Pydantic/TypeScript.
- **Flexibility**: Agent can switch between public OpenAI and Azure OpenAI by config.
- **Performance headroom**: Drogon enables high‑performance endpoints where needed.
- **Simplicity**: Nginx + Container Apps keep infra lean and cost‑efficient.
- **Portability**: Everything is containerized; dev/prod parity is straightforward.

## Alignment with DigiEduHack solution guidelines (justification)
- Clarity of problem and solution
  - Stack separates concerns: ingestion (data onboarding), agent (insights), UI (communication). This mirrors the problem → pipeline → insight user flow.
- Innovation and creativity
  - Agentic analysis blends structured ingest with LLM reasoning/tool use to propose plots and summaries, beyond simple dashboards.
- Impact and scalability
  - Azure Container Apps with autoscale and scale‑to‑zero; stateless services; PostgreSQL as a reliable core store; straightforward horizontal scaling when load grows.
- Feasibility and sustainability
  - Commodity, well‑documented components (Angular, FastAPI, PostgreSQL, Nginx). Ops footprint is small; cost target < €200/month at low/medium usage (see Deployment).
- User‑centric design
  - Angular UI with i18n (`@ngx-translate`) enables multilingual access; agent endpoint designed for session continuity to support conversational use.
- Data privacy and ethics
  - EU hosting (West/North Europe). Azure OpenAI deployed in EU region only. Secrets in Key Vault; only proxy is public. Replace local JSON session store with DB/Redis in production; data‑minimization (no raw PII to external AI, anonymized/aggregated prompts only).
- Openness and interoperability
  - Standard HTTP/REST, JSON contracts with Pydantic/TypeScript types; portable Docker images; vendor‑switchable LLMs (Azure/OpenAI).
- Quality of documentation and delivery
  - Architecture, deployment, and quick‑start docs included; environment variables and routes are explicit; local compose for reproducibility and live demos.

