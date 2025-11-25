## System architecture

### Overview
The solution is a containerized micro‑stack fronted by Nginx. It comprises:
- Angular frontend (SPA)
- Agentic analysis service (FastAPI + Azure/OpenAI client)
- Ingestion service (FastAPI + SQLAlchemy + PostgreSQL)
- C++ backend (Drogon) prototype API
- PostgreSQL database
- Nginx reverse proxy (edge)

All services run on a shared bridge network and communicate via container DNS names. For local runs, `docker-compose` exposes a small set of ports; in production, only the reverse proxy is internet‑facing.

### Containers and responsibilities
- reverseproxy
  - Nginx entrypoint on port 80.
  - Routes:
    - `/` → `digiedu-frontend:4200` (Angular dev server in local, static hosting in prod).
    - `/agent/` → `digiedu-agent:8000` (FastAPI agent service).
    - `/ingest/` → `digiedu-ingest:8000` (FastAPI ingest service).
  - Backend route is present but commented out for now.

- frontend
  - Angular 17 application.
  - Uses `/agent/fancy_analyze` for LLM queries via the proxy.
  - Internationalization via JSON catalogues.

- agentic_analysis
  - FastAPI service exposing:
    - `GET /health`
    - `POST /fancy_analyze` (main LLM entrypoint; session-aware)
    - `GET /session/{session_id}` (poll conversation history)
  - Integrates with Azure OpenAI or public OpenAI via environment configuration.
  - Maintains a lightweight JSON session store on disk (swappable for a DB).

- ingest_service
  - FastAPI service handling file ingestion and extraction:
    - `POST /audio/upload` → async audio pipeline (e.g., transcription via faster‑whisper).
    - `POST /survey/ingest` → CSV/XLS parsing to structured tables.
    - `POST /raw/ingest` → generic document intake (PDF, etc.).
  - Persists to PostgreSQL via SQLAlchemy. Uses a volume for raw files.

- server (backend)
  - Drogon (C++) sample API (e.g., `/users`, `/users/{name}`).
  - Connects to PostgreSQL using env‑provided DSN.
  - Currently exposed directly on `:4444` in local; not routed by Nginx yet.

- digiedu-db
  - PostgreSQL with database `develop` and test credentials for local runs.
  - Shared among `server` and `ingest_service`.

### Dependencies and networking
- `server` → `digiedu-db` (PostgreSQL)
- `ingest_service` → `digiedu-db` (PostgreSQL)
- `frontend` → `agentic_analysis` via `/agent/`
- `frontend` → `ingest_service` via `/ingest/` (future UI integration)
- `reverseproxy` → `frontend`, `agentic_analysis`, `ingest_service`

All services join `digiedu_backend_network` (bridge). Volumes:
- `ingest_data` mounted at `/app/data` for raw files.

### Data flow (simplified)
1) User interacts with the Angular UI via Nginx (`/`).
2) For questions/analysis, the frontend calls `/agent/fancy_analyze`:
   - Agent runs tool‑augmented reasoning with Azure/OpenAI and keeps session state.
3) For data onboarding, clients post files to `/ingest/*` endpoints:
   - Ingest parses, extracts metadata, stores raw artifacts to the volume and structured entities in PostgreSQL.
4) The C++ backend is a high‑performance API layer (prototype) that will evolve to serve domain entities and analytics results; it already connects to the same PostgreSQL instance.

### Local ports (compose)
- Nginx: `http://localhost`
- Frontend (dev): proxied through `/`
- Agent: `http://localhost/agent/…` (container port 8000, host 8001)
- Ingest: `http://localhost/ingest/…` (container port 8000, host 8002)
- Backend (Drogon): `http://localhost:4444` (container 8080 → host 4444)
- PostgreSQL: `localhost:5435` (host) → `5432` (container)

## Data boundaries & privacy
- Dataset and derivatives remain within the designated environment; only `reverseproxy` is public.
- No direct egress from database/storage to external public AI services.
- Agent service is configured to use Azure OpenAI in an EU region and must receive anonymized/aggregated prompts (no raw PII).
- Secrets are provided via environment/Key Vault (in production); restrict logs to avoid sensitive payloads.
- Replace local JSON session store with a DB/Redis in production to centralize access control and auditing.
