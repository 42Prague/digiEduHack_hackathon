# 🎓 EduScale Engine

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-🚀-brightgreen)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
![DigiEduHack 2025](https://img.shields.io/badge/DigiEduHack-2025-blue)
![Eduzměna](https://img.shields.io/badge/Eduzměna-Foundation-green)

**EduScale Engine** is an open-source data infrastructure solution built for **Eduzměna Foundation** as part of **DigiEduHack 2025**. It transforms manual data analysis processes into an automated, scalable system capable of handling diverse educational data from 5,000+ Czech schools.

> Built for **Eduzměna Foundation** to scale educational impact nationwide.

---

## ✨ Core Features (EduScale Engine)

### 📥 Data Input Layer
- **Multi-format ingestion**: Accepts `.xlsx`, `.csv`, `.docx`, and `.md` files
- **Automatic schema detection**: Infers column types, null ratios, and data quality
- **PII masking**: GDPR-compliant anonymization (emails, phones, names)
- **Validation & logging**: Comprehensive error tracking and audit trails

### 🤖 AI-Powered Processing Core
- **Automatic classification**: Quantitative vs qualitative dataset detection
- **NLP theme extraction**: LLM-powered insight generation (Ollama recommended, heuristic fallback, or EU-hosted Azure OpenAI)
- **Full-text search**: Intelligent content indexing and retrieval
- **TONE format support**: 40-50% token reduction for LLM consumption
- **Privacy-first AI**: Self-hosted Ollama by default, no data leaves your infrastructure

### 📊 BI & Analytics Engine
- **Statistical metrics**: Mean, median, std, min, max for numeric columns
- **Trend analysis**: Cross-regional performance tracking over time
- **Impact measurement**: Intervention effectiveness analysis
- **Data visualization**: Ready-to-use metrics for dashboards

### 🖥️ User Dashboard Interface
- **Multi-level filtering**: National → regional → school-level views
- **Real-time updates**: Live data processing and summary generation
- **Comparison tools**: Side-by-side school and region analysis
- **Export capabilities**: JSON and TONE format outputs

---

## 📁 Project Structure

```bash
swx_api/
├── app/                # User-defined application logic (routes, services)
├── core/               # Core framework logic (auth, db, utils, etc.)
├── docs/               # MkDocs documentation
├── alembic/            # Alembic migrations
├── scripts/            # CLI scripts
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Base Compose config
└── ...

```
### 🛠️ Installation

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (optional)
- PostgreSQL

### 📦 Clone the Repository

```bash
git clone https://github.com/yourusername/swx-api.git
cd swx-api
```

### 🐍 Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 📥 Install Dependencies

```bash
pip install -r requirements.txt
```

### ⚙️ Configure Environment Variables

Create a `.env` file in the project root with the following content:

```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/swx_db
JWT_SECRET_KEY=your_jwt_secret
```

> Replace `user`, `password`, and `swx_db` with your actual PostgreSQL credentials and database name.

### 🔄 Run Database Migrations

```bash
swx migrate
```

### 🚀 Start the Development Server

```bash
uvicorn main:app --reload
```

---

### 🐳 Run with Docker (Optional)

If you prefer using Docker:

```bash
docker-compose up --build
```

> This will spin up the app along with PostgreSQL using the provided `docker-compose.yml`.

---

## 🧠 Ingestion & Processing Pipeline

The EduScale ingestion pipeline is available directly from the FastAPI backend.

### Endpoints

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/ingestion/ingest` | `POST` | Upload `.xlsx`, `.csv`, `.docx`, or `.md` files. Files are stored under `data/raw/`, PII is masked, schemas are profiled, and summaries are generated. |
| `/api/ingestion/datasets` | `GET` | List all normalized datasets and their corresponding summary artifacts. |
| `/api/ingestion/summaries/{dataset}` | `GET` | Retrieve JSON summaries or pass `?format=tone` for TONE output. |
| `/api/ingestion/metrics` | `GET` | Aggregate counts of quantitative vs qualitative datasets. |

All processed artifacts live in the repository’s `data/` folder:

- `data/raw/` – original uploads (timestamped)
- `data/normalized/` – masked, normalized derivatives
- `data/summaries/` – combined JSON + TONE summaries
- `data/logs/ingest.log` – structured ingestion logs

### Summary Behaviour

- **Schema detection** for tables captures column metadata, null ratios, and numeric ratios.
- **Classification** is automatic: numeric ratio > 0.5 → quantitative, otherwise qualitative.
- **Quantitative** datasets include min / max / mean / std metrics for all numeric fields.
- **Qualitative** datasets trigger an insight extractor (Ollama recommended, heuristic fallback, or EU-hosted OpenAI) to surface 3–5 themes.
- All responses return both JSON bodies and optional TONE strings for LLM-friendly consumption.

### Data Privacy Statement

**REQUIRED BY HACKATHON RULES:**

- **Where does data get processed?** 
  - **Default:** Local server (no external processing)
  - **Optional:** EU cloud (Ollama self-hosted on EU server, or Azure OpenAI EU region)
  
- **Which AI services were used?**
  - **Recommended:** Self-hosted Ollama with Llama 3 / Mistral (runs locally, no data leaves your infrastructure)
  - **Fallback:** Heuristic keyword extraction (no AI, zero privacy risk)
  - **Optional (requires EU deployment):** Azure OpenAI (EU region) - **NOT US-based OpenAI API**
  
- **Does data leave the EU?**
  - **Default:** No - all processing is local
  - **With Ollama:** No - self-hosted, data never leaves your infrastructure
  - **With Azure OpenAI EU:** No - processed in EU region only
  - **⚠️ IMPORTANT:** US-based OpenAI API is NOT used. If OpenAI is needed, only Azure OpenAI (EU region) with proper data protection agreements.
  
- **Monthly cost estimate:** 
  - **Default (heuristic):** €0 - no external services
  - **Ollama (self-hosted):** €0 - runs on your infrastructure
  - **Azure OpenAI EU (if configured):** ~€5-20/month depending on usage (EU region pricing)

**GDPR Compliance:**
- PII masking happens **before** any storage or processing
- All data processing is local-first by default
- No real educational data is sent to external, public, or third-party services
- Audit trails in `data/logs/ingest.log` for compliance tracking

---

## 📈 Analytics & Insights Layer

The analytics layer enriches normalized datasets with derived metrics and qualitative insights.

### Endpoints

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/analytics/summary` | `GET` | Combined numeric metrics (mean, median, std, min, max) across all datasets. |
| `/api/analytics/trends?metric=teacher_satisfaction` | `GET` | Regional trend overview for a numeric metric. |
| `/api/analytics/themes` | `GET` | Aggregated qualitative themes extracted via the configured LLM/heuristic. |
| `/api/analytics/cost-benefit?intervention=X&metric=Y&cost=Z` | `GET` | Calculate ROI and cost-effectiveness for interventions. |
| `/api/analytics/regions` | `GET` | Get all unique regions across datasets for multi-level filtering. |
| `/api/search?q=query&limit=20` | `GET` | Full-text search across all ingested datasets (CSV, markdown, text files). |
| `/api/schools/search?query=Praha` | `GET` | Search schools by name, district, or region. |
| `/api/schools/compare?names=School%20A,School%20B` | `GET` | Compare numeric indicators across schools. |

Append `?format=tone` to any endpoint above to receive a TONE-formatted response.

### Storage Layout

- `data/analytics/metrics/{dataset}.json` – cached numeric metric snapshots per dataset.
- `data/analytics/themes/{dataset}.json` – high-level qualitative themes.

### Sample Responses

```
json
{
  "datasets": ["schools"],
  "metrics": {
    "teacher_satisfaction": {
      "mean": 4.16,
      "median": 4.20,
      "std": 0.28,
      "min": 3.80,
      "max": 4.50
    }
  },
  "generated_at": "2025-11-11T10:45:00.123456"
}
```

```
tone
datasets[1]{schools}
metrics.teacher_satisfaction.mean: 4.16
metrics.teacher_satisfaction.median: 4.20
metrics.teacher_satisfaction.std: 0.28
metrics.teacher_satisfaction.min: 3.80
metrics.teacher_satisfaction.max: 4.50
generated_at: 2025-11-11T10:45:00.123456
```

---

## Deployment

Deployment docs: [deployment.md](./deployment.md).

## Development

General development docs: [development.md](./development.md).

This includes using Docker Compose, custom local domains, `.env` configurations, etc.

