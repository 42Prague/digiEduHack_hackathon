# Design Document

## Overview

The Tabular Service is a microservice within the event-driven data processing architecture that transforms extracted text into normalized, validated data in BigQuery. The service receives text URIs from the Transformer service, analyzes text structure to detect tabular data, and uses sentence-transformer embeddings for semantic understanding of table types and column meanings, ensuring consistent data quality across diverse educational data sources.

The Tabular service operates as part of a larger event-driven pipeline:
**User → Backend → Cloud Storage → Eventarc → MIME Decoder → Transformer → Tabular → BigQuery**

This design focuses on the Tabular service component, which is responsible for the semantic analysis and structured data loading stages.

### Key Design Principles

1. **Modularity**: Each pipeline stage is isolated in its own module with clear interfaces
2. **Determinism**: Same input always produces same output for debugging and reproducibility
3. **Explainability**: All AI decisions are logged with scores and contributing factors
4. **Privacy-First**: All ML models run locally; no external API calls with real data
5. **Fail-Fast**: Errors are caught early with clear messages and full context
6. **Testability**: Each component can be tested independently with synthetic data

## Architecture

### High-Level Flow

#### Full Pipeline Context
```
User Upload → Backend → Cloud Storage
    ↓
Eventarc (OBJECT_FINALIZE event)
    ↓
MIME Decoder (orchestration)
    ↓
Transformer (format conversion)
    ↓
**Tabular Service** (this component)
    ↓
BigQuery → Status back to MIME Decoder → Backend → UI
```

#### Tabular Service Internal Flow
```
Text URI from Transformer
    ↓
[Retrieve Text from GCS] → text content
    ↓
[Text Structure Analysis] → CSV/TSV/JSON/JSONL/free-form
    ↓
[DataFrame Loading] → pandas.DataFrame
    ↓
[AI Table Classification] → ATTENDANCE/ASSESSMENT/FEEDBACK/INTERVENTION/MIXED
    ↓
[AI Column Mapping] → source_column → concept_key mappings
    ↓
[Normalization] → Canonical DataFrame with metadata
    ↓
[Pandera Validation] → Quality checks
    ↓
[Clean Layer Write] → Parquet (GCS)
    ↓
[BigQuery Load] → Staging → MERGE → Core Tables
    ↓
Return Status: INGESTED/FAILED with metadata
```

### Module Structure

```
src/eduscale/
├── core/
│   └── config.py                    # Extended settings
├── models/
│   └── embeddings.py                # Sentence-transformer singleton
├── tabular/
│   ├── text_analyzer.py             # Text structure analysis
│   ├── concepts.py                  # Concepts catalog loader
│   ├── classifier.py                # AI table classification
│   ├── mapping.py                   # AI column-to-concept mapping
│   ├── schemas.py                   # Pandera validation schemas
│   ├── normalize.py                 # Data normalization
│   ├── clean_layer.py               # Parquet writing
│   ├── runs_store.py                # BigQuery ingest runs tracking
│   └── pipeline.py                  # Main orchestration
├── dwh/
│   └── client.py                    # BigQuery DWH operations
└── api/
    └── v1/
        └── routes_tabular.py        # FastAPI endpoints for Tabular service

config/
└── concepts.yaml                    # Table types and concepts catalog

tests/
├── fixtures/
│   ├── sample_text_csv.txt          # Text file with CSV content
│   ├── sample_text_json.txt         # Text file with JSON content
│   └── sample_text_tsv.txt          # Text file with TSV content
└── test_tabular_service.py          # Comprehensive tests
```

## Components and Interfaces

### 1. Configuration (config.py)

**Purpose**: Centralized settings management

**New Settings**:
```python
class Settings(BaseSettings):
    # Existing
    STORAGE_BACKEND: str = "local"  # "gcs" or "local"
    GCS_BUCKET_NAME: str = ""
    GCP_PROJECT_ID: str = ""
    
    # New for ingestion
    BIGQUERY_PROJECT_ID: str = ""  # If not set, defaults to GCP_PROJECT_ID
    BIGQUERY_DATASET_ID: str = "jedouscale_core"
    BIGQUERY_STAGING_DATASET_ID: str = ""  # Defaults to BIGQUERY_DATASET_ID
    CLEAN_LAYER_BASE_PATH: str = "./data/clean"
    CONCEPT_CATALOG_PATH: str = "./config/concepts.yaml"
    EMBEDDING_MODEL_NAME: str = "paraphrase-multilingual-mpnet-base-v2"
    INGEST_MAX_ROWS: int = 200_000
    PSEUDONYMIZE_IDS: bool = False
    
    @property
    def bigquery_project(self) -> str:
        """Get BigQuery project ID, defaulting to GCP_PROJECT_ID."""
        return self.BIGQUERY_PROJECT_ID or self.GCP_PROJECT_ID
    
    @property
    def bigquery_staging_dataset(self) -> str:
        """Get staging dataset, defaulting to main dataset."""
        return self.BIGQUERY_STAGING_DATASET_ID or self.BIGQUERY_DATASET_ID
```


### 2. Text Structure Analysis (text_analyzer.py)

**Purpose**: Analyze text structure and detect tabular data format

**Interface**:
```python
@dataclass
class TextAnalysisResult:
    format: Literal["csv", "tsv", "json", "jsonl", "free_form"]
    confidence: float
    delimiter: str | None
    has_header: bool
    estimated_rows: int

def analyze_text_structure(text_content: str) -> TextAnalysisResult:
    """Analyze text structure and detect format."""
```

**Algorithm**:
1. Sample first 1000 characters for structure detection
2. Check for JSON structure (starts with `{` or `[`)
3. Detect delimiters by counting occurrences of common separators (`,`, `;`, `\t`, `|`)
4. Validate delimiter consistency across lines
5. Detect header row by checking first line characteristics
6. Return format with confidence score
7. If no clear structure, classify as free_form

### 3. Embedding Model (embeddings.py)

**Purpose**: Singleton sentence-transformer model for semantic understanding

**Interface**:
```python
def init_embeddings() -> None:
    """Load and cache the embedding model."""

def embed_texts(texts: list[str]) -> np.ndarray:
    """Generate embeddings for a list of texts."""
```

**Implementation**:
- Module-level cached model instance
- Lazy loading on first use
- Support for multilingual models (paraphrase-multilingual-mpnet-base-v2)

### 4. Concepts Catalog (concepts.py)

**Purpose**: Load and manage canonical concepts and table types

**Data Model**:
```python
@dataclass
class Concept:
    key: str                          # e.g., "student_id"
    description: str
    expected_type: str                # "string", "number", "date", "categorical"
    synonyms: list[str]               # ["Student ID", "StudentID", "ID žáka"]
    embedding: np.ndarray | None = None

@dataclass
class TableType:
    name: str                         # "ATTENDANCE", "ASSESSMENT", etc.
    anchors: list[str]                # Descriptive phrases
    embedding: np.ndarray | None = None

class ConceptsCatalog:
    table_types: list[TableType]
    concepts: list[Concept]
```

**Interface**:
```python
def load_concepts_catalog(path: str) -> ConceptsCatalog:
    """Load catalog from YAML and precompute embeddings."""

def get_table_type_anchors() -> list[TableType]:
    """Get all table types with embeddings."""

def get_concepts() -> list[Concept]:
    """Get all concepts with embeddings."""
```

**How Synonym Matching Works**:
The synonyms in concepts.yaml are NOT used for exact string matching. Instead:
1. All synonyms for each concept are combined into a single text description
2. This combined text is embedded using the sentence-transformer model
3. The embedding captures the semantic meaning of ALL synonyms together
4. When a source column is encountered (e.g., "Známka" or "Student Number"), it's also embedded
5. Cosine similarity between the column embedding and concept embedding determines the match
6. This means the AI can match columns even if they use variations NOT listed in synonyms
7. The synonyms serve as training examples to help the embedding understand the concept's meaning

**Example**: If synonyms include "Student ID" and "ID žáka", the AI can still match:
- "StudentID" (no space)
- "Pupil Identifier" (different wording)
- "Číslo žáka" (Czech variation)
- Any semantically similar text

The more diverse synonyms you provide, the better the AI understands the concept.

**YAML Structure** (concepts.yaml):
```yaml
table_types:
  - name: ATTENDANCE
    anchors:
      - "student attendance records"
      - "presence and absence tracking"
      - "docházka žáků"
      - "attendance tracking"
  
  - name: ASSESSMENT
    anchors:
      - "test scores and grades"
      - "student performance evaluation"
      - "hodnocení žáků"
      - "exam results"
  
  - name: FEEDBACK
    anchors:
      - "student feedback and comments"
      - "teacher observations"
      - "zpětná vazba"
      - "behavioral notes"
  
  - name: INTERVENTION
    anchors:
      - "intervention programs"
      - "support activities"
      - "intervence"
      - "remedial actions"
  
  - name: MIXED
    anchors:
      - "mixed data types"
      - "unstructured information"

concepts:
  # Core Entity Identifiers
  - key: student_id
    description: "Unique student identifier"
    expected_type: string
    synonyms:
      - "Student ID"
      - "StudentID"
      - "ID žáka"
      - "Student Number"
      - "Pupil ID"
  
  - key: teacher_id
    description: "Unique teacher identifier"
    expected_type: string
    synonyms:
      - "Teacher ID"
      - "TeacherID"
      - "ID učitele"
      - "Instructor ID"
      - "Educator ID"
  
  - key: parent_id
    description: "Unique parent/guardian identifier"
    expected_type: string
    synonyms:
      - "Parent ID"
      - "ParentID"
      - "ID rodiče"
      - "Guardian ID"
  
  - key: region_id
    description: "Geographic region identifier"
    expected_type: string
    synonyms:
      - "Region"
      - "Region ID"
      - "Oblast"
      - "District"
      - "District ID"
  
  # Entity Names
  - key: student_name
    description: "Student full name"
    expected_type: string
    synonyms:
      - "Student Name"
      - "Student"
      - "Jméno žáka"
      - "Pupil Name"
      - "Name"
  
  - key: teacher_name
    description: "Teacher full name"
    expected_type: string
    synonyms:
      - "Teacher Name"
      - "Teacher"
      - "Jméno učitele"
      - "Instructor Name"
      - "Educator"
  
  - key: parent_name
    description: "Parent/guardian full name"
    expected_type: string
    synonyms:
      - "Parent Name"
      - "Parent"
      - "Jméno rodiče"
      - "Guardian Name"
  
  - key: school_name
    description: "Name of the school"
    expected_type: string
    synonyms:
      - "School"
      - "School Name"
      - "Škola"
      - "Institution"
  
  - key: region_name
    description: "Name of the region"
    expected_type: string
    synonyms:
      - "Region Name"
      - "Region"
      - "Název oblasti"
      - "District Name"
  
  # Temporal Fields
  - key: date
    description: "Date of the event or record"
    expected_type: date
    synonyms:
      - "Date"
      - "Datum"
      - "Event Date"
      - "Record Date"
      - "Timestamp"
  
  - key: from_date
    description: "Start date of a period or relationship"
    expected_type: date
    synonyms:
      - "From"
      - "From Date"
      - "Start Date"
      - "Od"
      - "Začátek"
  
  - key: to_date
    description: "End date of a period or relationship"
    expected_type: date
    synonyms:
      - "To"
      - "To Date"
      - "End Date"
      - "Do"
      - "Konec"
  
  # Assessment Fields
  - key: test_score
    description: "Numeric test or assessment score"
    expected_type: number
    synonyms:
      - "Score"
      - "Test Score"
      - "Grade"
      - "Hodnocení"
      - "Známka"
      - "Points"
      - "Mark"
  
  - key: subject
    description: "Academic subject"
    expected_type: categorical
    synonyms:
      - "Subject"
      - "Předmět"
      - "Course"
      - "Class"
      - "Subject Name"
  
  - key: subject_id
    description: "Unique subject identifier"
    expected_type: string
    synonyms:
      - "Subject ID"
      - "SubjectID"
      - "ID předmětu"
      - "Course ID"
  
  # Intervention Fields
  - key: intervention_type
    description: "Type of intervention or support"
    expected_type: categorical
    synonyms:
      - "Intervention"
      - "Intervention Type"
      - "Typ intervence"
      - "Support Type"
      - "Program"
      - "Program Type"
  
  - key: intervention_id
    description: "Unique intervention identifier"
    expected_type: string
    synonyms:
      - "Intervention ID"
      - "InterventionID"
      - "ID intervence"
      - "Program ID"
  
  - key: participants_count
    description: "Number of participants"
    expected_type: number
    synonyms:
      - "Participants"
      - "Count"
      - "Počet účastníků"
      - "Number of Students"
      - "Attendance Count"
      - "Participant Count"
  
  # Experiment Fields
  - key: experiment_id
    description: "Unique experiment identifier"
    expected_type: string
    synonyms:
      - "Experiment ID"
      - "ExperimentID"
      - "ID experimentu"
      - "Trial ID"
  
  - key: experiment_name
    description: "Name of the experiment"
    expected_type: string
    synonyms:
      - "Experiment"
      - "Experiment Name"
      - "Název experimentu"
      - "Trial Name"
  
  - key: experiment_status
    description: "Status of the experiment"
    expected_type: categorical
    synonyms:
      - "Status"
      - "Experiment Status"
      - "Stav experimentu"
      - "State"
  
  # Criteria Fields
  - key: criteria_id
    description: "Unique criteria identifier"
    expected_type: string
    synonyms:
      - "Criteria ID"
      - "CriteriaID"
      - "ID kritéria"
      - "Metric ID"
  
  - key: criteria_name
    description: "Name of the criteria"
    expected_type: string
    synonyms:
      - "Criteria"
      - "Criteria Name"
      - "Název kritéria"
      - "Metric Name"
      - "KPI"
  
  - key: target_value
    description: "Target value for a criteria"
    expected_type: number
    synonyms:
      - "Target"
      - "Target Value"
      - "Cílová hodnota"
      - "Goal"
      - "Objective"
  
  - key: baseline_value
    description: "Baseline value for a criteria"
    expected_type: number
    synonyms:
      - "Baseline"
      - "Baseline Value"
      - "Výchozí hodnota"
      - "Starting Value"
  
  # Rule Fields
  - key: rule_id
    description: "Unique rule identifier"
    expected_type: string
    synonyms:
      - "Rule ID"
      - "RuleID"
      - "ID pravidla"
      - "Policy ID"
  
  - key: rule_title
    description: "Title of the rule"
    expected_type: string
    synonyms:
      - "Rule"
      - "Rule Title"
      - "Název pravidla"
      - "Policy Name"
      - "Regulation"
  
  - key: rule_type
    description: "Type of rule"
    expected_type: categorical
    synonyms:
      - "Rule Type"
      - "Type"
      - "Typ pravidla"
      - "Policy Type"
      - "Category"
  
  # Feedback Fields
  - key: feedback_id
    description: "Unique feedback identifier"
    expected_type: string
    synonyms:
      - "Feedback ID"
      - "FeedbackID"
      - "ID zpětné vazby"
      - "Comment ID"
  
  - key: feedback_text
    description: "Text content of feedback"
    expected_type: string
    synonyms:
      - "Feedback"
      - "Feedback Text"
      - "Text zpětné vazby"
      - "Comment"
      - "Comments"
      - "Notes"
  
  - key: sentiment_score
    description: "Sentiment score of feedback"
    expected_type: number
    synonyms:
      - "Sentiment"
      - "Sentiment Score"
      - "Skóre sentimentu"
      - "Rating"
      - "Mood Score"
  
  - key: feedback_category
    description: "Category of feedback"
    expected_type: categorical
    synonyms:
      - "Category"
      - "Feedback Category"
      - "Kategorie zpětné vazby"
      - "Type"
      - "Classification"
  
  - key: author_id
    description: "ID of feedback author"
    expected_type: string
    synonyms:
      - "Author ID"
      - "AuthorID"
      - "ID autora"
      - "Submitted By"
      - "User ID"
  
  - key: author_type
    description: "Type of feedback author (student/teacher/parent)"
    expected_type: categorical
    synonyms:
      - "Author Type"
      - "Typ autora"
      - "Role"
      - "User Type"
      - "Submitter Type"
  
  # Generic Description Field
  - key: description
    description: "General description or notes"
    expected_type: string
    synonyms:
      - "Description"
      - "Popis"
      - "Notes"
      - "Details"
      - "Information"
      - "Poznámky"
```


### 5. DataFrame Loading from Text (pipeline.py)

**Purpose**: Load text content into pandas DataFrames

**Interface**:
```python
@dataclass
class TabularSource:
    file_id: str
    region_id: str
    text_uri: str
    original_content_type: str | None
    extraction_metadata: dict | None

def load_dataframe_from_text(
    text_content: str, 
    analysis: TextAnalysisResult
) -> pd.DataFrame:
    """Load text into DataFrame based on detected structure."""
```

**Algorithm**:
1. Retrieve text content from Cloud Storage using text_uri
2. Analyze structure using text_analyzer.analyze_text_structure()
3. Load based on detected format:
   - CSV/TSV: `pd.read_csv(sep=delimiter, engine="python")` with UTF-8 encoding first, fallback to cp1250
   - JSON: `pd.json_normalize()` for single JSON, line-by-line for JSONL
   - free_form: Create single-column DataFrame with text as observation
4. Strip whitespace from column names
5. Store original column names in metadata
6. Normalize column names to lower_snake_case
7. Drop completely empty columns and log
8. Check INGEST_MAX_ROWS limit, raise error if exceeded
9. Return DataFrame with metadata


### 6. AI Table Classification (classifier.py)

**Purpose**: Classify table type using embeddings

**Interface**:
```python
def classify_table(df: pd.DataFrame, catalog: ConceptsCatalog) -> tuple[str, float]:
    """Classify table type and return (type, confidence)."""
```

**Algorithm**:
1. Extract features: column headers + up to 5 non-null sample values per column
2. Format text snippets as "column_name: value1; value2; value3" for embedding
3. Generate embeddings for all feature texts
4. Compute cosine similarity with table type anchors (use mean or max)
5. Apply softmax normalization over table type scores for calibrated probabilities
6. Return table type with highest score (or "MIXED" if confidence < 0.4)
7. Log decision with top contributing column headers and anchor phrases

### 7. AI Column Mapping (mapping.py)

**Purpose**: Map source columns to canonical concepts

**Data Model**:
```python
@dataclass
class ColumnMapping:
    source_column: str
    concept_key: str | None
    score: float
    status: Literal["AUTO", "LOW_CONFIDENCE", "UNKNOWN"]
    candidates: list[tuple[str, float]]
```

**Algorithm**:
1. For each column: build description with samples, generate embedding, infer dtype
2. Compute cosine similarity with all concept embeddings
3. Apply type-based score adjustments:
   - +0.1 if numeric column and concept type is "number"
   - +0.1 if datetime column and concept type is "date"
   - +0.05 if string column and concept type is "string" or "categorical"
   - -0.15 if types don't match
4. Assign status: AUTO (>=0.75), LOW_CONFIDENCE (0.55-0.75), UNKNOWN (<0.55)
5. Store top-3 candidates, log all mappings

### 8. Pandera Validation (schemas.py)

**Purpose**: Define and enforce data quality schemas per table type

**Schemas**: ATTENDANCE_SCHEMA, ASSESSMENT_SCHEMA, FEEDBACK_SCHEMA, INTERVENTION_SCHEMA, MIXED_SCHEMA

**Interface**:
```python
def validate_normalized_df(df: pd.DataFrame, table_type: str) -> pd.DataFrame:
    """Validate DataFrame against schema, raise on hard failures."""
```

**Error Handling**:
- **Hard failures** (missing required columns): Raise exception immediately with detailed error messages
- **Soft failures** (invalid values in rows): Log warnings, optionally write rejects file
- **Rejects file**: Invalid rows written to `{clean_layer_base}/rejects/{table_type}/region={region_id}/{file_id}_rejects.parquet`
- Return validated DataFrame (with invalid rows removed if soft failures occurred)

### 9. Data Normalization (normalize.py)

**Purpose**: Transform raw data to canonical structure

**Interface**:
```python
def normalize_dataframe(
    df_raw: pd.DataFrame,
    table_type: str,
    mappings: list[ColumnMapping],
    region_id: str,
    file_id: str
) -> pd.DataFrame:
    """Normalize DataFrame to canonical structure."""
```

**Steps**:
1. Store original column names in mapping structure for audit trail
2. Rename columns per mappings (AUTO/LOW_CONFIDENCE only)
3. Cast types: dates (pd.to_datetime), numbers (pd.to_numeric), strings (strip)
4. Add metadata: region_id, file_id, ingest_timestamp, source_table_type
5. Clean data: normalize school names, pseudonymize IDs if enabled (SHA256 hash)
6. Validate with Pandera schema

### 10. Clean Layer Storage (clean_layer.py)

**Purpose**: Write normalized data as Parquet

**Interface**:
```python
@dataclass
class CleanLocation:
    uri: str
    size_bytes: int

def write_clean_parquet(df_norm: pd.DataFrame, target_info: CleanTargetInfo) -> CleanLocation:
    """Write DataFrame to Parquet in clean layer."""
```

**Path Structure**:
- GCS: `gs://{bucket}/clean/{table_type}/region={region_id}/file_id={file_id}.parquet`
- Local: `{base_path}/clean/{table_type}/region={region_id}/{file_id}.parquet`

### 11. BigQuery DWH Client (dwh/client.py)

**Purpose**: Load data into BigQuery data warehouse

**Interface**:
```python
class DwhClient:
    def load_parquet_to_staging(
        self, table_type: str, clean_location: CleanLocation, context: IngestContext
    ) -> LoadJobResult:
        """Load Parquet from GCS to staging table."""
    
    def merge_staging_to_core(
        self, table_type: str, context: IngestContext
    ) -> MergeResult:
        """MERGE staging data into core tables."""
```

**Table Structure**:
- **Staging**: `stg_attendance`, `stg_assessment`, `stg_feedback`, `stg_intervention`
- **Dimensions**: `dim_region`, `dim_school`, `dim_time`
- **Facts**: `fact_assessment`, `fact_intervention`
- **Observations**: `observations` (for MIXED data)

**Features**:
- Partition by date, cluster by region_id
- Use maximum_bytes_billed for cost control
- Return bytes_processed and cache_hit metadata

### 12. Ingest Runs Tracking (runs_store.py)

**Purpose**: Track ingestion pipeline execution in BigQuery

**Data Model**:
```python
@dataclass
class IngestRun:
    file_id: str
    region_id: str
    status: str  # STARTED, DONE, FAILED
    step: str    # LOAD_RAW, PARSED, CLASSIFIED, MAPPED, etc.
    error_message: str | None
    created_at: datetime
    updated_at: datetime
```

**Interface**:
```python
class RunsStore:
    def start_run(self, file_id: str, region_id: str) -> IngestRun
    def update_run_step(self, file_id: str, step: str, status: str, error_message: str | None)
    def get_run(self, file_id: str) -> IngestRun | None
```

**BigQuery Table**: `ingest_runs` partitioned by created_at, clustered by region_id and status

### 13. Pipeline Orchestration (pipeline.py)

**Purpose**: Coordinate all pipeline stages

**Interface**:
```python
def process_tabular_file(file_id: str, region_id: str, storage_meta: dict) -> IngestResult:
    """Execute complete ingestion pipeline."""
```

**Pipeline Steps**:
1. LOAD_RAW: Initialize run
2. PARSED: Detect format and load DataFrame
3. CLASSIFIED: AI table classification
4. MAPPED: AI column mapping
5. NORMALIZED: Transform to canonical structure
6. VALIDATED: Pandera validation
7. CLEAN_WRITTEN: Write Parquet to clean layer
8. DWH_LOADED: Load to BigQuery staging and merge to core
9. DONE: Complete successfully

**Error Handling**: Catch exceptions, log with context, update run status to FAILED, re-raise

### 14. FastAPI Integration (api/v1/routes_tabular.py)

**Purpose**: REST API for receiving requests from Transformer

**Endpoint**:
```python
@dataclass
class TabularRequest:
    file_id: str
    region_id: str
    text_uri: str
    original_content_type: str | None
    extraction_metadata: dict | None

@dataclass
class TabularResponse:
    status: Literal["INGESTED", "FAILED"]
    table_type: str | None
    rows_loaded: int | None
    bytes_processed: int | None
    cache_hit: bool | None
    error_message: str | None
    warnings: list[str]
    processing_time_ms: int

@router.post("/api/v1/tabular/analyze")
async def analyze_tabular(request: TabularRequest) -> TabularResponse:
    """Analyze text structure and load to BigQuery."""
```

**Flow**:
1. Receive request from Transformer with text_uri and metadata
2. Retrieve text content from Cloud Storage
3. Call process_tabular_text() with text content and metadata
4. Return response with status, table_type, rows_loaded, and BigQuery metrics
5. Include warnings array for non-fatal issues
6. Log request and response for audit trail

## Service Integration

### Transformer → Tabular Flow

1. **Transformer completes text extraction**
   - Saves extracted text to Cloud Storage (gs://bucket/text/file_id.txt)
   - Prepares metadata (file_id, region_id, original_content_type)

2. **Transformer calls Tabular service**
   - POST /api/v1/tabular/analyze
   - Payload: TabularRequest with text_uri and metadata

3. **Tabular processes request**
   - Retrieves text from Cloud Storage
   - Analyzes structure and loads to BigQuery
   - Returns TabularResponse with status and metrics

4. **Transformer receives response**
   - Forwards status to MIME Decoder
   - MIME Decoder updates Backend
   - Backend updates UI

### Event-Driven Characteristics

- **Asynchronous**: Tabular processes requests without blocking Transformer
- **Scalable**: Cloud Run scales Tabular service based on load
- **Resilient**: Transformer retries on failures with exponential backoff
- **Observable**: Structured logs and metrics for monitoring

## Data Models

### Core Data Structures

```python
@dataclass
class IngestContext:
    file_id: str
    region_id: str
    table_type: str
    rows_count: int
    text_uri: str

@dataclass
class IngestResult:
    file_id: str
    status: Literal["INGESTED", "FAILED"]
    table_type: str | None
    rows_loaded: int | None
    clean_location: str | None
    bytes_processed: int | None
    cache_hit: bool | None
    error_message: str | None
    warnings: list[str]
    processing_time_ms: int
```

## Error Handling

### Error Categories

1. **Format Errors**: Unsupported file format, corrupted files
2. **Size Errors**: Exceeds INGEST_MAX_ROWS limit
3. **Classification Errors**: Unable to determine table type with confidence
4. **Mapping Errors**: Too many UNKNOWN column mappings
5. **Validation Errors**: Schema validation failures (hard/soft)
6. **Storage Errors**: GCS/local write failures
7. **DWH Errors**: BigQuery load/merge failures

### Error Response

All errors update ingest_runs with:
- status = "FAILED"
- step = current pipeline step
- error_message = exception details

Errors are logged with full context and re-raised for HTTP error responses.

## Testing Strategy

### Unit Tests

1. **filetypes.py**: Test detection for CSV, XLSX, JSON, JSONL with various extensions and MIME types
2. **classifier.py**: Test classification with synthetic DataFrames for each table type
3. **mapping.py**: Test column mapping with known column names and expected concepts
4. **normalize.py**: Test type casting, metadata addition, data cleaning
5. **schemas.py**: Test Pandera validation with valid and invalid data
6. **clean_layer.py**: Test Parquet writing to local and GCS (mocked)
7. **dwh/client.py**: Test BigQuery operations with mocks or test dataset

### Integration Tests

1. End-to-end pipeline with sample CSV/XLSX/JSON files
2. Verify data flows from raw file to BigQuery tables
3. Test error handling at each pipeline stage
4. Verify ingest_runs tracking accuracy

### Test Fixtures

- `tests/fixtures/sample_assessment.csv`: Sample assessment data
- `tests/fixtures/sample_attendance.xlsx`: Sample attendance data
- `tests/fixtures/sample_feedback.json`: Sample feedback data
- `tests/fixtures/concepts_test.yaml`: Minimal concepts catalog for testing

## Dependencies

### New Python Packages

```
sentence-transformers>=2.2.0
pandas>=2.0.0
pyarrow>=12.0.0
openpyxl>=3.1.0
pandera>=0.17.0
google-cloud-bigquery>=3.11.0
google-cloud-storage>=2.10.0
python-magic>=0.4.27  # optional
pyyaml>=6.0
numpy>=1.24.0
scikit-learn>=1.3.0  # for cosine_similarity
```

All dependencies use MIT/Apache 2.0 licenses.

## Performance Considerations

1. **Embedding Model**: Load once at startup, cache in memory
2. **Concepts Catalog**: Precompute embeddings at startup, cache
3. **BigQuery**: Use batch loading, partitioning, and clustering
4. **Parquet**: Efficient columnar format for clean layer
5. **Streaming**: Use streaming for large file downloads from GCS

## Security and Privacy

1. **No External APIs**: All ML models run locally
2. **Data Locality**: Processing within configured GCP region
3. **Pseudonymization**: Optional hashing of student IDs
4. **Logging**: Never log raw data values, only metadata
5. **Access Control**: Rely on GCS and BigQuery IAM policies

## Deployment Notes

1. **Cloud Run Service**: Deploy as independent Cloud Run service named "tabular-service"
2. **Model Download**: sentence-transformers downloads models on first use (~400MB)
3. **Memory**: Embedding model requires ~1GB RAM, configure Cloud Run with 2GB minimum
4. **CPU**: Configure Cloud Run with 2 vCPUs for embedding performance
5. **Concurrency**: Set max concurrency to 10 to balance throughput and memory usage
6. **BigQuery Setup**: Terraform provisions datasets and tables
7. **Concepts Catalog**: Deploy concepts.yaml with application container
8. **Environment Variables**: Configure all settings via Cloud Run environment variables
9. **Service Account**: Grant Cloud Run service account permissions for:
   - Cloud Storage read access (for text_uri retrieval)
   - BigQuery write access (for data loading)
10. **Health Checks**: Configure Cloud Run health check endpoint at /health
11. **Logging**: Enable structured logging with JSON format for Cloud Logging integration
12. **Monitoring**: Set up Cloud Monitoring alerts for:
    - High error rates
    - Long processing times
    - Memory usage spikes

