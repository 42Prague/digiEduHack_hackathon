# Requirements Document

## Introduction

The Tabular Ingestion Pipeline is a microservice within the event-driven data processing architecture that transforms extracted text from various file formats into normalized, validated data loaded into a data warehouse (BigQuery). The service receives text URIs from the Transformer service, analyzes the text structure to detect tabular data, and uses AI-powered classification and mapping to automatically understand table types and column semantics, ensuring data quality and consistency across diverse educational data sources.

The Tabular service operates as part of a larger pipeline: User → Backend → Cloud Storage → Eventarc → MIME Decoder → Transformer → **Tabular** → BigQuery, with status flowing back to the user interface.

## Glossary

- **Tabular Service**: The microservice responsible for analyzing content structure (tabular or free-form) and loading data to BigQuery
- **Transformer Service**: Upstream service that converts various file formats (Excel, PDFs, audio, images) to text and passes text_uri to Tabular
- **MIME Decoder**: Orchestration service that receives Eventarc events and routes to appropriate processors (Transformer, Tabular)
- **Text URI**: Cloud Storage URI pointing to extracted text file (e.g., gs://bucket/text/file_id.txt)
- **Content Type**: Classification of source data: TABULAR (structured tables), FREE_FORM (unstructured text), or MIXED
- **Table Type**: Classification category for tabular data (ATTENDANCE, ASSESSMENT, FEEDBACK, INTERVENTION, RELATIONSHIP)
- **Concept Key**: Canonical identifier for a data column in tabular data (e.g., student_id, test_score, date)
- **Column Mapping**: AI-powered association between source column names and canonical concept keys (only for tabular data)
- **Clean Layer**: Intermediate storage layer containing normalized Parquet files
- **DWH**: Data Warehouse (BigQuery) for final structured data storage
- **Embedding Model**: Sentence-transformer model for semantic text understanding
- **Concepts Catalog**: YAML/JSON configuration defining table types and canonical concepts
- **Ingest Run**: Tracked execution of the pipeline for a specific file
- **Processing Status**: Status information returned to MIME Decoder (INGESTED, FAILED) with metadata
- **Entity Resolution**: AI-driven process that identifies "И. Петров" and "Иван Петров" as the same person by matching against canonical entities in BigQuery dimension tables
- **Junction Table**: Relational table that connects two or more entities (e.g., StudentTeacherSubject links students, teachers, subjects, and regions)
- **Canonical Entity ID**: Unique identifier for an entity in BigQuery dimension tables (dim_teacher, dim_student, dim_region, etc.)
- **Fuzzy Matching**: String similarity algorithm (Levenshtein distance) for matching name variations
- **Embedding-Based Matching**: Semantic similarity using sentence-transformer embeddings for cross-language and synonym matching

## Requirements

### Requirement 1: Content Type Routing

**User Story:** As a data engineer, I want the system to route files to appropriate processing pipeline based on content type, so that diverse file types are handled correctly.

#### Acceptance Criteria

1. WHEN text_uri is provided, THE Tabular Service SHALL retrieve the text content from Cloud Storage
2. WHEN text content starts with YAML frontmatter delimiters (---), THE Tabular Service SHALL parse the frontmatter to extract metadata
3. WHEN frontmatter is parsed, THE Tabular Service SHALL extract top-level fields (file_id, region_id, text_uri, event_id, file_category)
4. WHEN frontmatter is parsed, THE Tabular Service SHALL extract nested 'original' section fields (filename, content_type, size_bytes, bucket, object_path, uploaded_at)
5. WHEN frontmatter is parsed, THE Tabular Service SHALL extract nested 'extraction' section fields (method, timestamp, success, duration_ms)
6. WHEN frontmatter is parsed, THE Tabular Service SHALL extract nested 'content' and 'document' section fields (text_length, word_count, page_count, etc.)
7. WHEN frontmatter parsing completes, THE Tabular Service SHALL separate frontmatter from actual text content
8. WHEN original.content_type indicates structured data (application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, text/csv), THE Tabular Service SHALL route to TABULAR processing path
9. WHEN original.content_type indicates unstructured data (application/pdf, audio/*, text/plain), THE Tabular Service SHALL route to FREE_FORM processing path
10. WHEN original.content_type is application/json, THE Tabular Service SHALL attempt TABULAR parsing first, fallback to FREE_FORM if parsing fails
11. THE Tabular Service SHALL log the routing decision with original.content_type for debugging
12. THE Tabular Service SHALL support two processing paths: TABULAR (column mapping + entity resolution) and FREE_FORM (entity extraction from text)

### Requirement 2: Free-Form Text Processing

**User Story:** As a data engineer, I want free-form text (PDF content, audio transcripts, unstructured feedback) processed and stored with entity extraction, so that all content types are searchable and analyzable.

#### Acceptance Criteria

1. WHEN content is classified as FREE_FORM, THE Tabular Service SHALL skip column mapping and DataFrame loading
2. WHEN free-form text is processed, THE Tabular Service SHALL extract mentioned entities using NER (Named Entity Recognition) or embedding-based detection
3. WHEN entities are detected in free-form text, THE Tabular Service SHALL apply entity resolution to match against canonical entities
4. WHEN free-form text contains feedback-like content, THE Tabular Service SHALL compute sentiment_score using sentiment analysis
5. WHEN free-form text is processed, THE Tabular Service SHALL store it in observations table with metadata: file_id, region_id, text_content, detected_entities, sentiment_score
6. WHEN original content_type is audio/*, THE Tabular Service SHALL preserve audio metadata (duration, confidence, language) from frontmatter
7. WHEN original content_type is application/pdf, THE Tabular Service SHALL preserve document metadata (page_count) from frontmatter
8. THE Tabular Service SHALL support full-text search on observations table for free-form content
9. THE Tabular Service SHALL create observation_targets junction records linking observations to detected entities (similar to FeedbackTarget)
10. WHEN observation_targets are created, THE Tabular Service SHALL apply entity resolution to normalize entity mentions to canonical IDs

### Requirement 3: DataFrame Loading from Text

**User Story:** As a data engineer, I want to load tabular text content into pandas DataFrames, so that I can process structured data extracted from various file formats.

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

1. THE Concepts Catalog SHALL define 5 table types: ATTENDANCE, ASSESSMENT, FEEDBACK, INTERVENTION, RELATIONSHIP
2. THE Concepts Catalog SHALL include anchor phrases for each table type in English and Czech
3. THE Concepts Catalog SHALL define canonical concepts organized by category: entity IDs, entity names, temporal fields, assessment fields, intervention fields, experiment fields, criteria fields, rule fields, feedback fields, analysis fields, junction/relationship fields, and generic fields
4. THE Concepts Catalog SHALL include multilingual synonyms (English and Czech), descriptions, and expected_type for each concept
5. THE Concepts Catalog SHALL include concepts for all junction tables: StudentParent, StudentTeacherSubject, RegionRule, RegionCriteria, RegionExperiment, ExperimentCriteria, FeedbackTarget, AnalysisFeedback, AnalysisImpact
6. THE Concepts Catalog SHALL include concepts for AnalysisResult entity (for ingesting pre-generated analysis data): analysis_id, analysis_timestamp, analysis_status, analysis_report
7. THE Concepts Catalog SHALL include missing temporal and metadata fields: timestamp, source_url, weight, role, relevance_score, impact_score, target_type, target_id
8. WHEN the application starts, THE Concepts Loader SHALL load the catalog from CONCEPT_CATALOG_PATH
9. WHEN the catalog is loaded, THE Concepts Loader SHALL precompute embeddings for table type anchors and concept synonyms
10. THE Concepts Loader SHALL provide functions to retrieve table type anchors, concepts, and concept embeddings
11. THE Concepts Loader SHALL cache embeddings to avoid recomputation on each request

**Note:** Detailed list of concepts is defined in `config/concepts.yaml`

### Requirement 12: AI Models Management

**User Story:** As an ML engineer, I want AI models loaded once and reused, so that inference is fast and resource-efficient.

#### Acceptance Criteria

1. THE Tabular Service SHALL use BGE-M3 (BAAI/bge-m3) for text embeddings
2. THE Tabular Service SHALL use Llama 3.2 1B via Ollama for entity extraction, sentiment analysis, and report generation
3. WHEN the application starts, THE Embeddings Module SHALL load BGE-M3 model specified by EMBEDDING_MODEL_NAME
4. WHEN the application starts, THE Ollama service SHALL start in background and pull Llama 3.2 1B model
5. WHEN the embedding model is loaded, THE Embeddings Module SHALL cache it in a module-level variable
6. THE Embeddings Module SHALL provide an embed_texts function accepting a list of strings and returning numpy array of 1024-dimensional embeddings
7. WHEN embed_texts is called, THE Embeddings Module SHALL use the cached model instance without reloading
8. THE LLM Client SHALL connect to Ollama at LLM_ENDPOINT (default: http://localhost:11434)
9. THE LLM Client SHALL use low temperature (0.1) for deterministic outputs
10. WHEN LLM calls fail, THE LLM Client SHALL log warnings and return safe defaults (empty list for entities, 0.0 for sentiment)

### Requirement 13: Event-Driven Integration

**User Story:** As a system architect, I want the Tabular service to be triggered by Eventarc when text files are created, so that processing is fully event-driven and scalable.

#### Acceptance Criteria

1. THE Tabular Service SHALL expose endpoint POST / for receiving CloudEvents from Eventarc
2. WHEN the endpoint receives a CloudEvent with type "google.cloud.storage.object.v1.finalized", THE Tabular Service SHALL extract bucket and object_name from event data
3. WHEN the object_name matches pattern "text/*.txt", THE Tabular Service SHALL process the text file
4. WHEN the object_name does NOT match "text/*.txt", THE Tabular Service SHALL return 200 and skip processing
5. WHEN CloudEvent is received, THE Tabular Service SHALL extract file_id from object_name (text/{file_id}.txt)
6. WHEN file_id is extracted, THE Tabular Service SHALL download text content from Cloud Storage
7. WHEN processing completes successfully, THE Tabular Service SHALL return 200 to Eventarc
8. WHEN processing fails with retryable error, THE Tabular Service SHALL return 500 to trigger Eventarc retry
9. WHEN processing fails with non-retryable error, THE Tabular Service SHALL return 400 to prevent retry
10. THE Tabular Service SHALL support both CloudEvents from Eventarc and direct API calls for testing
11. THE Tabular Service SHALL log all CloudEvents with correlation IDs for tracing



### Requirement 14: Event-Driven Flow

**User Story:** As a system architect, I want the Tabular service to participate in the event-driven pipeline, so that processing is scalable, resilient, and observable.

#### Acceptance Criteria

1. WHEN the Tabular service is deployed, THE Tabular Service SHALL run as an independent Cloud Run service
2. WHEN the Tabular service receives a CloudEvent, THE Tabular Service SHALL process it asynchronously without blocking Eventarc
3. WHEN processing completes or fails, THE Tabular Service SHALL return status immediately to Eventarc
4. THE Tabular Service SHALL scale independently based on processing load
5. THE Tabular Service SHALL implement health check endpoints for Cloud Run monitoring
6. WHEN the service is unavailable, THE Eventarc SHALL retry with exponential backoff
7. THE Tabular Service SHALL emit structured logs for observability and debugging

### Requirement 15: Testing Coverage

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

### Requirement 16: Privacy and Security

**User Story:** As a compliance officer, I want the pipeline to be privacy-safe and not send data to external services, so that we maintain data sovereignty and GDPR compliance.

#### Acceptance Criteria

1. THE Tabular Service SHALL NOT send any real data to external SaaS APIs like OpenAI or external cloud AI endpoints
2. THE Tabular Service SHALL use only self-hosted ML models within the service infrastructure
3. THE Tabular Service SHALL use sentence-transformers models that run locally without external API calls
4. WHERE student identifiers are processed, THE Tabular Service SHALL support pseudonymization via hashing when PSEUDONYMIZE_IDS is enabled
5. THE Tabular Service SHALL log only metadata and statistics, never raw data values in logs
6. THE Tabular Service SHALL ensure all data processing occurs within the configured GCP region for data locality

### Requirement 17: Determinism and Explainability

**User Story:** As a data scientist, I want the pipeline to be deterministic and explainable, so that I can debug issues and understand classification decisions.

#### Acceptance Criteria

1. THE Tabular Service SHALL produce identical results when processing the same text content multiple times with the same configuration
2. WHEN table classification occurs, THE Tabular Service SHALL log the top contributing column headers or anchor phrases
3. WHEN column mapping occurs, THE Tabular Service SHALL log the mapping decisions with similarity scores
4. THE Tabular Service SHALL store top-3 candidate concepts for each column mapping for human review
5. THE Tabular Service SHALL use deterministic algorithms without random sampling or non-deterministic operations
6. THE Tabular Service SHALL be understandable by a junior developer in less than 30 minutes through clear code structure and documentation

### Requirement 18: Dependency Management

**User Story:** As a legal compliance officer, I want all dependencies to use permissive licenses, so that we avoid legal risks in commercial deployment.

#### Acceptance Criteria

1. THE Tabular Service SHALL use only Python libraries with MIT, Apache 2.0, or BSD licenses
2. THE Tabular Service SHALL NOT use libraries with GPL, AGPL, or other copyleft licenses
3. THE Tabular Service SHALL use standard, well-maintained libraries from the Python ecosystem
4. THE Tabular Service SHALL document all ML model licenses in the concepts catalog or configuration
5. THE Tabular Service SHALL use sentence-transformers models with permissive licenses



### Requirement 19: Data Warehouse Table Structure

**User Story:** As a data analyst, I want data loaded into specific dimensional, fact, and junction tables, so that I can perform star schema analytics with full relational integrity.

#### Acceptance Criteria

1. THE DWH Client SHALL load dimension data into tables: dim_region, dim_student, dim_teacher, dim_parent, dim_subject, dim_school, dim_time, dim_rule, dim_criteria, dim_experiment
2. THE DWH Client SHALL load fact data into tables: fact_assessment, fact_intervention, fact_attendance
3. THE DWH Client SHALL load junction table data into tables: student_parent, student_teacher_subject, region_rule, region_criteria, region_experiment, experiment_criteria, feedback_target, observation_targets, analysis_feedback, analysis_impact
4. THE DWH Client SHALL load observation data into an observations table for free-form text (PDF content, audio transcripts, unstructured feedback)
5. THE DWH Client SHALL load feedback data into a feedback table with polymorphic author references
6. THE DWH Client SHALL load analysis results into an analysis_results table
7. WHEN loading dimension tables, THE DWH Client SHALL use MERGE operations to handle slowly changing dimensions with valid_from and valid_to timestamps
8. WHEN loading fact tables, THE DWH Client SHALL use INSERT operations or MERGE with deduplication logic based on composite keys
9. WHEN loading junction tables, THE DWH Client SHALL use MERGE operations to maintain historical relationships with temporal validity
10. THE DWH Client SHALL create staging tables with prefix "stg_" followed by the target table name

### Requirement 20: Ingest Runs Storage Implementation

**User Story:** As a DevOps engineer, I want ingest run tracking persisted in BigQuery, so that I have a durable audit trail for all ingestion operations.

#### Acceptance Criteria

1. THE Runs Store SHALL create and use an ingest_runs table in BigQuery for tracking all ingestion operations
2. THE Runs Store SHALL provide functions: start_run, update_run_step, get_run for managing run lifecycle
3. THE Runs Store SHALL store fields: file_id, region_id, status, step, error_message, created_at, updated_at
4. THE Runs Store SHALL persist run history in BigQuery for audit and monitoring purposes
5. THE Runs Store SHALL use the same BigQuery project and dataset configuration as the main DWH
6. THE Runs Store SHALL create the ingest_runs table automatically if it does not exist with appropriate schema

### Requirement 21: YAML Frontmatter Parsing

**User Story:** As a data engineer, I want the system to parse YAML frontmatter from text files, so that metadata from Transformer is available for processing.

#### Acceptance Criteria

1. WHEN text content starts with "---\n", THE Tabular Service SHALL identify it as YAML frontmatter
2. WHEN frontmatter is detected, THE Tabular Service SHALL parse YAML content between first and second "---" delimiters
3. WHEN frontmatter is parsed, THE Tabular Service SHALL extract file_id, region_id, text_uri, event_id
4. WHEN frontmatter contains "original" section, THE Tabular Service SHALL extract filename, content_type, size_bytes, bucket, object_path, uploaded_at
5. WHEN frontmatter contains "extraction" section, THE Tabular Service SHALL extract method, timestamp, success, duration_ms
6. WHEN frontmatter contains "content" section, THE Tabular Service SHALL extract text_length, word_count, character_count
7. WHEN frontmatter contains "document" section, THE Tabular Service SHALL extract page_count, sheet_count, slide_count
8. WHEN frontmatter parsing fails, THE Tabular Service SHALL log warning and proceed with text content only
9. WHEN frontmatter is successfully parsed, THE Tabular Service SHALL use extracted metadata for audit logging and tracking

### Requirement 22: CloudEvents Handling

**User Story:** As a system integrator, I want the Tabular service to handle CloudEvents from Eventarc, so that it integrates seamlessly with the event-driven architecture.

#### Acceptance Criteria

1. THE Tabular Service SHALL accept CloudEvents in JSON format with specversion "1.0"
2. WHEN CloudEvent is received, THE Tabular Service SHALL validate required fields: type, source, subject, id, data
3. WHEN CloudEvent data contains bucket and name fields, THE Tabular Service SHALL extract them
4. WHEN CloudEvent id is present, THE Tabular Service SHALL use it as correlation_id for logging
5. WHEN CloudEvent subject matches "objects/text/{file_id}.txt", THE Tabular Service SHALL extract file_id
6. WHEN region_id is needed, THE Tabular Service SHALL extract it from frontmatter (not from path)
7. THE Tabular Service SHALL return HTTP 200 for successful processing
8. THE Tabular Service SHALL return HTTP 400 for invalid CloudEvents (no retry)
9. THE Tabular Service SHALL return HTTP 500 for processing errors (Eventarc will retry)

### Requirement 23: Status Response Format

**User Story:** As a system integrator, I want standardized status responses, so that Backend service can reliably process results.

#### Acceptance Criteria

1. WHEN processing completes successfully, THE Tabular Service SHALL update Backend with status "INGESTED", table_type, rows_loaded, bytes_processed, and cache_hit
2. WHEN processing fails, THE Tabular Service SHALL update Backend with status "FAILED", error_message, and current_step
3. WHEN processing encounters warnings, THE Tabular Service SHALL include warnings array in the Backend update
4. THE Tabular Service SHALL include processing_time_ms in all Backend updates for performance monitoring
5. THE Tabular Service SHALL use fire-and-forget pattern for Backend updates (non-blocking)
6. THE Tabular Service SHALL return HTTP 200 to Eventarc for successful processing and HTTP 500 for retryable failures

### Requirement 24: Entity Resolution During Ingestion

**User Story:** As a data engineer, I want entity names and IDs from diverse data sources automatically matched to canonical entities in the warehouse, so that data from different schools and systems is unified.

#### Acceptance Criteria

1. WHEN entity columns are identified (student_name, teacher_name, parent_name, region_name, subject, school_name), THE Tabular Service SHALL apply entity resolution
2. WHEN entity IDs are present in source data, THE Tabular Service SHALL attempt to match them against canonical IDs in BigQuery dimension tables
3. WHEN entity IDs are missing or unmatched, THE Tabular Service SHALL use name-based entity resolution
4. WHEN entity names are processed, THE Tabular Service SHALL normalize names by removing extra whitespace, unifying case, and standardizing punctuation
5. WHEN normalized names are compared against BigQuery entities, THE Tabular Service SHALL use fuzzy string matching with Levenshtein distance (threshold 0.85)
6. WHEN names contain initials (e.g., "П. Свободова"), THE Tabular Service SHALL expand initials and try all candidate full names
7. WHEN fuzzy matching fails, THE Tabular Service SHALL use embedding-based similarity matching (threshold 0.75)
8. WHEN a match is found with HIGH confidence (>=0.85), THE Tabular Service SHALL replace source ID/name with canonical entity_id
9. WHEN a match is found with MEDIUM confidence (0.70-0.85), THE Tabular Service SHALL flag for manual review but use canonical entity_id
10. WHEN no match is found (confidence <0.70), THE Tabular Service SHALL create a new entity record in the appropriate dimension table
11. THE Tabular Service SHALL preserve original source IDs and names in metadata columns for audit trail
12. THE Tabular Service SHALL log all entity resolution decisions with confidence scores and match methods
13. WHERE ENTITY_RESOLUTION_ENABLED setting is false, THE Tabular Service SHALL skip entity resolution and use source data as-is

### Requirement 25: Junction Table Support

**User Story:** As a data architect, I want the system to recognize and process junction tables that define relationships between entities, so that relational data structures are preserved in the warehouse.

#### Acceptance Criteria

1. THE Concepts Catalog SHALL define RELATIONSHIP as a distinct table type for junction tables
2. WHEN a DataFrame contains columns matching junction table patterns (e.g., student_id + teacher_id + subject_id), THE Tabular Service SHALL classify it as RELATIONSHIP type
3. WHEN RELATIONSHIP tables are detected, THE Tabular Service SHALL validate that all required foreign key columns are present
4. WHEN junction tables contain temporal fields (from_date, to_date), THE Tabular Service SHALL validate date ranges and flag overlapping periods
5. WHEN junction tables contain metadata fields (status, weight, role, relevance_score, impact_score), THE Tabular Service SHALL preserve these fields in normalized output
6. WHEN junction tables contain polymorphic references (target_type, target_id), THE Tabular Service SHALL validate target_type against known entity types
7. THE DWH Client SHALL load junction table data to dedicated junction tables in BigQuery (e.g., student_teacher_subject, region_rule, feedback_target)
8. WHEN loading junction tables, THE DWH Client SHALL enforce referential integrity by validating foreign keys against dimension tables
9. THE DWH Client SHALL use MERGE operations for junction tables to handle updates and maintain historical records

### Requirement 26: Analysis Result Support

**User Story:** As a data scientist, I want the system to ingest AI-generated analysis reports and their relationships to feedback, so that insights and recommendations are stored alongside source data.

#### Acceptance Criteria

1. THE Concepts Catalog SHALL include concepts for AnalysisResult entity: analysis_id, analysis_timestamp, analysis_status, analysis_report
2. WHEN a DataFrame contains analysis result columns, THE Tabular Service SHALL classify it as FEEDBACK or MIXED type depending on content
3. WHEN analysis result data is detected, THE Tabular Service SHALL validate that analysis_id is unique and analysis_report is non-empty
4. WHEN analysis results reference feedback entries, THE Tabular Service SHALL validate feedback_id foreign keys
5. WHEN analysis results specify impact targets, THE Tabular Service SHALL validate target_type and target_id combinations
6. THE DWH Client SHALL load analysis results to an analysis_results table in BigQuery
7. THE DWH Client SHALL load analysis-feedback relationships to analysis_feedback junction table
8. THE DWH Client SHALL load analysis impacts to analysis_impact junction table with polymorphic target references
9. WHEN loading analysis data, THE DWH Client SHALL partition by analysis_timestamp and cluster by analysis_status

### Requirement 27: AI-Powered Feedback Analysis Module

**User Story:** As a data analyst, I want feedback text automatically analyzed to identify mentioned entities and relationships, so that feedback is linked to relevant teachers, experiments, and criteria.

#### Acceptance Criteria

1. WHEN table_type is classified as FEEDBACK, THE Tabular Service SHALL invoke the AI Feedback Analysis module
2. WHEN feedback text is analyzed, THE Analysis Module SHALL use the cached sentence-transformer model to generate text embeddings
3. WHEN feedback embeddings are generated, THE Analysis Module SHALL compute similarity scores against all entity types (teacher, student, region, subject, experiment, criteria, rule)
4. WHEN similarity score exceeds threshold (default 0.65), THE Analysis Module SHALL create FeedbackTarget record with target_type, target_id, and relevance_score
5. WHEN entity names are mentioned in feedback text, THE Analysis Module SHALL apply entity resolution to match against known entities in BigQuery
6. WHEN multiple entity candidates match, THE Analysis Module SHALL select the candidate with highest combined similarity score
7. WHEN FeedbackTarget records are created, THE Analysis Module SHALL store them in feedback_target junction table
8. WHEN feedback analysis completes, THE Analysis Module SHALL log all detected targets with relevance scores for audit
9. WHERE FEEDBACK_ANALYSIS_ENABLED setting is false, THE Analysis Module SHALL skip feedback analysis
10. THE Analysis Module SHALL process feedback analysis within the same transaction as data ingestion

### Requirement 28: Entity Resolution for Feedback Analysis

**User Story:** As a data analyst, I want the system to recognize that "И. Петров" in feedback refers to teacher "Иван Петров" in the database, so that feedback is correctly attributed to entities.

#### Acceptance Criteria

1. WHEN entity names are extracted from feedback text, THE Entity Resolver SHALL normalize names by removing extra whitespace, unifying case, and standardizing punctuation
2. WHEN normalized names are compared against database entities, THE Entity Resolver SHALL use fuzzy string matching with Levenshtein distance
3. WHEN names contain initials (e.g., "И. Петров"), THE Entity Resolver SHALL expand initials to common full names based on region-specific name databases
4. WHEN multiple name candidates exist, THE Entity Resolver SHALL compute similarity scores for all candidates
5. WHEN similarity score is >= 0.85, THE Entity Resolver SHALL consider it a HIGH_CONFIDENCE match
6. WHEN similarity score is between 0.70 and 0.85, THE Entity Resolver SHALL consider it a MEDIUM_CONFIDENCE match
7. WHEN similarity score is < 0.70, THE Entity Resolver SHALL not create entity link
8. WHEN entity IDs are mentioned in feedback text, THE Entity Resolver SHALL use ID as primary match key
9. THE Entity Resolver SHALL query BigQuery dimension tables (dim_teacher, dim_student, dim_region) for entity matching
10. THE Entity Resolver SHALL cache entity lookups within the same ingestion run to avoid repeated queries


