# Requirements Document

## Introduction

The Tabular Ingestion Pipeline is a microservice within the event-driven data processing architecture that transforms extracted text from various file formats into normalized, validated data loaded into a data warehouse (BigQuery). The service receives text URIs from the Transformer service, analyzes the text structure to detect tabular data, and uses AI-powered classification and mapping to automatically understand table types and column semantics, ensuring data quality and consistency across diverse educational data sources.

The Tabular service operates as part of a larger pipeline: User → Backend → Cloud Storage → Eventarc → MIME Decoder → Transformer → **Tabular** → BigQuery, with status flowing back to the user interface.

## Glossary

- **Tabular Service**: The microservice responsible for analyzing text structure and loading structured data to BigQuery
- **Transformer Service**: Upstream service that converts various file formats (images, PDFs, audio) to text and passes text_uri to Tabular
- **MIME Decoder**: Orchestration service that receives Eventarc events and routes to appropriate processors (Transformer, Tabular)
- **Text URI**: Cloud Storage URI pointing to extracted text file (e.g., gs://bucket/text/file_id.txt)
- **Tabular Source**: A data structure containing file metadata (file_id, region_id, text_uri, original content type)
- **Table Type**: Classification category for data tables (ATTENDANCE, ASSESSMENT, FEEDBACK, INTERVENTION, MIXED)
- **Concept Key**: Canonical identifier for a data column (e.g., student_id, test_score, date)
- **Column Mapping**: Association between source column names and canonical concept keys
- **Clean Layer**: Intermediate storage layer containing normalized Parquet files
- **DWH**: Data Warehouse (BigQuery) for final structured data storage
- **Embedding Model**: Sentence-transformer model for semantic text understanding
- **Concepts Catalog**: YAML/JSON configuration defining table types and canonical concepts
- **Ingest Run**: Tracked execution of the pipeline for a specific file
- **Processing Status**: Status information returned to MIME Decoder (INGESTED, FAILED) with metadata

## Requirements

### Requirement 1: Text Structure Analysis

**User Story:** As a data engineer, I want the system to automatically analyze text structure and detect tabular data formats, so that diverse file types can be processed uniformly.

#### Acceptance Criteria

1. WHEN text_uri is provided from Transformer, THE Tabular Service SHALL retrieve the text content from Cloud Storage
2. WHEN text content is retrieved, THE Tabular Service SHALL analyze the structure to determine if it contains tabular data (CSV, TSV, JSON, JSONL, or structured text)
3. WHEN the text contains delimiter-separated values, THE Tabular Service SHALL detect the delimiter (comma, semicolon, tab, pipe)
4. WHEN the text contains JSON structure, THE Tabular Service SHALL determine if it is a single JSON object or line-delimited JSON (JSONL)
5. WHEN the text structure cannot be parsed as tabular data, THE Tabular Service SHALL classify it as free-form text and route to observations table
6. WHEN structure analysis completes, THE Tabular Service SHALL log the detected format and confidence score

### Requirement 2: DataFrame Loading from Text

**User Story:** As a data engineer, I want to load text content into pandas DataFrames, so that I can process structured data extracted from various file formats.

#### Acceptance Criteria

1. WHEN text content is analyzed and format is detected, THE Tabular Service SHALL parse the text into a pandas DataFrame
2. WHEN loading CSV-like text, THE Tabular Service SHALL use pandas.read_csv with detected separator and handle UTF-8 and cp1250 encodings
3. WHEN loading JSON text, THE Tabular Service SHALL use pandas.json_normalize for single objects or line-by-line parsing for JSONL
4. WHEN loading TSV or pipe-delimited text, THE Tabular Service SHALL use the appropriate delimiter for parsing
5. WHEN the DataFrame is loaded, THE Tabular Service SHALL strip whitespace from column names and normalize to lower snake case
6. WHEN the DataFrame exceeds INGEST_MAX_ROWS, THE Tabular Service SHALL raise an error with row count details
7. WHEN columns are completely empty, THE Tabular Service SHALL drop them and log the action
8. WHEN text cannot be parsed into a DataFrame, THE Tabular Service SHALL treat it as unstructured observation data

### Requirement 3: AI-Powered Table Classification

**User Story:** As a data analyst, I want the system to automatically classify table types (ATTENDANCE, ASSESSMENT, etc.), so that data is routed to appropriate schemas and validation rules.

#### Acceptance Criteria

1. WHEN a DataFrame is provided, THE Ingestion Pipeline SHALL extract text features from column headers and sample values
2. WHEN text features are extracted, THE Ingestion Pipeline SHALL generate embeddings using the configured sentence-transformer model
3. WHEN embeddings are generated, THE Ingestion Pipeline SHALL compute similarity scores against table type anchors from the concepts catalog
4. WHEN similarity scores are computed, THE Ingestion Pipeline SHALL select the table type with maximum aggregate similarity
5. WHEN the confidence score is below 0.4, THE Ingestion Pipeline SHALL classify the table as MIXED
6. WHEN classification is complete, THE Ingestion Pipeline SHALL log the chosen type, confidence score, and top contributing features
7. WHEN classification completes, THE Ingestion Pipeline SHALL return both table type and confidence score

### Requirement 4: AI-Powered Column Mapping

**User Story:** As a data engineer, I want source columns automatically mapped to canonical concepts, so that diverse data sources are normalized to a consistent schema.

#### Acceptance Criteria

1. WHEN a DataFrame and table type are provided, THE Ingestion Pipeline SHALL generate text descriptions for each column combining header and sample values
2. WHEN column descriptions are generated, THE Ingestion Pipeline SHALL compute embeddings for each description
3. WHEN column embeddings are computed, THE Ingestion Pipeline SHALL calculate cosine similarity against all concept embeddings from the catalog
4. WHEN the inferred column data type matches the concept's expected type, THE Ingestion Pipeline SHALL increase the similarity score
5. WHEN the similarity score is >= 0.75, THE Ingestion Pipeline SHALL assign status "AUTO" to the mapping
6. WHEN the similarity score is between 0.55 and 0.75, THE Ingestion Pipeline SHALL assign status "LOW_CONFIDENCE"
7. WHEN the similarity score is < 0.55, THE Ingestion Pipeline SHALL set concept_key to None and status to "UNKNOWN"
8. WHEN mapping is complete, THE Ingestion Pipeline SHALL store top-3 candidate concepts for each column for explainability

### Requirement 5: Schema Validation

**User Story:** As a data quality manager, I want normalized data validated against Pandera schemas, so that only quality data enters the warehouse.

#### Acceptance Criteria

1. WHEN a normalized DataFrame is provided with table type, THE Ingestion Pipeline SHALL select the appropriate Pandera schema for that table type
2. WHEN the schema requires non-null columns, THE Ingestion Pipeline SHALL verify all required columns are present and non-null
3. WHEN the schema defines numeric ranges, THE Ingestion Pipeline SHALL validate values fall within acceptable bounds
4. WHEN the schema defines categorical constraints, THE Ingestion Pipeline SHALL verify values match allowed categories
5. WHEN validation fails on required columns, THE Ingestion Pipeline SHALL raise an exception with detailed error messages
6. WHEN validation fails on data values, THE Ingestion Pipeline SHALL collect error messages distinguishing hard failures from soft anomalies
7. WHERE validation produces soft anomalies, THE Ingestion Pipeline SHALL optionally store invalid rows in a separate rejects file

### Requirement 6: Data Normalization

**User Story:** As a data engineer, I want raw data normalized to canonical structure, so that downstream analytics work with consistent column names and types.

#### Acceptance Criteria

1. WHEN column mappings with status "AUTO" or "LOW_CONFIDENCE" are provided, THE Ingestion Pipeline SHALL rename source columns to their concept keys
2. WHEN date columns are identified, THE Ingestion Pipeline SHALL parse values using pandas.to_datetime with common format handling
3. WHEN numeric columns are identified, THE Ingestion Pipeline SHALL convert values to float or int, coercing errors to NaN
4. WHEN categorical columns are identified, THE Ingestion Pipeline SHALL ensure string type and strip whitespace
5. WHEN normalization occurs, THE Ingestion Pipeline SHALL add metadata columns: region_id, file_id, ingest_timestamp, source_table_type
6. WHEN school names are present, THE Ingestion Pipeline SHALL normalize by removing extra spaces and unifying case
7. WHERE PSEUDONYMIZE_IDS setting is enabled, THE Ingestion Pipeline SHALL hash or pseudo-anonymize student identifiers
8. WHEN normalization completes, THE Ingestion Pipeline SHALL invoke Pandera validation on the normalized DataFrame

### Requirement 7: Clean Layer Storage

**User Story:** As a data engineer, I want normalized data written to a clean layer as Parquet files, so that I have an auditable intermediate format before warehouse loading.

#### Acceptance Criteria

1. WHEN a normalized DataFrame is ready for storage, THE Ingestion Pipeline SHALL compute a deterministic path based on table_type, region_id, and file_id
2. WHEN storage backend is "gcs", THE Ingestion Pipeline SHALL write Parquet files to gs://bucket/clean/{table_type}/region={region_id}/file_id={file_id}.parquet
3. WHEN storage backend is "local", THE Ingestion Pipeline SHALL write Parquet files to ./data/clean/{table_type}/region={region_id}/{file_id}.parquet
4. WHEN writing to local storage, THE Ingestion Pipeline SHALL create necessary directories if they do not exist
5. WHEN writing to GCS, THE Ingestion Pipeline SHALL use the google-cloud-storage client for upload operations
6. WHEN the write completes, THE Ingestion Pipeline SHALL return the full URI or path for use in subsequent loading steps
7. WHEN the write completes, THE Ingestion Pipeline SHALL log the location and file size for audit purposes

### Requirement 8: Data Warehouse Loading

**User Story:** As a data analyst, I want normalized data loaded into BigQuery, so that I can query and analyze educational data using SQL.

#### Acceptance Criteria

1. WHEN a clean layer Parquet file is available, THE DWH Client SHALL load data from the GCS URI to a staging table in BIGQUERY_STAGING_DATASET_ID
2. WHEN BIGQUERY_STAGING_DATASET_ID is not configured, THE DWH Client SHALL use BIGQUERY_DATASET_ID for staging tables
3. WHEN loading to staging, THE DWH Client SHALL use explicit schemas aligned with canonical normalized DataFrame structure
4. WHEN staging load completes, THE DWH Client SHALL execute a MERGE operation from staging to core fact/dimension tables
5. WHEN creating or updating core tables, THE DWH Client SHALL partition tables by date and cluster by region_id
6. WHEN executing queries, THE DWH Client SHALL set maximum_bytes_billed to control costs
7. WHEN loading completes, THE DWH Client SHALL return metadata including bytes_processed and cache_hit status

### Requirement 9: Pipeline Orchestration

**User Story:** As a data engineer, I want the complete pipeline orchestrated with status tracking, so that I can monitor progress and debug failures.

#### Acceptance Criteria

1. WHEN a file is submitted for ingestion, THE Ingestion Pipeline SHALL create an ingest run record with status "STARTED" and step "LOAD_RAW"
2. WHEN file format is detected and DataFrame loaded, THE Ingestion Pipeline SHALL update step to "PARSED"
3. WHEN table classification completes, THE Ingestion Pipeline SHALL update step to "CLASSIFIED"
4. WHEN column mapping completes, THE Ingestion Pipeline SHALL update step to "MAPPED"
5. WHEN normalization and validation complete, THE Ingestion Pipeline SHALL update step to "NORMALIZED" then "VALIDATED"
6. WHEN clean layer write completes, THE Ingestion Pipeline SHALL update step to "CLEAN_WRITTEN"
7. WHEN DWH loading completes, THE Ingestion Pipeline SHALL update step to "DWH_LOADED" and status to "DONE"
8. WHEN any error occurs, THE Ingestion Pipeline SHALL update status to "FAILED", log the error with full context, and raise an exception
9. WHEN an error occurs, THE Ingestion Pipeline SHALL record the current step and error message in the ingest run record

### Requirement 10: Configuration Management

**User Story:** As a DevOps engineer, I want all pipeline settings configurable via environment variables, so that I can deploy to different environments without code changes.

#### Acceptance Criteria

1. THE Settings class SHALL include STORAGE_BACKEND with values "gcs" or "local"
2. THE Settings class SHALL include BIGQUERY_DATASET_ID for core tables dataset name
3. THE Settings class SHALL include BIGQUERY_STAGING_DATASET_ID for staging tables, defaulting to BIGQUERY_DATASET_ID if not set
4. THE Settings class SHALL include CLEAN_LAYER_BASE_PATH for clean layer storage location
5. THE Settings class SHALL include CONCEPT_CATALOG_PATH for concepts YAML/JSON file location
6. THE Settings class SHALL include EMBEDDING_MODEL_NAME for sentence-transformer model selection
7. THE Settings class SHALL include INGEST_MAX_ROWS with default value 200000 for row limit enforcement
8. THE Settings class SHALL use BigQuery for ingest run tracking (no separate database or in-memory storage required)
9. THE Settings class SHALL be accessible as a singleton via "from eduscale.core.config import settings"

### Requirement 11: Concepts Catalog

**User Story:** As a data architect, I want a concepts catalog defining table types and canonical columns, so that the AI models have clear targets for classification and mapping.

#### Acceptance Criteria

1. THE Concepts Catalog SHALL define table types: ATTENDANCE, ASSESSMENT, FEEDBACK, INTERVENTION, MIXED
2. THE Concepts Catalog SHALL include anchor phrases for each table type in English and Czech
3. THE Concepts Catalog SHALL define canonical concept keys with descriptions, expected data types, and synonyms
4. THE Concepts Catalog SHALL include concepts: student_id, region_id, school_name, date, test_score, subject, intervention_type, participants_count
5. WHEN the application starts, THE Concepts Loader SHALL load the catalog from CONCEPT_CATALOG_PATH
6. WHEN the catalog is loaded, THE Concepts Loader SHALL precompute embeddings for table type anchors and concept synonyms
7. THE Concepts Loader SHALL provide functions to retrieve table type anchors, concepts, and concept embeddings
8. THE Concepts Loader SHALL cache embeddings to avoid recomputation on each request

### Requirement 12: Embedding Model Management

**User Story:** As an ML engineer, I want the embedding model loaded once and reused, so that inference is fast and resource-efficient.

#### Acceptance Criteria

1. THE Embeddings Module SHALL use sentence-transformers library for text embedding
2. WHEN the application starts or first embedding is requested, THE Embeddings Module SHALL load the model specified by EMBEDDING_MODEL_NAME
3. WHEN the model is loaded, THE Embeddings Module SHALL cache it in a module-level variable
4. THE Embeddings Module SHALL provide an embed_texts function accepting a list of strings and returning numpy array of embeddings
5. WHEN embed_texts is called, THE Embeddings Module SHALL use the cached model instance without reloading
6. THE Embeddings Module SHALL support multilingual models like paraphrase-multilingual-mpnet-base-v2

### Requirement 13: Service Integration

**User Story:** As a system architect, I want the Tabular service to integrate with the event-driven pipeline, so that it processes data automatically and returns status to upstream services.

#### Acceptance Criteria

1. THE Tabular Service SHALL expose endpoint POST /api/v1/tabular/analyze for receiving requests from Transformer
2. WHEN the endpoint receives a request with text_uri and metadata, THE Tabular Service SHALL retrieve the text content from Cloud Storage
3. WHEN metadata includes file_id and region_id, THE Tabular Service SHALL use these for tracking and partitioning
4. WHEN processing completes successfully, THE Tabular Service SHALL return status "INGESTED" with summary including rows loaded, table type, bytes_processed, and cache_hit
5. WHEN processing fails, THE Tabular Service SHALL return status "FAILED" with error details and current processing step
6. THE Tabular Service SHALL support both synchronous HTTP calls from Transformer and direct invocation for testing
7. THE Tabular Service SHALL log all requests and responses for audit purposes

### Requirement 14: Transformer Integration

**User Story:** As a system architect, I want the Tabular service to receive processed text from Transformer, so that the pipeline can handle diverse file formats uniformly.

#### Acceptance Criteria

1. WHEN Transformer completes text extraction, THE Transformer SHALL call the Tabular service with text_uri and metadata
2. WHEN the request includes original_content_type, THE Tabular Service SHALL use it as a hint for structure analysis
3. WHEN the request includes multiple text_uris (from archive unpacking), THE Tabular Service SHALL process each text file independently
4. WHEN Transformer provides extraction_metadata, THE Tabular Service SHALL include it in audit logs
5. WHEN the Tabular service completes processing, THE Tabular Service SHALL return processing status to Transformer
6. THE Tabular Service SHALL handle both single file and batch processing requests from Transformer

### Requirement 15: Event-Driven Flow

**User Story:** As a system architect, I want the Tabular service to participate in the event-driven pipeline, so that processing is scalable, resilient, and observable.

#### Acceptance Criteria

1. WHEN the Tabular service is deployed, THE Tabular Service SHALL run as an independent Cloud Run service
2. WHEN the Tabular service receives a request, THE Tabular Service SHALL process it asynchronously without blocking the caller
3. WHEN processing completes or fails, THE Tabular Service SHALL return status immediately to the Transformer
4. THE Tabular Service SHALL scale independently based on processing load
5. THE Tabular Service SHALL implement health check endpoints for Cloud Run monitoring
6. WHEN the service is unavailable, THE upstream services SHALL retry with exponential backoff
7. THE Tabular Service SHALL emit structured logs for observability and debugging

### Requirement 16: Testing Coverage

**User Story:** As a software engineer, I want comprehensive unit tests, so that I can confidently refactor and extend the pipeline.

#### Acceptance Criteria

1. THE Test Suite SHALL include tests for text structure analysis covering CSV, TSV, JSON, and JSONL text formats
2. THE Test Suite SHALL include tests for load_dataframe_from_text using fixture text files
3. THE Test Suite SHALL include tests for classify_table using synthetic DataFrames representing different table types
4. THE Test Suite SHALL include tests for map_columns verifying correct mapping of common column names to concept keys
5. THE Test Suite SHALL include tests for normalize_df ensuring canonical column names and types are applied
6. THE Test Suite SHALL include tests for DWH loading operations, either using mocks or a test BigQuery dataset
7. THE Test Suite SHALL verify that BigQuery load jobs and merge statements use correct dataset IDs from settings
8. THE Test Suite SHALL include integration tests simulating requests from Transformer with text_uri

### Requirement 17: Privacy and Security

**User Story:** As a compliance officer, I want the pipeline to be privacy-safe and not send data to external services, so that we maintain data sovereignty and GDPR compliance.

#### Acceptance Criteria

1. THE Tabular Service SHALL NOT send any real data to external SaaS APIs like OpenAI or external cloud AI endpoints
2. THE Tabular Service SHALL use only self-hosted ML models within the service infrastructure
3. THE Tabular Service SHALL use sentence-transformers models that run locally without external API calls
4. WHERE student identifiers are processed, THE Tabular Service SHALL support pseudonymization via hashing when PSEUDONYMIZE_IDS is enabled
5. THE Tabular Service SHALL log only metadata and statistics, never raw data values in logs
6. THE Tabular Service SHALL ensure all data processing occurs within the configured GCP region for data locality

### Requirement 18: Determinism and Explainability

**User Story:** As a data scientist, I want the pipeline to be deterministic and explainable, so that I can debug issues and understand classification decisions.

#### Acceptance Criteria

1. THE Tabular Service SHALL produce identical results when processing the same text content multiple times with the same configuration
2. WHEN table classification occurs, THE Tabular Service SHALL log the top contributing column headers or anchor phrases
3. WHEN column mapping occurs, THE Tabular Service SHALL log the mapping decisions with similarity scores
4. THE Tabular Service SHALL store top-3 candidate concepts for each column mapping for human review
5. THE Tabular Service SHALL use deterministic algorithms without random sampling or non-deterministic operations
6. THE Tabular Service SHALL be understandable by a junior developer in less than 30 minutes through clear code structure and documentation

### Requirement 19: Dependency Management

**User Story:** As a legal compliance officer, I want all dependencies to use permissive licenses, so that we avoid legal risks in commercial deployment.

#### Acceptance Criteria

1. THE Tabular Service SHALL use only Python libraries with MIT, Apache 2.0, or BSD licenses
2. THE Tabular Service SHALL NOT use libraries with GPL, AGPL, or other copyleft licenses
3. THE Tabular Service SHALL use standard, well-maintained libraries from the Python ecosystem
4. THE Tabular Service SHALL document all ML model licenses in the concepts catalog or configuration
5. THE Tabular Service SHALL use sentence-transformers models with permissive licenses

### Requirement 20: DataFrame Column Name Preservation

**User Story:** As a data auditor, I want original column names preserved alongside normalized names, so that I can trace data lineage and verify mappings.

#### Acceptance Criteria

1. WHEN column names are normalized to lower snake case, THE Tabular Service SHALL store the original column names in a separate mapping
2. THE Tabular Service SHALL include original column names in audit logs and metadata
3. THE Tabular Service SHALL provide a mapping structure that includes both source_column (original) and concept_key (normalized)
4. WHERE column mappings are stored, THE Tabular Service SHALL preserve the original column name for traceability

### Requirement 21: Advanced Text Parsing

**User Story:** As a data engineer, I want robust text parsing that handles various delimiters and encodings, so that I can ingest data from diverse sources.

#### Acceptance Criteria

1. WHEN parsing delimiter-separated text, THE Tabular Service SHALL use pandas.read_csv with sep=None and engine="python" for automatic separator detection
2. WHEN automatic detection fails, THE Tabular Service SHALL attempt to sniff the first few lines to determine the separator
3. WHEN parsing text, THE Tabular Service SHALL attempt UTF-8 encoding first, then fall back to cp1250 for Central European data
4. WHEN encoding detection fails, THE Tabular Service SHALL log the encoding error and raise a clear exception
5. THE Tabular Service SHALL handle text with comma, semicolon, tab, and pipe separators

### Requirement 22: Classification Algorithm Details

**User Story:** As an ML engineer, I want specific classification algorithm implementation details, so that the system produces reliable and calibrated confidence scores.

#### Acceptance Criteria

1. WHEN extracting text features for classification, THE Tabular Service SHALL sample up to 5 non-null values per column
2. WHEN computing aggregate similarity, THE Tabular Service SHALL use either mean or max cosine similarity between embeddings and anchors
3. WHEN converting scores to confidence, THE Tabular Service SHALL apply softmax normalization over table type scores
4. WHEN multiple table types have similar scores, THE Tabular Service SHALL use softmax to produce calibrated probabilities
5. THE Tabular Service SHALL format text snippets as "column_name: value1; value2; value3" for embedding

### Requirement 23: Column Mapping Scoring Details

**User Story:** As an ML engineer, I want specific scoring rules for column mapping, so that type mismatches are penalized appropriately.

#### Acceptance Criteria

1. WHEN the inferred column dtype is numeric and concept expected_type is number, THE Tabular Service SHALL increase the similarity score by 0.1
2. WHEN the inferred column dtype is datetime and concept expected_type is date, THE Tabular Service SHALL increase the similarity score by 0.1
3. WHEN the inferred column dtype is string and concept expected_type is categorical or string, THE Tabular Service SHALL increase the similarity score by 0.05
4. WHEN the inferred column dtype does not match concept expected_type, THE Tabular Service SHALL decrease the similarity score by 0.15
5. THE Tabular Service SHALL compute base similarity using cosine similarity before applying type-based adjustments

### Requirement 24: Data Warehouse Table Structure

**User Story:** As a data analyst, I want data loaded into specific dimensional and fact tables, so that I can perform star schema analytics.

#### Acceptance Criteria

1. THE DWH Client SHALL load dimension data into tables: dim_region, dim_school, dim_time
2. THE DWH Client SHALL load fact data into tables: fact_assessment, fact_intervention
3. THE DWH Client SHALL load observation data into an observations table for unstructured or mixed data
4. WHEN loading dimension tables, THE DWH Client SHALL use MERGE operations to handle slowly changing dimensions
5. WHEN loading fact tables, THE DWH Client SHALL use INSERT operations or MERGE with deduplication logic
6. THE DWH Client SHALL create staging tables with prefix "stg_" followed by the target table name

### Requirement 25: Ingest Runs Storage Implementation

**User Story:** As a DevOps engineer, I want ingest run tracking persisted in BigQuery, so that I have a durable audit trail for all ingestion operations.

#### Acceptance Criteria

1. THE Runs Store SHALL create and use an ingest_runs table in BigQuery for tracking all ingestion operations
2. THE Runs Store SHALL provide functions: start_run, update_run_step, get_run for managing run lifecycle
3. THE Runs Store SHALL store fields: file_id, region_id, status, step, error_message, created_at, updated_at
4. THE Runs Store SHALL persist run history in BigQuery for audit and monitoring purposes
5. THE Runs Store SHALL use the same BigQuery project and dataset configuration as the main DWH
6. THE Runs Store SHALL create the ingest_runs table automatically if it does not exist with appropriate schema

### Requirement 26: Status Response Format

**User Story:** As a system integrator, I want standardized status responses, so that upstream services can reliably process results.

#### Acceptance Criteria

1. WHEN processing completes successfully, THE Tabular Service SHALL return JSON with status "INGESTED", table_type, rows_loaded, bytes_processed, and cache_hit
2. WHEN processing fails, THE Tabular Service SHALL return JSON with status "FAILED", error_message, and current_step
3. WHEN processing encounters warnings, THE Tabular Service SHALL include warnings array in the response
4. THE Tabular Service SHALL include processing_time_ms in all responses for performance monitoring
5. THE Tabular Service SHALL return HTTP 200 for successful processing and HTTP 500 for failures
6. THE response format SHALL be compatible with the Transformer service expectations
