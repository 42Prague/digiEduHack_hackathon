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
- **Local LLM**: Uses Llama 3.2 1B via Ollama (no external API dependencies)
- **Safety-First**: Multi-layer SQL validation (read-only, no DML/DDL)
- **BigQuery Integration**: Direct execution against EduScale data warehouse
- **Simple UI**: Chat interface with result tables and SQL transparency
- **Cloud Run Deployment**: Containerized with Ollama, 8GB memory, 2 vCPUs

## Technology Stack

- **Backend**: FastAPI (existing)
- **LLM Runtime**: Ollama 
- **LLM Model**: Llama 3.2 1B (Meta, open-source)
- **Database**: Google BigQuery
- **UI**: Vanilla HTML/CSS/JavaScript
- **Deployment**: Google Cloud Run (Docker container)

## Architecture Summary

```
User Browser
    ↓ (natural language question)
Chat UI (/nlq/chat)
    ↓ (POST /api/v1/nlq/chat)
FastAPI Chat Endpoint
    ↓                           ↓
LLM SQL Generator          BigQuery Engine
(Ollama/Llama)            (google-cloud-bigquery)
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

- **Estimated Development**: 18-25 hours (2-3 days for single developer)
  - Foundation & Configuration: 2-3 hours
  - Core NLQ Modules: 4-5 hours
  - API Integration: 3-4 hours
  - User Interface: 2-3 hours
  - Ollama Integration: 3-4 hours
  - Testing: 3-4 hours
  - Documentation: 2-3 hours
  - Deployment: 2-3 hours

## Dependencies

### Internal
- BigQuery infrastructure (from `terraform-gcp-infrastructure` spec)
- Configuration system (`eduscale.core.config`)
- Logging system (`eduscale.core.logging`)

### External
- Ollama (system-level, installed in Docker)
- Llama 3.2 1B model (pulled via Ollama)
- Google Cloud BigQuery API
- Google Cloud Run (hosting)

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
- **Local LLM**: No data sent to external APIs (GDPR-compliant)
- **Cost Controls**: LIMIT enforcement + optional bytes_billed cap
- **Data Locality**: All processing within configured GCP region

## Related Specs

- `terraform-gcp-infrastructure`: Provisions BigQuery datasets and tables
- `tabular-ingestion-pipeline`: Populates data queried by NLQ
- `tabular-shared-model-volumes`: Similar Ollama integration pattern for Tabular service

## Questions or Issues

- See **requirements.md** for detailed acceptance criteria
- See **design.md** "Troubleshooting" sections for common issues
- See **tasks.md** "Risk Mitigation" for known challenges and solutions

## Change Log

- **2025-11-14**: Initial specification created
  - Requirements: 15 requirements, 100+ acceptance criteria
  - Design: 7 components, complete implementation details
  - Tasks: 8 phases, 30+ tasks, 18-25 hour estimate

