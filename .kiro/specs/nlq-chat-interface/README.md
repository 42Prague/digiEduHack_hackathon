# NL→SQL Chat Interface Specification

## Overview

This specification defines the Natural Language to SQL (NL→SQL) Chat Interface for the EduScale Engine. The feature enables users to query BigQuery analytics data using plain English/Czech questions, with queries automatically translated to safe SQL and executed.

## Specification Files

1. **[requirements.md](./requirements.md)** - Detailed functional and non-functional requirements
   - 15 major requirements with acceptance criteria
   - User stories for each requirement
   - Non-functional requirements (performance, security, privacy)
   - Success criteria and dependencies

2. **[design.md](./design.md)** - Technical design and architecture
   - High-level architecture diagrams
   - Component design (Schema Context, LLM SQL Generator, BigQuery Engine, Chat API, UI)
   - Data flows and sequence diagrams
   - Implementation details with code examples
   - Testing strategy and deployment considerations

3. **[tasks.md](./tasks.md)** - Implementation plan and task breakdown
   - 8 implementation phases
   - 30+ granular tasks with validation criteria
   - Task dependencies and timeline (18-25 hours total)
   - Risk mitigation strategies
   - Rollout plan (local → staging → production)

## Key Features

- **Natural Language Query**: Ask questions in plain text, get SQL results
- **Featherless.ai LLM**: Uses Llama 3.1 8B Instruct via serverless API (faster, simpler than local LLM)
- **Safety-First**: Multi-layer SQL validation (read-only, no DML/DDL)
- **BigQuery Integration**: Direct execution against EduScale data warehouse
- **Simple UI**: Chat interface with result tables and SQL transparency
- **Standard Cloud Run**: No special deployment (2GB memory, 1 vCPU, concurrency=80)

## Technology Stack

- **Backend**: FastAPI (existing)
- **LLM API**: Featherless.ai (serverless, OpenAI-compatible)
- **LLM Model**: Llama 3.1 8B Instruct (Meta, via Featherless.ai)
- **API Client**: OpenAI Python library (already in requirements.txt)
- **Database**: Google BigQuery
- **Embeddings**: sentence-transformers (already in app, NOT used in NLQ MVP)
- **UI**: Vanilla HTML/CSS/JavaScript
- **Deployment**: Google Cloud Run (standard configuration)

**Note:** The application already has embeddings infrastructure (`sentence-transformers/paraphrase-multilingual-mpnet-base-v2`) used for tabular ingestion and entity resolution, but NLQ MVP doesn't need it - the LLM handles all NL understanding. Embeddings could be added later for query caching/suggestions.

## Architecture Summary

```
User Browser
    ↓ (natural language question)
Chat UI (/nlq/chat)
    ↓ (POST /api/v1/nlq/chat)
FastAPI Chat Endpoint
    ↓                           ↓
LLM SQL Generator          BigQuery Engine
(Featherless.ai API)      (google-cloud-bigquery)
    ↓                           ↓
[Generated SQL] ───────→ [Execute Query]
    ↓
[Results + Explanation]
    ↓
Chat UI (render table + SQL)
```

## Getting Started

### For Developers

1. Read **requirements.md** to understand what the feature does
2. Review **design.md** to understand how it works
3. Follow **tasks.md** to implement the feature

### For Product/Demo

- See **requirements.md** Section "Requirement 12: Demo-Ready Example Queries"
- See **tasks.md** Section "Task 7.4: Prepare demo script"
- Key demo queries:
  - "Compare Region A and Region B by average test performance"
  - "Which interventions produced the largest improvement in Region A?"
  - "Show the trend of Region A's math scores over the last year"

## Timeline

- **Estimated Development**: 12-18 hours (1.5-2 days for single developer) - **REDUCED from 18-25h!**
  - Foundation & Configuration: 1-2 hours (minimal config changes)
  - Core NLQ Modules: 3-4 hours (reuse existing LLMClient pattern)
  - API Integration: 3-4 hours
  - User Interface: 2-3 hours
  - Deployment: 1-2 hours (NO Docker changes needed!)
  - Testing: 3-4 hours (simpler mocking)
  - Documentation: 1-2 hours (less to document)
  
**Why faster?** No Ollama setup, no Docker changes, reuses existing infrastructure!

## Dependencies

### Internal
- BigQuery infrastructure (from `terraform-gcp-infrastructure` spec)
- **Existing LLMClient** (`eduscale.tabular.analysis.llm_client`) - REUSED!
- **Existing config** (`FEATHERLESS_*`, `LLM_ENABLED`) - REUSED!
- Logging system (`eduscale.core.logging`)

### External
- **Featherless.ai API** (serverless LLM, no installation needed)
- **OpenAI Python library** (already in requirements.txt)
- Llama 3.1 8B Instruct model (via Featherless.ai API)
- Google Cloud BigQuery API
- Google Cloud Run (standard hosting)

## Success Metrics

MVP is successful when:

1. ✅ Users can query BigQuery using natural language
2. ✅ 3-5 demo queries work reliably (< 5s execution)
3. ✅ System prevents data modification (100% SQL validation)
4. ✅ Performance meets targets (P95 < 15s end-to-end)
5. ✅ Code coverage >= 80%
6. ✅ Feature is demo-ready for pitch
7. ✅ Junior developer can understand system in < 30 min

## Security & Compliance

- **Read-Only**: Only SELECT queries allowed (enforced by validation + IAM)
- **External LLM API**: User questions sent to Featherless.ai (NOT BigQuery results)
- **API Key Security**: Stored in Secret Manager, never logged
- **Cost Controls**: LIMIT enforcement + optional bytes_billed cap
- **Data Locality**: BigQuery processing within configured GCP region
- **Privacy Documentation**: Clear disclosure of external API usage

## Related Specs

- `terraform-gcp-infrastructure`: Provisions BigQuery datasets and tables
- `tabular-ingestion-pipeline`: Populates data queried by NLQ
- `tabular-shared-model-volumes`: Similar Ollama integration pattern for Tabular service

## Questions or Issues

- See **requirements.md** for detailed acceptance criteria
- See **design.md** "Troubleshooting" sections for common issues
- See **tasks.md** "Risk Mitigation" for known challenges and solutions

## Change Log

- **2025-11-14**: Specification updated to match current architecture
  - **CRITICAL**: Changed from Ollama (local) to Featherless.ai API (external)
  - Updated to use actual BigQuery schema from terraform/bigquery.tf
  - Reduced timeline from 18-25h to 12-18h (no Docker work!)
  - Added UPDATES.md with detailed migration guide
  - Requirements: 15 requirements updated for Featherless.ai
  - Design: 7 components updated with OpenAI client integration
  - Tasks: 8 phases, 30+ tasks, 12-18 hour estimate

- **2025-11-14**: Initial specification created (Ollama-based)
  - Requirements: 15 requirements, 100+ acceptance criteria
  - Design: 7 components, complete implementation details
  - Tasks: 8 phases, 30+ tasks, 18-25 hour estimate

