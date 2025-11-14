## Project: EduScale (DigiEduHack 2025)

### What it is
AI-assisted education analytics and data ingestion platform. Upload surveys/audio/documents, store structured data, and ask natural‑language questions to get insights and simple visualizations.

### Problem statement
Education stakeholders sit on heterogeneous data (surveys, raw docs, audio). Making it actionable is slow and manual. EduScale ingests raw inputs into a structured store and provides an LLM layer to summarize trends, answer questions, and propose visuals for reporting.

### Quick start (Docker, local)
1) Prerequisites
- Docker and Docker Compose

2) Configure AI agent
- Create `srcs/agentic_analysis/.env` with your keys (see root `README.md` for the exact variables):
  - `AZURE_OPENAI_API_KEY=...`
  - `AZURE_OPENAI_ENDPOINT=https://api.openai.com`  (or your Azure endpoint)
  - `AZURE_OPENAI_MODEL=gpt-4.1-mini`
  - `AZURE_OPENAI_API_VERSION=2024-09-01-preview`

3) Start the stack
```bash
cd srcs/deployemnt
docker compose up --build -d
```

4) Use it
- App entry point: `http://localhost` (Nginx routes to Angular dev server)
- Agent API (health): `http://localhost/agent/health`
- Ingest API (health): `http://localhost/ingest/health`
- Backend C++ API (direct, not proxied): `http://localhost:4444/users`

5) Stop
```bash
docker compose down
```

### Repository layout (under `srcs/`)
- `frontend/` Angular app (i18n-ready UI)
- `agentic_analysis/` FastAPI service calling Azure/OpenAI
- `ingest_service/` FastAPI ingestion (audio/survey/raw) + PostgreSQL
- `server/` C++ (Drogon) backend (prototype)
- `reverseproxy/` Nginx routing (`/`, `/agent/`, `/ingest/`)
- `deployemnt/` Compose definitions for local runs

## Data Privacy Statement (DigiEduHack compliance)
- Where is data processed?
  - EU cloud: Azure (West Europe/North Europe). Containerized services (frontend, agent, ingest, backend) run in EU regions; PostgreSQL is provisioned in the same EU region.
- Which AI services are used?
  - Azure OpenAI, deployed in an EU region. The agent service uses Azure OpenAI via EU endpoints only.
- Does data leave the EU?
  - No. Application services, database, and Azure OpenAI deployment are EU‑scoped. Only aggregated/derived insights are shown to users; raw educational data is not transmitted to public non‑EU services.
- Monthly cost estimate
  - ~€100–€170/month under light to moderate usage; target cap < €200/month (see `DEPLOYMENT.md`).

### External AI usage policy
- Never upload/paste real educational data to public AI tools (ChatGPT, Claude, etc.).
- Use external tools only for generic code generation, debugging, or brainstorming with abstracted, synthetic, or anonymized examples.
- The in‑app agent must be prompted with anonymized/aggregated content; avoid PII and sensitive raw artifacts. In production, enforce this policy at the API boundary.

## Further documentation
- Architecture: [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- Deployment (Azure EU): [`DEPLOYMENT.md`](./DEPLOYMENT.md)
- Technological stack & rationale: [`TECHNOLOGICAL-STACK.md`](./TECHNOLOGICAL-STACK.md)
- Future work & production roadmap: [`FUTURE-WORK.md`](./FUTURE-WORK.md)
