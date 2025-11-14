# Data Flow Diagram

## Quick Visual Reference

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         STAGE 1: FILE UPLOAD                           │
└─────────────────────────────────────────────────────────────────────────┘

    [User Browser]
         │
         │ Selects files (PDF, CSV, MP3, etc.)
         ↓
    ┌─────────────────┐
    │  Frontend UI     │  upload-interface.tsx
    │  (Next.js)       │  logs.tsx
    └─────────────────┘
         │
         │ POST /upload (FormData)
         ↓
    ┌─────────────────┐
    │  FastAPI        │  main.py:upload_file()
    │  Backend        │  - Reads file content
    │  :8000          │  - Generates unique filename
    └─────────────────┘  - Uploads to MinIO
         │
         │ minio_client.put_object()
         ↓
    ┌─────────────────┐
    │  MinIO          │  Bucket: "inbox"
    │  Object Storage │  File: {datetime}_{uuid}_{filename}
    └─────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                    STAGE 2: ETL PIPELINE PROCESSING                      │
└─────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐
    │  DuckDB         │  run_pipeline.py
    │  Pipeline       │
    └─────────────────┘
         │
         ├─ Watcher Thread (polls every 30s)
         │     │
         │     │ list_objects("inbox")
         │     ↓
         │  ┌─────────────────┐
         │  │  Work Queue     │
         │  └─────────────────┘
         │
         └─ Worker Thread (processes queue)
               │
               │ 1. Download from inbox
               │ 2. Route by file type
               │ 3. Ai model for transcript
                4. schema unification
               │ 
               ↓
    ┌─────────────────┐
    │  MinIO          │  Bucket: "bronze"
    │  Object Storage │  (parquet)
    └─────────────────┘
         │
         │   1. data cleaning
            2. data validation
         │ 
         ↓
    ┌─────────────────┐
    │  MinIO          │  Bucket: "silver"
    │  Object Storage │  (Parquet)
    └─────────────────┘
         │
         │ modelling transformation to derive
         │ tables and enhance data for consumption
    ┌─────────────────┐
    │  MinIO          │  Bucket: "gold"
    │  Object Storage │  (Parquet files)
    └─────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                    STAGE 3: DASHBOARD DATA LOADING                        │
└─────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐
    │  Streamlit      │  AI_auto_dashboard.py
    │  Dashboard      │
    │  :8501          │
    └─────────────────┘
         │
         │ list_parquet_files("gold")
         ↓
    ┌─────────────────┐
    │  MinIO Client   │  minio_client.py
    │                 │  - Lists .parquet files
    └─────────────────┘
         │
         │ load_parquet_from_minio()
         ↓
    ┌─────────────────┐
    │  Data Loader    │  data_loader.py
    │                 │  - Uses s3fs or MinIO client
    │                 │  - Reads Parquet → DataFrame
    └─────────────────┘
         │
         │ Pandas DataFrame
         ↓
    ┌─────────────────┐
    │  Schema         │  ai_dashboard.py
    │  Analysis       │  - Analyzes columns/types
    │                 │  - Computes statistics
    └─────────────────┘
         │
         │ Schema Summary
         ↓
    ┌─────────────────┐
    │  AI Insight     │  ai_dashboard.py
    │  Generation     │  - LangChain + Ollama
    │                 │  - Qwen VL 4B model
    └─────────────────┘
         │
         │ JSON Insights
         ↓
    ┌─────────────────┐
    │  Visualization  │  AI_auto_dashboard.py
    │  Rendering      │  - Plotly charts
    │                 │  - Bar, Line, Pie, etc.
    └─────────────────┘
         │
         ↓
    [User Dashboard View]


┌─────────────────────────────────────────────────────────────────────────┐
│                      METADATA MANAGEMENT                                 │
└─────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐
    │  SQLite         │  /app/data/metadata.db
    │  Metadata DB    │
    └─────────────────┘
         │
         ├─ admin_users (authentication)
         ├─ schema_metadata (schema definitions)
         └─ pipeline_logs (ETL logs)
         │
         │ FastAPI Endpoints:
         │ - POST /schemas/register
         │ - PUT /schemas/update
         │ - GET /schemas
         │ - GET /logs
         │
         ↓
    [Schema Catalog & Logs]


┌─────────────────────────────────────────────────────────────────────────┐
│                      DATA EXPLORER FLOW                                  │
└─────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐
    │  Data Explorer  │  Data_explorer.py
    │  Page           │
    └─────────────────┘
         │
         │ Loads ALL Parquet files
         │ Combines into single DataFrame
         │
         ├─ Filtering (by source, columns)
         ├─ Schema Viewing (from FastAPI)
         └─ Schema Registration (add columns)
         │
         ↓
    [Interactive Data Exploration]
```

## Component Interaction Map

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend   │──────│   FastAPI    │──────│    MinIO     │
│  (Next.js)   │ HTTP │   Backend    │ S3   │  (Storage)   │
│   :3000      │      │    :8000     │      │   :9000      │
└──────────────┘      └──────────────┘      └──────────────┘
                              │                    │
                              │                    │
                              │                    │
                     ┌─────────┴─────────┐          │
                     │                  │          │
              ┌──────▼──────┐    ┌──────▼──────┐  │
              │   SQLite    │    │   DuckDB    │  │
              │  Metadata   │    │  Pipeline   │──┘
              │     DB      │    │  (ETL)      │
              └─────────────┘    └─────────────┘
                                        │
                                        │
                              ┌─────────▼─────────┐
                              │   Streamlit       │
                              │   Dashboard       │
                              │   :8501           │
                              └───────────────────┘
                                        │
                              ┌─────────▼─────────┐
                              │   Ollama LLM      │
                              │   (AI Insights)   │
                              └───────────────────┘
```

## MinIO Bucket Flow

```
inbox (upload)
  │
  │ [ETL Pipeline]
  ↓
bronze (raw)
  │
  │ [Transformation]
  ↓
gold (parquet) ────► [Dashboard reads from here]
  │
  │
archive (processed)
  │
staging (errors)
```

## Key Data Formats

- **Upload**: Raw files (PDF, CSV, MP3, etc.)
- **Bronze**: Raw files (same format as upload)
- **Gold**: Parquet files (structured, optimized)
- **Dashboard**: Pandas DataFrame (in-memory)
- **Visualization**: Plotly JSON/HTML

