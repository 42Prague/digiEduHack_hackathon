# Data Flow: Upload to Dashboard

This document maps the complete data flow from file upload to dashboard visualization.

## Architecture Overview

The system uses a **medallion architecture** (Bronze → Silver → Gold) with MinIO object storage and multiple processing components:

- **Frontend** (Next.js): User interface for file uploads
- **FastAPI Backend**: REST API for uploads and metadata management
- **DuckDB Pipeline**: ETL worker that processes files from inbox
- **MinIO**: Object storage with multiple buckets (inbox, bronze, gold, staging, archive)
- **Streamlit Dashboard**: Data visualization and exploration interface
- **SQLite Metadata DB**: Stores schema metadata and pipeline logs

---

## Complete Data Flow

### Stage 1: File Upload

**Component**: Frontend (`frontend/src/components/upload-interface.tsx`)

1. User selects files via drag-and-drop or file picker
2. Files are added to local state (`selectedFiles`)
3. On "Upload" click:
   - Creates `FormData` with all selected files
   - Sends POST request to `${API_URL}/upload` (default: `http://localhost:8000`)
   - Displays upload status (success/error)

**Supported File Types**: PDF, MP3, CSV, and other formats

---

### Stage 2: API Upload Handler

**Component**: FastAPI (`fastapi/src/app/main.py`)

**Endpoint**: `POST /upload`

1. Receives multiple files via `UploadFile` list
2. For each file:
   - Reads file content into memory
   - Generates unique filename: `{datetime}_{uuid}_{original_filename}`
   - Creates `BytesIO` stream from content
   - Uploads to MinIO `inbox` bucket using `minio_client.put_object()`
   - Returns status for each file

**MinIO Configuration**:
- Endpoint: `MINIO_ENDPOINT` or `MINIO_URL` env var (default: `minio:9000`)
- Bucket: `inbox`
- Credentials: `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` (default: `minioadmin`)

**Response Format**:
```json
{
  "results": [
    {"file_name": "2024-01-01T12:00:00_abc123_file.pdf", "status": "ok"},
    ...
  ]
}
```

---

### Stage 3: ETL Pipeline Processing

**Component**: DuckDB Pipeline (`duckDB/app/scripts/run_pipeline.py`)

**Architecture**: Multi-threaded watcher-worker pattern

#### 3.1 Watcher Thread (`enqueue_watcher`)

- Polls `inbox` bucket every 30 seconds (configurable)
- Lists all objects in `inbox` bucket
- For each unseen file:
  - Checks if already processed (exists in `bronze` bucket)
  - If new, adds to `work_queue`
  - Marks as `seen` to avoid duplicate processing

#### 3.2 Worker Thread (`worker`)

- Continuously processes files from `work_queue`
- For each file:
  1. **Download**: Downloads file from `inbox` to `/tmp/{filename}`
  2. **Route**: Calls `file_router()` to determine file type:
     - Tabular: `.csv`, `.xls`, `.xlsx`, `.parquet`, `.json`
     - Documents: `.pdf`, `.docx`, `.txt`, `.doc`, `.md`
     - Images: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`
     - Video: `.mp4`, `.avi`, `.mov`, `.wmv`
  3. **Log**: Logs routing decision to SQLite metadata DB (`pipeline_logs` table)
  4. **Move**: Removes file from `inbox` bucket
  5. **Archive**: File is considered archived (moved from inbox)

**Error Handling**:
- If processing fails, file is moved to `staging` bucket
- Errors are logged to `pipeline_logs` table

**Note**: The current pipeline implementation logs file routing but doesn't explicitly transform files to Parquet format. Files are expected to be manually placed in the `gold` bucket or transformed by external processes.

---

### Stage 4: MinIO Bucket Structure

**Buckets** (created automatically by pipeline):

1. **`inbox`**: Initial upload destination
2. **`bronze`**: Raw data storage (after initial processing)
3. **`gold`**: Processed Parquet files (final destination for dashboard)
4. **`staging`**: Failed/error files
5. **`archive`**: Processed files archive
6. **`input`**: Reserved for future use
7. **`transformation`**: Reserved for future use

**Current Flow**: `inbox` → (processing) → `bronze` → (transformation) → `gold`

---

### Stage 5: Dashboard Data Loading

**Component**: Streamlit Dashboard (`streamlit/src/app/pages/AI_auto_dashboard.py`)

#### 5.1 File Discovery

**Component**: `streamlit/src/app/core/minio_client.py`

1. Connects to MinIO using environment variables:
   - `MINIO_ENDPOINT` (default: `minio:9000`)
   - `MINIO_ACCESS_KEY` (default: `minioadmin`)
   - `MINIO_SECRET_KEY` (default: `minioadmin`)
   - `MINIO_BUCKET` (default: `gold`)

2. Lists all `.parquet` files in `gold` bucket using `list_parquet_files()`
   - Recursively searches bucket
   - Filters by `.parquet` extension
   - Returns sorted list of object names

#### 5.2 Data Loading

**Component**: `streamlit/src/app/core/data_loader.py`

1. **Method 1**: Uses `s3fs` with pandas:
   - Configures S3 storage options with MinIO endpoint
   - Reads Parquet directly: `pd.read_parquet(f"s3://{bucket}/{object_name}", storage_options=...)`

2. **Method 2** (Fallback): Direct MinIO download:
   - Downloads file to memory using MinIO client
   - Reads Parquet from bytes using `pyarrow.parquet`
   - Converts to pandas DataFrame

3. **Sampling**: Optionally samples first N rows (default: 1000 for dashboard)

#### 5.3 Schema Analysis

**Component**: `streamlit/src/app/core/ai_dashboard.py`

1. **Schema Summary** (`generate_schema_summary`):
   - Analyzes DataFrame columns and data types
   - Categorizes columns: `numeric`, `categorical`, `datetime`, `text`
   - Computes statistics per column:
     - Numeric: count, null_count, unique, min, max, mean, std
     - Categorical: count, null_count, unique, top_values
     - Datetime: count, null_count, unique, min, max
   - Samples first 20 rows for context

2. **AI Insight Generation** (`generate_dashboard_insights`):
   - Uses LangChain + Ollama + Qwen VL 4B model
   - Sends schema summary to LLM with system prompt
   - LLM generates up to 10 dashboard insights in JSON format:
     ```json
     {
       "insights": [
         {
           "title": "...",
           "description": "...",
           "chart_type": "bar|line|pie|scatter|histogram|table",
           "x": "column_name or null",
           "y": "column_name or null",
           "group_by": "column_name or null",
           "aggregation": "count|sum|mean|min|max or null",
           "filters": "optional filter description or null"
         }
       ]
     }
     ```
   - Validates insights (checks column names exist, chart types valid)
   - Falls back to basic insights if LLM fails

#### 5.4 Visualization Rendering

**Component**: `streamlit/src/app/pages/AI_auto_dashboard.py`

1. **Insight Cards**: Each insight rendered in expandable card
2. **Chart Rendering** (`render_insight_chart`):
   - **Table**: Displays DataFrame (first 100 rows)
   - **Bar Chart**: `plotly.express.bar()` with optional grouping
   - **Line Chart**: `plotly.express.line()` with markers
   - **Area Chart**: `plotly.express.area()`
   - **Pie Chart**: `plotly.express.pie()`
   - **Scatter Plot**: `plotly.express.scatter()`
   - **Histogram**: `plotly.express.histogram()`

3. **Aggregations**: Applies aggregations (count, sum, mean, min, max) before visualization

4. **Layout**: Responsive grid layout (1-3 columns configurable)

---

### Stage 6: Metadata Management

**Component**: FastAPI + SQLite (`fastapi/src/app/db_utils.py`)

#### 6.1 Schema Registration

**Endpoint**: `POST /schemas/register`

- Stores schema metadata in SQLite `schema_metadata` table
- Format: `{schema_name, columns: {col_name: {type, description}}, description}`
- Used for data catalog and schema discovery

#### 6.2 Schema Updates

**Endpoint**: `PUT /schemas/update`

- Adds/updates columns in existing schema
- Supports overwrite mode

#### 6.3 Schema Listing

**Endpoint**: `GET /schemas`

- Returns all registered schemas with columns and descriptions
- Used by Data Explorer page to display schema information

#### 6.4 Pipeline Logs

**Component**: DuckDB Pipeline (`duckDB/app/scripts/run_pipeline.py`)

- Logs all pipeline operations to SQLite `pipeline_logs` table
- Fields: `ts`, `level`, `component`, `message`, `meta` (JSON)
- Components: `watcher`, `worker`, `router`, `main`

**Endpoint**: `GET /logs?from_date={ISO_DATE}`

- Retrieves logs from metadata DB since specified date

---

## Data Explorer Flow

**Component**: `streamlit/src/app/pages/Data_explorer.py`

1. **Load All Parquet Files**:
   - Lists all `.parquet` files in `gold` bucket
   - Loads each file into pandas DataFrame
   - Adds `_source_file` column to track origin
   - Combines all DataFrames into single DataFrame

2. **Filtering**:
   - Source file filter (multiselect)
   - Numeric column filters (sliders)
   - Categorical column filters (multiselect)

3. **Schema Viewing**:
   - Fetches registered schemas from FastAPI `/schemas` endpoint
   - Displays schema metadata (columns, types, descriptions)

4. **Schema Registration**:
   - Allows users to register new columns via FastAPI `/schemas/update`

---

## Database Components

### SQLite Metadata Database

**Location**: `/app/data/metadata.db` (mounted volume)

**Tables**:

1. **`admin_users`**:
   - Stores admin user credentials (bcrypt hashed passwords)
   - Used for authentication

2. **`schema_metadata`**:
   - Stores schema definitions
   - Columns: `id`, `schema_name`, `columns` (JSON), `description`, `created_at`

3. **`pipeline_logs`**:
   - Stores ETL pipeline logs
   - Columns: `ts`, `level`, `component`, `message`, `meta` (JSON)

### DuckDB Database

**Location**: `/app/data/education.duckdb` (mounted volume)

- Used for querying Parquet files from MinIO
- Configured with S3/MinIO support via `httpfs` extension
- Can load Parquet files directly from `gold` bucket as tables

---

## Environment Variables

### MinIO Configuration
- `MINIO_ENDPOINT` / `MINIO_URL`: MinIO server endpoint (default: `minio:9000`)
- `MINIO_ROOT_USER` / `MINIO_ACCESS_KEY`: Access key (default: `minioadmin`)
- `MINIO_ROOT_PASSWORD` / `MINIO_SECRET_KEY`: Secret key (default: `minioadmin`)
- `MINIO_BUCKET`: Default bucket for dashboard (default: `gold`)
- `MINIO_ENABLED`: Enable MinIO integration (default: `false`)

### API Configuration
- `NEXT_PUBLIC_API_URL`: Frontend API URL (default: `http://localhost:8000`)
- `FASTAPI_URL` / `FASTAPI_URL_EXTERNAL`: FastAPI backend URL

### AI Configuration
- `OLLAMA_URL`: Ollama server URL (default: `http://host.docker.internal:11434`)
- `OLLAMA_MODEL`: Default LLM model
- `DASHBOARD_MODEL`: Model for dashboard insights (default: `qwen2.5-vl:4b`)

### Database Configuration
- `SQLITE_DB_PATH`: Path to SQLite metadata DB (default: `/app/data/metadata.db`)

---

## Docker Services

**docker-compose.yml**:

1. **minio**: MinIO object storage server
2. **duckdb**: ETL pipeline worker (runs `run_pipeline.py`)
3. **fastapi-backend**: FastAPI REST API server
4. **streamlit**: Streamlit dashboard application
5. **frontend**: Next.js frontend application

**Volume Mounts**:
- `./data:/app/data`: Shared data directory (SQLite DB, DuckDB files)
- Source code mounted for hot-reload during development

---

## Current Limitations & Gaps

1. **Missing Transformation Step**: The pipeline moves files from `inbox` → `bronze` but doesn't explicitly transform files to Parquet format in the `gold` bucket. Files must be manually placed in `gold` or transformed by external processes.

2. **No Silver Layer**: The medallion architecture mentions bronze/silver/gold, but there's no explicit silver layer transformation.

3. **File Type Processing**: The router identifies file types but doesn't process them (e.g., PDF extraction, CSV parsing, audio transcription).

4. **Error Recovery**: Failed files go to `staging` but there's no retry mechanism.

---

## Future Enhancements

1. **Automated Parquet Conversion**: Add transformation step to convert CSV/JSON to Parquet
2. **Content Processing**: Add AI services for PDF OCR, audio transcription, image analysis
3. **Silver Layer**: Add data quality checks and normalization
4. **Retry Logic**: Implement retry mechanism for failed files
5. **Data Lineage**: Track data lineage from upload to dashboard

---

## Summary Flow Diagram

```
[User] 
  ↓ (selects files)
[Frontend Upload Interface]
  ↓ (POST /upload)
[FastAPI Backend]
  ↓ (uploads to MinIO)
[MinIO: inbox bucket]
  ↓ (watcher detects)
[DuckDB Pipeline Watcher]
  ↓ (enqueues)
[DuckDB Pipeline Worker]
  ↓ (downloads, routes, logs)
[MinIO: bronze bucket]
  ↓ (manual/external transformation)
[MinIO: gold bucket (Parquet files)]
  ↓ (dashboard loads)
[Streamlit Dashboard]
  ↓ (reads Parquet)
[Pandas DataFrame]
  ↓ (schema analysis)
[AI Dashboard Module]
  ↓ (LLM generates insights)
[Visualizations (Plotly)]
  ↓ (renders)
[User Dashboard View]
```

---

## Key Files Reference

- **Upload**: `frontend/src/components/upload-interface.tsx`
- **API Upload**: `fastapi/src/app/main.py` (line 53-75)
- **ETL Pipeline**: `duckDB/app/scripts/run_pipeline.py`
- **MinIO Client**: `streamlit/src/app/core/minio_client.py`
- **Data Loader**: `streamlit/src/app/core/data_loader.py`
- **AI Dashboard**: `streamlit/src/app/core/ai_dashboard.py`
- **Dashboard Page**: `streamlit/src/app/pages/AI_auto_dashboard.py`
- **Data Explorer**: `streamlit/src/app/pages/Data_explorer.py`
- **Database Utils**: `fastapi/src/app/db_utils.py`
- **Metadata Init**: `fastapi/src/app/db_init.py`

