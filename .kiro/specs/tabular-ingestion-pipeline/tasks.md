# Implementation Plan

## Overview
This implementation plan breaks down the Tabular Ingestion Pipeline into incremental, testable tasks. Each task builds on previous work and focuses on core functionality first, with optional testing tasks marked with *.

## Task List

- [ ] 1. Project setup and configuration
- [x] 1.1 Extend core/config.py with Tabular Service settings
  - Add BIGQUERY_PROJECT_ID, BIGQUERY_DATASET_ID, BIGQUERY_STAGING_DATASET_ID
  - Add CLEAN_LAYER_BASE_PATH, CONCEPT_CATALOG_PATH
  - Add AI models: EMBEDDING_MODEL_NAME="BAAI/bge-m3", LLM_MODEL_NAME="llama3.2:1b", LLM_ENDPOINT="http://localhost:11434", LLM_ENABLED=True
  - Add INGEST_MAX_ROWS, PSEUDONYMIZE_IDS settings
  - Add AI analysis settings: FEEDBACK_ANALYSIS_ENABLED, ENTITY_RESOLUTION_THRESHOLD, FEEDBACK_TARGET_THRESHOLD, MAX_TARGETS_PER_FEEDBACK, ENTITY_CACHE_TTL_SECONDS
  - Add computed properties: bigquery_project, bigquery_staging_dataset
  - _Requirements: Requirement 10, Requirement 12_

- [x] 1.2 Create concepts catalog YAML file
  - Create config/concepts.yaml with 5 table types (ATTENDANCE, ASSESSMENT, FEEDBACK, INTERVENTION, RELATIONSHIP)
  - Define all concepts from class-diagram.puml with multilingual synonyms (EN + CS)
  - Include entity IDs, names, temporal fields, assessment, intervention, experiment, criteria, rule, feedback, analysis, junction fields
  - _Requirements: Requirement 11_

- [x] 1.3 Update requirements.txt with new dependencies
  - Add sentence-transformers>=2.3.0 (for BGE-M3), pandas>=2.0.0, pyarrow>=12.0.0
  - Add pandera>=0.17.0, python-Levenshtein>=0.21.0, rapidfuzz>=3.0.0
  - Add requests>=2.31.0 (for Ollama API calls)
  - Add google-cloud-bigquery>=3.11.0 (if not present)
  - Note: Ollama will be installed via curl script in Dockerfile
  - _Requirements: Dependencies section_

- [ ] 2. Concepts catalog and embeddings module
- [x] 2.1 Implement concepts.py module
  - Create Concept and TableType dataclasses
  - Implement load_concepts_catalog() to parse YAML
  - Implement init_embeddings() for lazy BGE-M3 model loading
  - Implement embed_texts() using sentence-transformers with BGE-M3
  - Cache model at module level for reuse
  - Precompute embeddings for table type anchors and concept synonyms
  - Model returns 1024-dimensional embeddings
  - _Requirements: Requirement 11, Requirement 12_

- [x]* 2.2 Write unit tests for concepts module
  - Test YAML loading with sample concepts_test.yaml
  - Test embedding generation for sample texts
  - Test model caching behavior
  - _Requirements: Requirement 15_

- [ ] 3. YAML frontmatter parsing
- [x] 3.1 Implement frontmatter parsing in pipeline.py
  - Create FrontmatterData dataclass with top-level and nested fields
  - Implement parse_frontmatter() to extract metadata from text files
  - Parse top-level fields: file_id, region_id, text_uri, event_id, file_category
  - Parse nested 'original' section: filename, content_type, size_bytes, bucket, object_path, uploaded_at
  - Parse nested 'extraction' section: method, timestamp, success, duration_ms
  - Parse nested 'content' section: text_length, word_count, character_count
  - Parse nested 'document' section: page_count, sheet_count, slide_count
  - Handle missing nested sections gracefully (return None for missing fields)
  - Return (frontmatter_data, clean_text)
  - _Requirements: Requirement 21_

- [x]* 3.2 Write unit tests for frontmatter parsing
  - Test with sample text files containing YAML frontmatter
  - Test with missing frontmatter
  - Test with malformed YAML
  - _Requirements: Requirement 15_

- [ ] 4. DataFrame loading for tabular data
- [x] 4.1 Implement load_dataframe_from_text() in pipeline.py
  - Load CSV/TSV using pandas.read_csv with detected delimiter
  - Handle UTF-8 and cp1250 encodings
  - Load JSON using pandas.json_normalize or line-by-line for JSONL
  - Strip whitespace from column names and normalize to lower_snake_case
  - Drop completely empty columns
  - Check INGEST_MAX_ROWS limit
  - _Requirements: Requirement 3_

- [x]* 4.2 Write unit tests for DataFrame loading
  - Test with sample CSV, TSV, JSON, JSONL text files
  - Test encoding handling
  - Test row limit enforcement
  - _Requirements: Requirement 15_

- [ ] 5. AI table classification
- [x] 5.1 Implement classifier.py module
  - Implement classify_table() function
  - Extract features from column headers and sample values
  - Generate embeddings for features
  - Compute cosine similarity with table type anchors
  - Apply softmax normalization
  - Return table type with confidence (or FREE_FORM if < 0.4)
  - Log decision with contributing features
  - _Requirements: Requirement 3_

- [x]* 5.2 Write unit tests for table classification
  - Test with synthetic DataFrames for each table type
  - Test low confidence scenarios
  - Test logging output
  - _Requirements: Requirement 15_

- [ ] 6. AI column mapping
- [x] 6.1 Implement mapping.py module
  - Create ColumnMapping dataclass
  - Implement map_columns() function
  - Generate column descriptions with samples
  - Compute embeddings for columns
  - Calculate cosine similarity with concept embeddings
  - Apply type-based score adjustments
  - Assign status: AUTO (>=0.75), LOW_CONFIDENCE (0.55-0.75), UNKNOWN (<0.55)
  - Store top-3 candidates for explainability
  - _Requirements: Requirement 4_

- [x]* 6.2 Write unit tests for column mapping
  - Test with known column names and expected concepts
  - Test type matching logic
  - Test confidence thresholds
  - _Requirements: Requirement 15_

- [ ] 7. Entity resolution module
- [x] 7.1 Implement entity_resolver.py in analysis/ module
  - Create EntityMatch and EntityCache dataclasses
  - Implement normalize_name() for name standardization
  - Implement expand_initials() for initial expansion
  - Implement resolve_entity() with ID exact → Name exact → Fuzzy → Embedding matching
  - Use Levenshtein distance for fuzzy matching (threshold 0.85)
  - Use embedding similarity for semantic matching (threshold 0.75)
  - Implement create_new_entity() to insert into dimension tables
  - Implement load_entity_cache() to query BigQuery dimension tables
  - _Requirements: Requirement 24, Requirement 28_

- [x]* 7.2 Write unit tests for entity resolution
  - Test exact name matches
  - Test fuzzy matches with typos
  - Test initial expansion ("И. Петров" → candidates)
  - Test embedding-based matching
  - Test new entity creation
  - _Requirements: Requirement 15_

- [ ] 8. Data normalization
- [x] 8.1 Implement normalize.py module
  - Implement normalize_dataframe() function
  - Rename columns per AUTO/LOW_CONFIDENCE mappings
  - Cast types: dates (pd.to_datetime), numbers (pd.to_numeric), strings (strip)
  - Add metadata columns: region_id, file_id, ingest_timestamp, source_table_type
  - Normalize school names (remove extra spaces, unify case)
  - Pseudonymize IDs if PSEUDONYMIZE_IDS enabled (SHA256 hash)
  - Preserve original values in metadata for audit
  - _Requirements: Requirement 6_

- [x]* 8.2 Write unit tests for normalization
  - Test column renaming
  - Test type casting
  - Test metadata addition
  - Test pseudonymization
  - _Requirements: Requirement 15_

- [ ] 9. Pandera validation schemas
- [x] 9.1 Implement schemas.py module
  - Define ATTENDANCE_SCHEMA with required columns and constraints
  - Define ASSESSMENT_SCHEMA with required columns and constraints
  - Define FEEDBACK_SCHEMA with required columns and constraints
  - Define INTERVENTION_SCHEMA with required columns and constraints
  - Define RELATIONSHIP_SCHEMA for junction tables
  - Implement validate_normalized_df() function
  - Handle hard failures (missing columns) vs soft failures (invalid values)
  - Write rejects file for soft failures if configured
  - _Requirements: Requirement 5_

- [ ]* 9.2 Write unit tests for validation
  - Test with valid DataFrames for each schema
  - Test with missing required columns
  - Test with invalid values
  - Test rejects file creation
  - _Requirements: Requirement 15_

- [ ] 10. Clean layer storage
- [x] 10.1 Implement clean_layer.py module
  - Create CleanLocation dataclass
  - Implement write_clean_parquet() function
  - Compute deterministic path: {table_type}/region={region_id}/file_id={file_id}.parquet
  - Write to GCS if STORAGE_BACKEND="gcs"
  - Write to local filesystem if STORAGE_BACKEND="local"
  - Create directories if needed for local storage
  - Return CleanLocation with URI and size
  - _Requirements: Requirement 7_

- [ ]* 10.2 Write unit tests for clean layer
  - Test Parquet writing to local filesystem
  - Test path computation
  - Mock GCS operations for cloud storage tests
  - _Requirements: Requirement 15_

- [ ] 11. BigQuery DWH client
- [x] 11.1 Implement dwh/client.py module
  - Create DwhClient class
  - Implement load_parquet_to_staging() to load from GCS to staging table
  - Implement merge_staging_to_core() to MERGE staging → core tables
  - Use explicit schemas for staging tables
  - Partition by date, cluster by region_id
  - Set maximum_bytes_billed for cost control
  - Return LoadJobResult with bytes_processed and cache_hit
  - _Requirements: Requirement 8_

- [ ]* 11.2 Write unit tests for DWH client
  - Mock BigQuery operations
  - Test staging table creation
  - Test MERGE logic
  - Test partitioning and clustering
  - _Requirements: Requirement 15_

- [ ] 12. Ingest runs tracking
- [x] 12.1 Implement runs_store.py module
  - Create IngestRun dataclass
  - Create RunsStore class
  - Implement start_run() to create ingest_runs record in BigQuery
  - Implement update_run_step() to update status and step
  - Implement get_run() to query run by file_id
  - Create ingest_runs table if not exists
  - Partition by created_at, cluster by region_id and status
  - _Requirements: Requirement 20_

- [ ]* 12.2 Write unit tests for runs store
  - Mock BigQuery operations
  - Test run lifecycle (start → update → complete)
  - Test error handling
  - _Requirements: Requirement 15_

- [ ] 13. Free-form text processing
- [x] 13.1 Implement free-form text processing in pipeline.py
  - Detect FREE_FORM content type
  - Extract entity mentions using LLM (llm_client.extract_entities)
  - Apply entity resolution to each mention
  - Compute sentiment_score using LLM (llm_client.analyze_sentiment)
  - Store in observations table with metadata
  - Create observation_targets junction records
  - Preserve audio/PDF metadata from frontmatter
  - _Requirements: Requirement 2_

- [ ]* 13.2 Write unit tests for free-form processing
  - Test entity extraction from sample texts
  - Test sentiment analysis
  - Test observations table storage
  - _Requirements: Requirement 15_

- [ ] 14. Feedback analysis module
- [x] 14.1 Implement feedback_analyzer.py in analysis/ module
  - Create FeedbackTarget dataclass
  - Implement analyze_feedback_batch() function
  - Extract entity mentions from feedback text using LLM
  - Apply entity resolution to mentions
  - Generate embeddings for feedback text using BGE-M3
  - Compute similarity with entity embeddings
  - Combine LLM-based entity extraction and embedding-based matches
  - Create FeedbackTarget records with relevance scores
  - Assign confidence levels (HIGH/MEDIUM/LOW)
  - _Requirements: Requirement 27_

- [ ]* 14.2 Write unit tests for feedback analyzer
  - Test with sample feedback text containing entity mentions
  - Test entity extraction and resolution
  - Test FeedbackTarget creation
  - _Requirements: Requirement 15_

- [ ] 16. LLM client for entity extraction and sentiment
- [x] 16.1 Implement llm_client.py in analysis/ module
  - Create LLMClient class
  - Implement extract_entities() using Ollama API
  - Implement analyze_sentiment() using Ollama API
  - Implement _call_ollama() internal method with error handling
  - Use low temperature (0.1) for deterministic outputs
  - Handle JSON parsing errors gracefully
  - _Requirements: Requirement 12_

- [ ]* 16.2 Write unit tests for LLM client
  - Test entity extraction with sample texts
  - Test sentiment analysis
  - Test error handling
  - _Requirements: Requirement 15_

- [ ] 15. Pipeline orchestration
- [x] 15.1 Implement main pipeline orchestration in pipeline.py
  - Implement process_tabular_text() function
  - Parse frontmatter from text content
  - Detect content type (TABULAR vs FREE_FORM)
  - Route to appropriate processing path
  - For TABULAR: load DataFrame → classify → map → resolve entities → normalize → validate → clean layer → DWH
  - For FREE_FORM: extract entities → resolve → sentiment → observations table
  - Track pipeline steps in ingest_runs
  - Handle errors and update run status to FAILED
  - Return IngestResult with status and metadata
  - _Requirements: Requirement 9_

- [ ]* 15.2 Write integration tests for pipeline
  - Test end-to-end with sample CSV file
  - Test end-to-end with sample PDF text
  - Test error handling at each stage
  - _Requirements: Requirement 15_

- [ ] 16. CloudEvents API endpoint
- [x] 16.1 Implement routes_tabular.py FastAPI endpoints
  - Create POST / endpoint for CloudEvents from Eventarc
  - Parse CloudEvent to extract bucket, object_name, file_id, event_id
  - Filter for text/*.txt pattern
  - Download text content from GCS using StorageClient
  - Call process_tabular_text() with text content
  - Fire-and-forget Backend status update
  - Return 200 to Eventarc (or 400/500 for errors)
  - Log all steps with event_id as correlation_id
  - _Requirements: Requirement 13, Requirement 22_

- [x] 16.2 Implement optional direct API endpoint for testing
  - Create POST /api/v1/tabular/analyze endpoint
  - Accept TabularRequest with text_uri and metadata
  - Download text from Cloud Storage
  - Call process_tabular_text()
  - Return TabularResponse with status and metrics
  - _Requirements: Requirement 14_

- [x] 16.3 Implement health check endpoint
  - Create GET /health endpoint
  - Return service status and model loading status
  - _Requirements: Requirement 14_

- [ ]* 16.4 Write API endpoint tests
  - Test CloudEvent handling with sample events
  - Test direct API endpoint
  - Test error responses
  - _Requirements: Requirement 15_

- [ ] 17. Deployment configuration
- [x] 17.1 Create Dockerfile with Ollama
  - Base image: python:3.11-slim
  - Install Ollama via curl script
  - Install Python dependencies (sentence-transformers, requests, etc.)
  - Pre-download BGE-M3 model
  - Create startup script to start Ollama + pull Llama 3.2 1B + start FastAPI
  - _Requirements: Deployment Notes_

- [x] 17.2 Create Cloud Run configuration for Tabular service
  - Create infra/tabular-config.yaml
  - Configure memory: 4GB minimum (for BGE-M3 + Llama + overhead)
  - Configure CPU: 2 vCPUs
  - Configure max concurrency: 5 (lower due to LLM memory)
  - Set environment variables: EMBEDDING_MODEL_NAME, LLM_MODEL_NAME, LLM_ENDPOINT
  - Configure service account with BigQuery and GCS permissions
  - _Requirements: Deployment Notes_

- [x] 17.3 Create Eventarc trigger for text files
  - Add Eventarc trigger configuration to terraform
  - Filter on text/*.txt pattern in configured bucket
  - Route to Tabular service POST / endpoint
  - _Requirements: Requirement 13_

- [x] 17.4 Update CI/CD workflow
  - Create .github/workflows/deploy-tabular.yml
  - Build Docker image with sentence-transformers
  - Deploy to Cloud Run
  - Run smoke tests after deployment
  - _Requirements: Deployment Notes_

- [ ] 18. Documentation and testing
- [x] 18.1 Create test fixtures
  - Create tests/fixtures/sample_text_csv.txt with frontmatter
  - Create tests/fixtures/sample_text_json.txt with frontmatter
  - Create tests/fixtures/sample_feedback.txt with entity mentions
  - Create tests/fixtures/concepts_test.yaml
  - Create tests/fixtures/mock_entities.json
  - _Requirements: Requirement 15_

- [x] 18.2 Create README for Tabular service
  - Document service purpose and architecture
  - Document configuration options
  - Document API endpoints
  - Document deployment process
  - Include examples of CloudEvents and API requests
  - _Requirements: Documentation_

- [ ]* 18.3 Run full integration test suite
  - Test complete pipeline with real files
  - Verify data in BigQuery
  - Test entity resolution accuracy
  - Test feedback analysis
  - _Requirements: Requirement 15_

## Notes

- Tasks marked with * are optional testing tasks that can be skipped for faster MVP
- Each task should be completed and tested before moving to the next
- Entity resolution is critical and should be thoroughly tested
- **Content Type Detection:** Uses only frontmatter `original_content_type` field - no text structure analysis needed
- **Backend Updates:** Fire-and-forget status updates to inform UI of processing completion
- **Batch Analysis:** Removed from this spec - will be separate module/service
- **AI Models:**
  - BGE-M3 embedding model downloads on first use (~2.2GB)
  - Llama 3.2 1B pulled by Ollama during container startup (~1.3GB)
  - Total model size: ~3.5GB
  - Cold start time: ~20-30 seconds
- BigQuery tables are provisioned by terraform-gcp-infrastructure spec (tasks 11-18)
- Cloud Run configuration: 4GB memory, 2 vCPUs, concurrency 5
