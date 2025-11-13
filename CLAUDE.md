# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**EduScale Engine** - A strategic intelligence platform for scaling educational impact across multiple regions. The system automatically adapts to diverse data formats (CSV, Excel, JSON, audio records), performs AI-powered data understanding, cleaning, validation, and enables cross-regional performance tracking and intervention impact measurement.

**Key Challenge**: Build a data-agnostic platform that scales from 1 pilot region to 500+ regions, each with different data structures, quality levels, and baseline conditions - all while maintaining data security (EU-only), simplicity, and deployability within 48 hours.

## Architecture Overview

### Event-Driven Microservices Architecture

The system follows a serverless, event-driven architecture on Google Cloud Platform (EU region):

```
User PWA → Backend (FastAPI) → Cloud Storage (EU)
                                      ↓ (OBJECT_FINALIZE event)
                                   Eventarc
                                      ↓
                              MIME Decoder (Cloud Run)
                                      ↓
                              Transformer (Cloud Run)
                                      ↓
                               Tabular (Cloud Run)
                                      ↓
                              BigQuery (EU)
```

### Services and Responsibilities

1. **User PWA**: Frontend Progressive Web App for file upload and status display
   - Direct upload to Cloud Storage using resumable upload protocol
   - Real-time progress tracking and processing status updates

2. **Backend (Cloud Run FastAPI)**: API gateway and user interaction handler
   - Creates resumable upload sessions
   - Generates unique file_id for tracking
   - Receives and relays processing status to UI

3. **Cloud Storage (EU)**: Primary object storage with event emission
   - Stores uploaded files and processed text
   - Emits OBJECT_FINALIZE events to trigger processing

4. **Eventarc**: Event routing service
   - Subscribes to Cloud Storage events
   - Reliably delivers events to MIME Decoder with at-least-once guarantee

5. **MIME Decoder (Cloud Run)**: File processing coordinator
   - Detects file types and classifies into categories
   - Routes to appropriate Transformer
   - Does NOT perform transformation itself

6. **Transformer (Cloud Run)**: Multi-format converter to text
   - **text**: Extracts from plain/markdown/html/pdf/docx/rtf
   - **image**: OCR + EXIF metadata extraction
   - **audio**: ASR audio transcription
   - **archive**: Unpacks and processes each file
   - Saves extracted text to Cloud Storage

7. **Tabular (Cloud Run)**: Text-to-structure converter
   - Schema inference using embeddings
   - Maps to domain concepts (dim_*, fact_*, observations)
   - Validates and loads directly to BigQuery
   - Returns INGESTED status with audit trail

8. **BigQuery (EU)**: Final data warehouse
   - Star schema with dimensions and facts
   - Partitioned by date/region
   - Clustered for query performance

## Critical Design Principles

### 1. Data Security & Privacy (HIGHEST PRIORITY)

**GOLDEN RULE**: Provided datasets and derivatives MUST NOT leave the designated environment.

- **EU-only processing**: All services must run in EU regions (europe-west1)
- **No external AI APIs**: Use self-hosted models (Ollama/Llama 3/Mistral) or explicitly EU-configured services
- **Documentation requirement**: Every solution must include Data Privacy Statement in README:
  - Where data is processed (Local / EU cloud / Specific region)
  - AI services used (Self-hosted / Vertex AI EU / None)
  - Does data leave EU? (No / Only aggregated statistics)
  - Monthly cost estimate

### 2. Simplicity & Deployability

**Target**: Production-ready within 48 hours with minimal IT overhead

- Monolithic > Microservices for hackathon scope
- Serverless functions > Always-on services
- Managed services > Custom infrastructure
- Scheduled jobs > Real-time streaming
- REST/CSV > GraphQL
- Max 3 external dependencies
- Max 200€/month operational cost
- No manual server provisioning
- No 24/7 DevOps monitoring

### 3. Data-Agnostic Design

**Core Requirement**: System must automatically adapt to ANY data format without manual configuration

- Use AI for schema understanding and field type detection
- Semantic entity matching using embeddings
- Cross-regional normalization for fair comparisons
- Temporal tracking with baseline capture
- Handle evolving data structures over time

## Common Development Tasks

### Project Structure Requirements

```
/project-root
├── README.md              # With Data Privacy Statement
├── requirements.txt       # All dependencies with versions
├── .env.example          # Template for secrets (NO REAL SECRETS!)
├── docker-compose.yml    # If using containers (recommended)
├── /src                  # Source code
├── /docs
│   ├── ARCHITECTURE.md   # System design
│   └── DATA_FLOW.md      # Visual data flow diagram
└── /tests                # Even basic tests help
```

### Mandatory README Sections

1. One-sentence description
2. Technology stack (languages, libraries, AI models)
3. **Data Privacy Statement** (location, AI services, EU compliance, cost)
4. Prerequisites
5. Setup instructions (copy-paste commands)
6. How to run locally
7. How to deploy to production
8. Known limitations

### Recommended Tech Stack (Privacy-Safe)

**Best Choice - Self-Hosted AI:**
- Ollama with Llama 3/Mistral (runs on laptop)
- sentence-transformers for embeddings
- Data never leaves infrastructure

**Good Choice - Traditional Algorithms:**
- regex, fuzzy matching, statistics
- Fast, free, zero privacy risk

**Acceptable - EU Cloud AI (requires documentation):**
- Google Vertex AI (europe-west1 region)
- Azure OpenAI (westeurope region)
- Must document data protection agreements

**Python Libraries (MIT-licensed):**
- pandas, flask, streamlit, fastapi
- scikit-learn, numpy
- SQLite, PostgreSQL

### Git & Security

**NEVER commit credentials!**

Use `.env` files with `python-dotenv`:

```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("HACKATHON_API_KEY")
```

Add `.env` to `.gitignore`!

### Submission Workflow

1. Fork the main repository
2. Create branch: `git checkout -b your-team-name`
3. Add solution to `srcs/` folder
4. Add completed Solution Canvas PDF to root
5. Add pitch deck to `pitch/` folder
6. Commit and push: `git push origin your-team-name`
7. Open Pull Request to main repository

**Deadline**: 11:59 AM on Day 2

## AI Integration Patterns (Privacy-Safe)

Use AI strategically, not everywhere:

**✅ Schema Understanding**
- LLM interprets column names: "What does 'Pocet_zaku' likely mean?"
- Generates field type suggestions

**✅ Data Quality Detection**
- Identifies patterns: "90% of IDs are 4-digit numeric, but 10% contain letters"
- Suggests corrections based on context

**✅ Entity Matching**
- Uses embeddings: "Skola" = "Škola" = "School name"
- Cross-references data from different sources

**✅ Natural Language Queries**
- Users ask: "Which schools improved in math?"
- AI translates to data operations

**Think**: Good process flow with right AI touchpoints, not maximum AI coverage.

## Critical Features to Include

1. **Adaptive Data Ingestion**
   - Automatic structure interpretation
   - Mapping to common concepts
   - Quality issue flagging

2. **Temporal Tracking**
   - Baseline capture when region joins
   - Before/after comparisons
   - Track changes after interventions

3. **Cross-Regional Comparison**
   - Normalize metrics across formats
   - Handle different contexts (urban/rural, starting points)
   - Identify: "Region B improved 15% faster than Region A at same stage"

4. **Intervention Impact Measurement**
   - Link activities to outcome changes
   - Show: "After teacher training, Region A math scores +12% in 3 months"
   - Answer: "Should we replicate in Region C?"

5. **Network-Wide Intelligence**
   - Aggregate performance across regions
   - Identify best practices from high-performers
   - Detect system-wide trends vs anomalies

6. **Dashboards & Reports**
   - Regional dashboard with filtering
   - Comparison view (side-by-side)
   - Timeline view (monthly/quarterly/yearly)
   - Benchmarking: "How does Region X compare to network average?"

## Example Queries System Should Handle

- "What's the average time for a new region to reach network baseline performance?"
- "Compare Region C's current performance to Region A's performance at 6 months?"
- "Which interventions correlate with fastest improvement across all regions?"
- "Show network-wide trend: Are we closing the quality gap over time?"
- "Which interventions had highest impact in Region A? Apply to Region B?"

## Anti-Patterns to Avoid

❌ Microservices architecture (overkill for 24h hackathon)
❌ Training custom ML models from scratch (use pre-trained)
❌ Building custom database (use SQLite/Google Sheets/BigQuery)
❌ Real-time streaming (batch processing is adequate)
❌ Solutions requiring manual configuration per region
❌ Systems that lose historical context when formats change
❌ Dashboards showing only current state without temporal tracking

## Evaluation Criteria

1. **Feasibility** ⭐⭐⭐ - Production-ready & simplicity (HIGHEST PRIORITY)
2. **Quality** ⭐⭐ - Well-designed solution
3. **Relevance** ⭐⭐ - Technical fit & scalability
4. **Originality** ⭐ - Innovative approach
5. **Transferability** ⭐ - Broader applicability

## Pitching

- 5 minutes presentation + 2 minutes Q&A
- Focus on: what you built, what you learned, potential value
- Demonstrate working solution
- Explain scalability approach

## Resources

- Guidelines: `resources/DigiEduHack_solution_guidelines.pdf`
- Solution Canvas: `resources/Digi_Edu_Hack_Solution_Canvas_2025.pdf`
- Data Samples: [Google Drive](https://drive.google.com/drive/folders/1KVzBOg1ktjgJd16rlyVDPniwRMDWNYYt?usp=sharing)
- DigiEduHack Platform: [Submit Solution](https://digieduhack.com/host/submit-solution?relatedChallenge=106879)

## Notes

- Target: 5,000+ Czech schools
- Scale: 1 pilot region → 10+ regions over 5 years
- Data types: Alphanumeric, voice recordings, diaries, inspection reports
- No real datasets provided - solution must be data-agnostic
- Organization uses Google Workspace and Podio
