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

### Event-Driven Architecture

The Tabular Service is triggered by Eventarc when Transformer saves text files to Cloud Storage:

```
Cloud Storage (text/*.txt) → Eventarc Trigger → Tabular Service
    ↓
Parse CloudEvent → Extract file_id
    ↓
Download text from GCS → Parse YAML frontmatter
    ↓
[Existing pipeline: analyze → classify → map → normalize → validate → load]
    ↓
Update Backend (fire-and-forget) → Return 200 to Eventarc
```

**Key Integration Points:**
1. **Eventarc Trigger**: Filters on `text/*.txt` pattern in configured bucket
2. **CloudEvents**: Standard format for event delivery
3. **Frontmatter**: All metadata embedded in text file (no separate API call needed)
4. **Backend Updates**: Fire-and-forget status updates (don't block Eventarc response)

### High-Level Flow

#### Full Pipeline Context
```
User Upload → Backend → Cloud Storage
    ↓
Eventarc Trigger #1 (uploads/*)
    ↓
MIME Decoder (orchestration)
    ↓
Transformer (format conversion)
    ↓
Transformer saves text → gs://bucket/text/file_id.txt
    ↓
Eventarc Trigger #2 (text/*) ⭐ NEW
    ↓
**Tabular Service** (this component)
    ↓
BigQuery → Status to Backend → UI
```

#### Tabular Service Internal Flow

```
CloudEvent from Eventarc
    ↓
[Parse CloudEvent] → Extract bucket, object_name, file_id, event_id
    ↓
[Retrieve Text from GCS] → text content with frontmatter
    ↓
[Parse YAML Frontmatter] → Extract metadata from nested structure:
    - Top-level: file_id, region_id, text_uri, event_id, file_category
    - original.*: filename, content_type, size_bytes, bucket, object_path, uploaded_at
    - extraction.*: method, timestamp, success, duration_ms
    - content.*: text_length, word_count, character_count
    - document.*: page_count, sheet_count, slide_count
    ↓
[Content Type Detection] → Check original.content_type from frontmatter
    ↓
    ├─────────────────────┬─────────────────────┐
    ↓                     ↓                     
TABULAR PATH         FREE_FORM PATH        
(Excel, CSV,         (PDF, Audio,          
 JSON arrays)         plain text)          
    ↓                     ↓                     
[DataFrame Loading]  [Entity Extraction]  
    ↓                     ↓                     
[AI Table           [Entity Resolution]   
 Classification]         ↓                  
    ↓                [Sentiment Analysis]      
[AI Column Mapping]      ↓                
    ↓                [Store in             
[Entity Resolution]  observations table]      
    ↓                     
[Normalization]          
    ↓                                        
[Pandera Validation]
    ↓
[Clean Layer Write] → Parquet (GCS)
    ↓
[BigQuery Load] → Staging → MERGE → Core Tables
    ↓
[Update Backend] → Fire-and-forget status update
    ↓
Return 200 to Eventarc
```

**Content Type Detection Logic:**
- `application/vnd.ms-excel`, `text/csv`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` → TABULAR
- `application/pdf`, `audio/*`, `text/plain` (from transcript) → FREE_FORM
- `application/json` → Analyze structure (array of objects with consistent keys = TABULAR, otherwise FREE_FORM)
- Unknown → Analyze text structure heuristically

### Module Structure

```
src/eduscale/
├── core/
│   └── config.py                    # Extended settings
├── tabular/
│   ├── concepts.py                  # Concepts catalog + embeddings (merged)
│   ├── classifier.py                # AI table classification
│   ├── mapping.py                   # AI column-to-concept mapping
│   ├── schemas.py                   # Pandera validation schemas (separate for readability)
│   ├── normalize.py                 # Data normalization
│   ├── clean_layer.py               # Parquet writing (local/GCS abstraction)
│   ├── runs_store.py                # BigQuery ingest runs tracking
│   ├── pipeline.py                  # Main orchestration + frontmatter parsing
│   └── analysis/                    # 🆕 AI Analysis Module
│       ├── __init__.py
│       ├── feedback_analyzer.py     # Feedback text analysis & target detection
│       ├── entity_resolver.py       # Entity resolution (fuzzy matching + embeddings)
│       ├── llm_client.py            # LLM client for entity extraction and sentiment
│       └── models.py                # Data models for analysis
├── dwh/
│   └── client.py                    # BigQuery DWH operations
└── api/
    └── v1/
        └── routes_tabular.py        # FastAPI endpoints for Tabular service

config/
└── concepts.yaml                    # Table types and concepts catalog

tests/
├── fixtures/
│   ├── sample_text_csv.txt          # Text file with CSV content + frontmatter
│   ├── sample_text_json.txt         # Text file with JSON content + frontmatter
│   ├── sample_text_tsv.txt          # Text file with TSV content + frontmatter
│   ├── sample_feedback.txt          # Feedback text with entity mentions
│   └── sample_cloudevent.json       # CloudEvent payload example
├── test_frontmatter.py              # Frontmatter parsing tests
├── test_classifier.py               # AI classification tests
├── test_mapping.py                  # AI mapping tests
├── test_schemas.py                  # Pandera validation tests
├── test_clean_layer.py              # Parquet writing tests
├── test_feedback_analyzer.py        # 🆕 Feedback analysis tests
├── test_entity_resolver.py          # 🆕 Entity resolution tests
└── test_integration.py              # End-to-end pipeline tests

# REUSED (not created):
# - services/transformer/storage.py (StorageClient)
# - core/logging.py (logging patterns)
```

**Modules: 8 core + 3 analysis = 11 total**
**Tests: 5 core + 2 analysis = 7 total**

## Reused Components from Existing Codebase

Before implementing new components, we leverage existing, proven implementations:

### 1. StorageClient (`services/transformer/storage.py`)

**Reused functionality:**
- `download_file()` - Download files from GCS with retry logic
- `upload_text_streaming()` - Stream text uploads to GCS
- `get_file_size()` - Get file metadata
- Built-in retry logic with tenacity (3 attempts, exponential backoff)
- Structured error handling (NotFound, Forbidden, generic exceptions)
- Comprehensive logging with context

**Usage in Tabular:**
```python
from eduscale.services.transformer.storage import StorageClient

storage = StorageClient(project_id=settings.GCP_PROJECT_ID)
text_content = storage.download_file(bucket, object_name, temp_path)
```

### 2. Logging Patterns (`core/logging.py`)

**Reused functionality:**
- Structured JSON logging for Cloud Logging
- Correlation IDs for request tracing
- Contextual extra fields
- Log level management

### 3. Config Management (`core/config.py`)

**Reused functionality:**
- Pydantic Settings with environment variable loading
- Property-based computed values
- Type validation
- .env file support

---

## Components and Interfaces

### 0. CloudEvents Handler (routes_tabular.py)

**Purpose**: Receive and parse CloudEvents from Eventarc

**Interface**:
```python
@app.post("/")
async def handle_cloud_event(request: Request) -> JSONResponse:
    """Receive CloudEvents from Eventarc and trigger tabular processing."""
```

**CloudEvents Payload**:
```json
{
  "specversion": "1.0",
  "type": "google.cloud.storage.object.v1.finalized",
  "source": "//storage.googleapis.com/projects/_/buckets/BUCKET",
  "subject": "objects/text/abc123.txt",
  "id": "event-id-456",
  "time": "2025-11-14T10:30:10Z",
  "data": {
    "bucket": "eduscale-uploads-eu",
    "name": "text/abc123.txt",
    "contentType": "text/plain",
    "size": "15000"
  }
}
```

**Response**:
- 200: Successfully processed (or skipped non-text files)
- 400: Invalid event payload (no retry)
- 500: Processing error (Eventarc will retry)

**Algorithm**:
1. Parse CloudEvent from request body
2. Validate event type (google.cloud.storage.object.v1.finalized)
3. Extract bucket and object_name from data
4. Check if object_name matches "text/*.txt" pattern
5. Extract file_id from object_name (text/{file_id}.txt)
6. Download text content from GCS
7. Call process_tabular_text() with text content
8. Fire-and-forget Backend status update
9. Return 200 to Eventarc
10. Log all steps with event_id as correlation_id

### 0.5. Frontmatter Parser (pipeline.py)

**Purpose**: Parse YAML frontmatter from text files

**Interface**:
```python
@dataclass
class FrontmatterData:
    # Top-level fields
    file_id: str
    region_id: str
    text_uri: str
    event_id: str | None
    file_category: str | None
    
    # Original file metadata (from 'original' section)
    original_filename: str | None
    original_content_type: str | None
    original_size_bytes: int | None
    bucket: str | None
    object_path: str | None
    uploaded_at: str | None
    
    # Extraction metadata (from 'extraction' section)
    extraction_method: str | None
    extraction_timestamp: str | None
    extraction_success: bool | None
    extraction_duration_ms: int | None
    
    # Content metrics (from 'content' section)
    text_length: int | None
    word_count: int | None
    character_count: int | None
    
    # Document-specific metadata (from 'document' section)
    page_count: int | None
    sheet_count: int | None
    slide_count: int | None

def parse_frontmatter(text_content: str) -> tuple[FrontmatterData | None, str]:
    """Parse YAML frontmatter and return metadata + clean text.
    
    Returns:
        (frontmatter_data, text_without_frontmatter)
    """
```

**Frontmatter Format** (from Transformer):
```yaml
---
file_id: "abc123"
region_id: "region-cz-01"
event_id: "cloudevent-xyz"
text_uri: "gs://bucket/text/abc123.txt"
file_category: "pdf"

original:
  filename: "document.pdf"
  content_type: "application/pdf"
  size_bytes: 123456
  bucket: "bucket-name"
  object_path: "uploads/region/abc123.pdf"
  uploaded_at: "2025-01-14T10:30:00Z"

extraction:
  method: "pdfplumber"
  timestamp: "2025-01-14T10:31:00Z"
  duration_ms: 1234
  success: true

content:
  text_length: 5432
  word_count: 987
  character_count: 5432

document:
  page_count: 15
---
```

**Algorithm**:
1. Check if text starts with "---\n"
2. Find second "---" delimiter
3. Extract YAML content between delimiters
4. Parse YAML using pyyaml
5. Extract top-level fields: file_id, region_id, text_uri, event_id, file_category
6. Extract nested 'original' section fields: filename, content_type, size_bytes, bucket, object_path, uploaded_at
7. Extract nested 'extraction' section fields: method, timestamp, success, duration_ms
8. Extract nested 'content' section fields: text_length, word_count, character_count
9. Extract nested 'document' section fields: page_count, sheet_count, slide_count
10. Map all fields to FrontmatterData dataclass
11. Return metadata + text after second "---"
12. If parsing fails, return (None, original_text)

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
    
    # AI Models configuration
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-m3"  # BGE-M3 for embeddings
    LLM_MODEL_NAME: str = "llama3.2:1b"  # Llama 3.2 1B via Ollama
    LLM_ENDPOINT: str = "http://localhost:11434"  # Ollama in same container
    LLM_ENABLED: bool = True
    
    INGEST_MAX_ROWS: int = 200_000
    PSEUDONYMIZE_IDS: bool = False
    
    # AI Analysis settings
    FEEDBACK_ANALYSIS_ENABLED: bool = True
    ENTITY_RESOLUTION_THRESHOLD: float = 0.85  # Fuzzy matching threshold
    FEEDBACK_TARGET_THRESHOLD: float = 0.65  # Embedding similarity threshold
    MAX_TARGETS_PER_FEEDBACK: int = 10  # Max FeedbackTarget records per feedback
    ENTITY_CACHE_TTL_SECONDS: int = 3600  # Cache entity lookups for 1 hour
    
    @property
    def bigquery_project(self) -> str:
        """Get BigQuery project ID, defaulting to GCP_PROJECT_ID."""
        return self.BIGQUERY_PROJECT_ID or self.GCP_PROJECT_ID
    
    @property
    def bigquery_staging_dataset(self) -> str:
        """Get staging dataset, defaulting to main dataset."""
        return self.BIGQUERY_STAGING_DATASET_ID or self.BIGQUERY_DATASET_ID
```






### 2. Concepts Catalog + Embeddings (concepts.py)

**Purpose**: Load and manage canonical concepts, table types, and embedding model

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
# Embedding functions (merged from embeddings.py)
def init_embeddings() -> None:
    """Load and cache the sentence-transformer model."""

def embed_texts(texts: list[str]) -> np.ndarray:
    """Generate embeddings for a list of texts."""

# Concepts catalog functions
def load_concepts_catalog(path: str) -> ConceptsCatalog:
    """Load catalog from YAML and precompute embeddings."""

def get_table_type_anchors() -> list[TableType]:
    """Get all table types with embeddings."""

def get_concepts() -> list[Concept]:
    """Get all concepts with embeddings."""
```

**Implementation Notes:**
- Module-level cached embedding model (lazy loading)
- BGE-M3 model: 1024-dimensional embeddings, hybrid retrieval support
- Precompute embeddings at startup for performance
- Model size: ~2.2GB, supports 100+ languages including Czech

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
  
  - name: RELATIONSHIP
    anchors:
      - "entity relationships and connections"
      - "junction table data"
      - "relační data"
      - "student-teacher-subject assignments"
      - "region-rule associations"
      - "experiment-criteria mappings"
  


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
  
  - key: region_type
    description: "Type of region (school, district, municipality)"
    expected_type: categorical
    synonyms:
      - "Region Type"
      - "Type"
      - "Typ oblasti"
      - "Administrative Level"
  
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
  
  # Analysis Result Fields
  - key: analysis_id
    description: "Unique analysis result identifier"
    expected_type: string
    synonyms:
      - "Analysis ID"
      - "AnalysisID"
      - "ID analýzy"
      - "Report ID"
  
  - key: analysis_timestamp
    description: "Timestamp when analysis was performed"
    expected_type: date
    synonyms:
      - "Analysis Timestamp"
      - "Analysis Date"
      - "Čas analýzy"
      - "Report Date"
  
  - key: analysis_status
    description: "Status of analysis (PROCESSING, COMPLETED, FAILED)"
    expected_type: categorical
    synonyms:
      - "Analysis Status"
      - "Status"
      - "Stav analýzy"
      - "Report Status"
  
  - key: analysis_report
    description: "Text content of analysis report"
    expected_type: string
    synonyms:
      - "Analysis Report"
      - "Report"
      - "Zpráva analýzy"
      - "Analysis Text"
      - "Findings"
  
  # Junction Table / Relationship Fields
  - key: student_teacher_subject_id
    description: "Unique identifier for student-teacher-subject relationship"
    expected_type: string
    synonyms:
      - "Relationship ID"
      - "Assignment ID"
      - "ID vztahu"
  
  - key: weight
    description: "Weight or importance factor"
    expected_type: number
    synonyms:
      - "Weight"
      - "Váha"
      - "Importance"
      - "Priority"
  
  - key: role
    description: "Role in relationship or experiment"
    expected_type: categorical
    synonyms:
      - "Role"
      - "Role Type"
      - "Úloha"
      - "Function"
  
  - key: relevance_score
    description: "Relevance score for feedback target"
    expected_type: number
    synonyms:
      - "Relevance"
      - "Relevance Score"
      - "Skóre relevance"
      - "Confidence"
  
  - key: impact_score
    description: "Impact score for analysis impact"
    expected_type: number
    synonyms:
      - "Impact"
      - "Impact Score"
      - "Skóre dopadu"
      - "Effect Score"
  
  - key: target_type
    description: "Type of polymorphic target entity"
    expected_type: categorical
    synonyms:
      - "Target Type"
      - "Entity Type"
      - "Typ cíle"
      - "Reference Type"
  
  - key: target_id
    description: "ID of polymorphic target entity"
    expected_type: string
    synonyms:
      - "Target ID"
      - "Entity ID"
      - "ID cíle"
      - "Reference ID"
  
  - key: timestamp
    description: "Generic timestamp field"
    expected_type: date
    synonyms:
      - "Timestamp"
      - "Time"
      - "Čas"
      - "DateTime"
  
  - key: source_url
    description: "Source URL for rules or references"
    expected_type: string
    synonyms:
      - "Source URL"
      - "URL"
      - "Zdrojová URL"
      - "Link"
      - "Reference URL"
  
  - key: status
    description: "Generic status field for relationships and entities"
    expected_type: categorical
    synonyms:
      - "Status"
      - "Stav"
      - "State"
      - "Active Status"
```




### 3. DataFrame Loading from Text (pipeline.py)

**Purpose**: Load text content into pandas DataFrames

**Interface**:
```python
@dataclass
class TabularSource:
    file_id: str
    region_id: str
    text_uri: str
    frontmatter: FrontmatterData

def load_dataframe_from_text(
    text_content: str, 
    frontmatter: FrontmatterData
) -> pd.DataFrame:
    """Load text into DataFrame based on content type from frontmatter."""
```

**Algorithm**:
1. Retrieve text content from Cloud Storage using text_uri
2. Detect format from frontmatter.original_content_type
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


### 4. AI Table Classification (classifier.py)

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
6. If confidence < 0.4, classify as FREE_FORM and route to observations table
7. Return table type with highest score
7. Log decision with top contributing column headers and anchor phrases

### 5. AI Column Mapping (mapping.py)

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

### 6. Pandera Validation (schemas.py)

**Purpose**: Define and enforce data quality schemas per table type

**Schemas**: ATTENDANCE_SCHEMA, ASSESSMENT_SCHEMA, FEEDBACK_SCHEMA, INTERVENTION_SCHEMA, RELATIONSHIP_SCHEMA

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

### 7. Data Normalization (normalize.py)

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

### 8. Clean Layer Storage (clean_layer.py)

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

### 9. BigQuery DWH Client (dwh/client.py)

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
- **Observations**: `observations` (for FREE_FORM data: PDF text, audio transcripts, unstructured feedback)

**Features**:
- Partition by date, cluster by region_id
- Use maximum_bytes_billed for cost control
- Return bytes_processed and cache_hit metadata

### 10. Ingest Runs Tracking (runs_store.py)

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

### 11. Pipeline Orchestration (pipeline.py)

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

### 12. API Endpoints (api/v1/routes_tabular.py)

**Purpose**: Handle CloudEvents from Eventarc and provide testing API

**Primary Endpoint (CloudEvents)**:
```python
@app.post("/")
async def handle_cloud_event(request: Request) -> JSONResponse:
    """Receive CloudEvents from Eventarc for text file processing."""
```

**CloudEvent Flow**:
1. Parse CloudEvent from request body
2. Validate event type and extract bucket, object_name, event_id
3. Filter for text/*.txt pattern (skip others)
4. Extract file_id from object_name
5. Download text content from GCS
6. Parse YAML frontmatter to extract metadata
7. Call process_tabular_text() with text content and frontmatter metadata
8. Fire-and-forget Backend status update
9. Return 200 to Eventarc (or 400/500 for errors)
10. Log all steps with event_id as correlation_id

**Testing Endpoint (Direct API - Optional)**:
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
async def analyze_tabular_direct(request: TabularRequest) -> TabularResponse:
    """Direct API for testing without Eventarc (optional)."""
```

**Direct API Flow** (for testing only):
1. Receive request with text_uri and metadata
2. Download text content from Cloud Storage
3. Parse frontmatter if present
4. Call process_tabular_text() with text content
5. Return response with status and metrics

**Health Check**:
```python
@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint for Cloud Run."""
```

**Note**: The primary integration is via CloudEvents (POST /). The direct API endpoint (/api/v1/tabular/analyze) is optional and can be used for testing or manual triggering.

---

## AI Analysis Module Components

### 13. Feedback Analyzer (analysis/feedback_analyzer.py)

**Purpose**: Analyze feedback text to identify mentioned entities and create FeedbackTarget records

**Applies to both:**
- **Tabular feedback**: Entity resolution on structured columns (teacher_name, student_name, etc.)
- **Free-form feedback**: Entity extraction + resolution from text_content

**Data Models**:
```python
@dataclass
class FeedbackTarget:
    feedback_id: str
    target_type: str  # "teacher", "student", "experiment", "criteria", "region", "subject"
    target_id: str
    relevance_score: float
    confidence: Literal["HIGH", "MEDIUM", "LOW"]

@dataclass
class FeedbackAnalysisResult:
    feedback_id: str
    targets: list[FeedbackTarget]
    processing_time_ms: int
```

**Interface**:
```python
def analyze_feedback_batch(
    df_feedback: pd.DataFrame,
    region_id: str,
    frontmatter: FrontmatterData,
    catalog: ConceptsCatalog
) -> list[FeedbackTarget]:
    """Analyze feedback DataFrame and return detected targets."""
```

**Algorithm**:
1. For each feedback row, extract feedback_id and feedback_text
2. **Extract entity mentions from text** using LLM (Llama 3.2):
   - Call llm_client.extract_entities(feedback_text)
   - LLM returns: [{"text": "Петрова", "type": "person"}, {"text": "математика", "type": "subject"}]
   - Names: "Петрова", "Новак", "И. Петров"
   - Subjects: "математика", "физика"
   - Experiments: "эксперимент X"
3. **Apply entity resolution to each mention**:
   - "Петрова" → fuzzy match → teacher_id (uuid-123)
   - "Новак" → fuzzy match → student_id (uuid-456)
   - "математика" → embedding match → subject_id (uuid-789)
4. Generate embedding for full feedback_text using cached sentence-transformer model
5. Query BigQuery for all entities in the same region (teachers, students, experiments, criteria)
6. For each entity type:
   - Generate embeddings for entity names/descriptions
   - Compute cosine similarity between feedback embedding and entity embeddings
   - If similarity >= 0.65, create FeedbackTarget candidate
7. Combine name-based matches (from step 3) and embedding-based matches (from step 6)
8. Deduplicate targets and select top-N per feedback (max 10 targets)
9. Assign confidence levels: HIGH (>=0.80), MEDIUM (0.65-0.80), LOW (<0.65)
10. Return list of FeedbackTarget records for bulk insert to BigQuery

**Example:**
```python
# Input feedback text
text = "Учитель Петрова отлично объясняет математику. Ученик Новак показывает прогресс."

# Step 1: Extract mentions using LLM
llm_client = LLMClient()
mentions = llm_client.extract_entities(text)
# Returns: [
#     {"text": "Петрова", "type": "person"},
#     {"text": "Новак", "type": "person"},
#     {"text": "математику", "type": "subject"}
# ]

# Step 2: Resolve each mention (determine if person is teacher/student/parent)
resolved = [
    {"mention": "Петрова", "entity_id": "teacher-uuid-123", "confidence": 0.92, "method": "FUZZY"},
    {"mention": "Новак", "entity_id": "student-uuid-456", "confidence": 0.88, "method": "FUZZY"},
    {"mention": "математику", "entity_id": "subject-uuid-789", "confidence": 0.85, "method": "EMBEDDING"}
]

# Step 3: Create FeedbackTarget records
targets = [
    FeedbackTarget(feedback_id, "teacher", "teacher-uuid-123", 0.92, "HIGH"),
    FeedbackTarget(feedback_id, "student", "student-uuid-456", 0.88, "HIGH"),
    FeedbackTarget(feedback_id, "subject", "subject-uuid-789", 0.85, "HIGH")
]
```

**Performance Optimization**:
- Batch entity queries (single query per entity type)
- Cache entity embeddings within ingestion run
- Use vectorized operations for similarity computation

### 14. Entity Resolver (analysis/entity_resolver.py)

**Purpose**: Resolve entity name/ID variations to canonical entity IDs from BigQuery dimension tables

**Scope**: Used for ALL entity types during ingestion, not just for feedback analysis

**Data Models**:
```python
@dataclass
class EntityMatch:
    entity_id: str
    entity_name: str
    entity_type: str
    similarity_score: float
    match_method: Literal["ID_EXACT", "NAME_EXACT", "FUZZY", "EMBEDDING", "NEW"]
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    source_value: str  # Original value from source data

@dataclass
class EntityCache:
    """In-memory cache of entities for fast lookups during ingestion run"""
    teachers: dict[str, str]  # normalized_name -> teacher_id
    students: dict[str, str]
    parents: dict[str, str]
    regions: dict[str, str]
    subjects: dict[str, str]
    schools: dict[str, str]
    # Also store by ID for ID-based lookups
    teacher_ids: dict[str, str]  # source_id -> canonical_teacher_id
    student_ids: dict[str, str]
    # Store embeddings for semantic matching
    teacher_embeddings: dict[str, np.ndarray]
    student_embeddings: dict[str, np.ndarray]
```

**Interface**:
```python
def resolve_entity(
    source_value: str,
    entity_type: str,
    region_id: str,
    cache: EntityCache,
    value_type: Literal["id", "name"] = "name"
) -> EntityMatch:
    """Resolve entity from source data to canonical ID.
    
    Returns EntityMatch with match_method="NEW" if no match found.
    """

def normalize_name(name: str) -> str:
    """Normalize name for matching."""

def expand_initials(name: str, region_id: str) -> list[str]:
    """Expand initials to common full names."""

def create_new_entity(
    entity_type: str,
    source_value: str,
    region_id: str,
    dwh_client: DwhClient
) -> str:
    """Create new entity in dimension table and return new ID."""
```

**Algorithm**:

**normalize_name()**:
1. Convert to lowercase
2. Remove extra whitespace (multiple spaces → single space)
3. Strip leading/trailing whitespace
4. Remove periods from initials ("И." → "И")
5. Standardize punctuation
6. Return normalized string

**expand_initials()**:
1. Detect if name contains single-letter initials (e.g., "И. Петров")
2. Query region-specific name database for common first names starting with initial
3. Generate candidate full names (e.g., ["Иван Петров", "Игорь Петров", "Илья Петров"])
4. Return list of candidates (max 5)

**resolve_entity()**:
1. Determine if source_value is ID or name based on value_type parameter
2. If value_type == "id":
   - Check cache for exact ID match (e.g., teacher_ids[source_value])
   - If found, return EntityMatch with match_method="ID_EXACT", confidence="HIGH"
   - If not found, proceed to name-based matching
3. Normalize input value (name)
4. Check cache for exact normalized name match (O(1) lookup)
5. If exact match found, return EntityMatch with match_method="NAME_EXACT", confidence="HIGH"
6. If no exact match, try fuzzy matching:
   - Use Levenshtein distance with threshold 0.85
   - If name contains initials (e.g., "П. Свободова"), expand and try all candidates
   - If fuzzy match found with score >= 0.85, return with match_method="FUZZY", confidence="HIGH"
   - If fuzzy match found with score 0.70-0.85, return with confidence="MEDIUM"
7. If no fuzzy match, use embedding similarity:
   - Generate embedding for source_value
   - Compute cosine similarity with all cached entity embeddings
   - Select best match if similarity >= 0.75, return with match_method="EMBEDDING", confidence="HIGH"
   - If similarity 0.65-0.75, return with confidence="MEDIUM"
8. If no match found (all scores < thresholds):
   - Call create_new_entity() to insert into dimension table
   - Return EntityMatch with match_method="NEW", confidence="LOW"

**create_new_entity()**:
1. Generate new UUID for entity_id
2. Build entity record with source_value as name
3. Set metadata.source = "auto_created_from_ingestion"
4. Set metadata.original_source_value = source_value
5. Insert into appropriate dimension table (dim_teacher, dim_student, etc.)
6. Add to cache for subsequent lookups in same ingestion run
7. Log creation with source file_id for audit
8. Return new entity_id

**Entity Cache Loading**:
```python
def load_entity_cache(region_id: str, dwh_client: DwhClient) -> EntityCache:
    """Load entities from BigQuery for the region."""
```
- Query ALL dimension tables: dim_teacher, dim_student, dim_parent, dim_region, dim_subject, dim_school
- For region-specific entities (teachers, students), filter by region_id
- For global entities (subjects, regions), load all
- Build normalized_name → entity_id mappings
- Build source_id → canonical_id mappings (from metadata.source_ids if available)
- Precompute embeddings for all entity names
- Return EntityCache for fast lookups during ingestion run
- Cache TTL: duration of ingestion run (no cross-run caching to ensure fresh data)



### 15. LLM Client (analysis/llm_client.py)

**Purpose**: Interface to Ollama for LLM-based tasks

**Interface**:
```python
class LLMClient:
    def __init__(self, endpoint: str = "http://localhost:11434"):
        self.endpoint = endpoint
        self.model = settings.LLM_MODEL_NAME
    
    def extract_entities(self, text: str) -> list[dict]:
        """Extract named entities from text using LLM."""
    
    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment using LLM, return -1.0 to +1.0."""
    

    
    def _call_ollama(self, prompt: str, max_tokens: int = 500) -> str:
        """Internal method to call Ollama API."""
```

**Implementation**:
```python
def extract_entities(self, text: str) -> list[dict]:
    prompt = f"""Extract person names, subjects, and locations from this Czech/English educational text.
    Return ONLY a JSON array with this exact format: [{{"text": "name", "type": "person|subject|location"}}]
    Do not include any explanation, only the JSON array.
    
    Text: {text}
    
    JSON:"""
    
    response = self._call_ollama(prompt, max_tokens=200)
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse LLM response: {response}")
        return []

def analyze_sentiment(self, text: str) -> float:
    prompt = f"""Analyze the sentiment of this educational feedback (Czech/English).
    Return ONLY a single number from -1.0 (very negative) to +1.0 (very positive).
    Do not include any explanation, only the number.
    
    Text: {text}
    
    Score:"""
    
    response = self._call_ollama(prompt, max_tokens=10)
    try:
        return float(response.strip())
    except ValueError:
        logger.warning(f"Failed to parse sentiment: {response}")
        return 0.0

def _call_ollama(self, prompt: str, max_tokens: int = 500) -> str:
    import requests
    
    response = requests.post(
        f"{self.endpoint}/api/generate",
        json={
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.1  # Low temperature for deterministic outputs
            }
        },
        timeout=30
    )
    response.raise_for_status()
    return response.json()["response"]
```

### 16. Analysis Models (analysis/models.py)

**Purpose**: Shared data models for analysis module

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

@dataclass
class FeedbackTarget:
    feedback_id: str
    target_type: str
    target_id: str
    relevance_score: float
    confidence: Literal["HIGH", "MEDIUM", "LOW"]

@dataclass
class EntityMatch:
    entity_id: str
    entity_name: str
    entity_type: str
    similarity_score: float
    match_method: Literal["EXACT", "FUZZY", "EMBEDDING", "ID"]

@dataclass
class AnalysisImpact:
    analysis_id: str
    target_type: str
    target_id: str
    impact_score: float
    sentiment_avg: float


    analysis_status: Literal["PROCESSING", "COMPLETED", "FAILED"]
    analysis_report: str
    feedback_count: int
    impact_targets: list[AnalysisImpact]
```

---

## Updated Pipeline Flow with AI Analysis

### Enhanced Pipeline Steps

```
CloudEvent from Eventarc
    ↓
[Parse CloudEvent] → Extract bucket, object_name, file_id, event_id
    ↓
[Retrieve Text from GCS] → text content with frontmatter
    ↓
[Parse YAML Frontmatter] → Extract nested metadata structure
    ↓
[Content Type Detection] → Use frontmatter.original_content_type
    ↓
[DataFrame Loading] → pandas.DataFrame
    ↓
[AI Table Classification] → ATTENDANCE/ASSESSMENT/FEEDBACK/INTERVENTION/RELATIONSHIP (or route to FREE_FORM if confidence < 0.4)
    ↓
[AI Column Mapping] → source_column → concept_key mappings
    ↓
🆕 [Load Entity Cache] → Query BigQuery dimension tables for region
    ↓
🆕 [Entity Resolution] → Match ALL entity columns to canonical IDs
    │   ├─ student_id/student_name → canonical student_id
    │   ├─ teacher_id/teacher_name → canonical teacher_id
    │   ├─ parent_id/parent_name → canonical parent_id
    │   ├─ region_id/region_name → canonical region_id
    │   ├─ subject_id/subject → canonical subject_id
    │   └─ school_name → canonical school_id
    ↓
[Normalization] → Canonical DataFrame with resolved entity IDs + metadata
    ↓
[Pandera Validation] → Quality checks
    ↓
[Clean Layer Write] → Parquet (GCS)
    ↓
[BigQuery Load] → Staging → MERGE → Core Tables
    ↓
🆕 [IF table_type == FEEDBACK]:
    ↓
    [Feedback Text Analysis] → Detect entity mentions in text_content
    ↓
    [Entity Resolution for Mentions] → Match mentioned entities to canonical IDs
    ↓
    [Create FeedbackTarget] → Insert polymorphic relationships to BigQuery
    ↓
[Update Backend] → Fire-and-forget status update
    ↓
Return 200 to Eventarc
```

### Key Changes:

1. **Entity Resolution moved BEFORE Normalization**: Now resolves ALL entity references, not just feedback
2. **Entity Cache loaded once per ingestion**: Reused for all entity lookups
3. **Feedback Analysis separate**: Only for detecting entities MENTIONED in feedback text (polymorphic FeedbackTarget)
4. **New entities auto-created**: If no match found, creates new dimension table record



## Service Integration

### Transformer → Tabular Flow (Event-Driven)

1. **Transformer completes text extraction**
   - Extracts text from file
   - Builds YAML frontmatter with nested metadata structure (original.*, extraction.*, content.*, document.*)
   - Uploads text WITH frontmatter to GCS (gs://bucket/text/file_id.txt)
   - Returns text_uri to MIME Decoder

2. **GCS emits OBJECT_FINALIZE event**
   - Event triggered when text file is created
   - Contains bucket, object_name, contentType, size

3. **Eventarc filters and routes event**
   - Filters for `text/*.txt` pattern
   - Delivers CloudEvent to Tabular service

4. **Tabular processes CloudEvent**
   - Parses CloudEvent to extract file_id
   - Downloads text file from text_uri
   - Parses YAML frontmatter to extract metadata
   - Analyzes text structure (AFTER frontmatter)
   - Loads to BigQuery
   - Updates Backend (fire-and-forget)
   - Returns 200 to Eventarc

5. **Backend receives status update**
   - Updates file processing status
   - Updates UI with data health and preview

### Event-Driven Characteristics

- **Fully Asynchronous**: Tabular triggered independently via Eventarc
- **Decoupled**: Transformer doesn't know about Tabular
- **Scalable**: Cloud Run scales Tabular service based on load
- **Resilient**: Eventarc retries on failures with exponential backoff
- **Observable**: Structured logs with CloudEvent correlation IDs
- **Consistent**: Same pattern as uploads → MIME Decoder flow

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

**Core Pipeline Tests:**
1. **classifier.py**: Test classification with synthetic DataFrames for each table type
2. **mapping.py**: Test column mapping with known column names and expected concepts
4. **normalize.py**: Test type casting, metadata addition, data cleaning
5. **schemas.py**: Test Pandera validation with valid and invalid data
6. **clean_layer.py**: Test Parquet writing to local and GCS (mocked)
7. **dwh/client.py**: Test BigQuery operations with mocks or test dataset

**🆕 AI Analysis Tests:**
8. **feedback_analyzer.py**: Test feedback target detection with sample feedback text
9. **entity_resolver.py**: Test name normalization, fuzzy matching, and initial expansion
   - Test exact matches: "Иван Петров" → "Иван Петров"
   - Test fuzzy matches: "Иван Пeтров" (typo) → "Иван Петров"
   - Test initial variations: "И. Петров" → ["Иван Петров", "Игорь Петров"]
   - Test embedding-based matching for semantic similarity

### Integration Tests

1. End-to-end pipeline with sample CSV/TSV/JSON files
2. Verify data flows from raw file to BigQuery tables
3. Test error handling at each pipeline stage
4. Verify ingest_runs tracking accuracy
5. 🆕 Test feedback ingestion with automatic FeedbackTarget creation

### Test Fixtures

- `tests/fixtures/sample_assessment.csv`: Sample assessment data
- `tests/fixtures/sample_attendance.xlsx`: Sample attendance data
- `tests/fixtures/sample_feedback.json`: Sample feedback data with entity mentions
- `tests/fixtures/sample_feedback.txt`: Feedback text with Czech names and initials
- `tests/fixtures/concepts_test.yaml`: Minimal concepts catalog for testing
- `tests/fixtures/mock_entities.json`: Mock teacher/student/region data for entity resolution tests

## Dependencies

### New Python Packages

```
sentence-transformers>=2.3.0  # For BGE-M3 embeddings
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
python-Levenshtein>=0.21.0  # for fuzzy string matching
rapidfuzz>=3.0.0  # faster alternative to python-Levenshtein
requests>=2.31.0  # for Ollama API calls
```

**System Dependencies:**
- Ollama (installed via curl script in Dockerfile)

All Python dependencies use MIT/Apache 2.0 licenses.

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
2. **AI Models**:
   - BGE-M3 embedding model: ~2.2GB (downloaded on first use)
   - Llama 3.2 1B via Ollama: ~1.3GB (pulled during container startup)
   - Total model size: ~3.5GB
3. **Memory**: Configure Cloud Run with 4GB minimum (models + application overhead)
4. **CPU**: Configure Cloud Run with 2 vCPUs for model inference performance
5. **Concurrency**: Set max concurrency to 5 (lower due to LLM memory usage)
6. **Startup**: Cold start ~20-30 seconds (Ollama startup + model loading)
6. **BigQuery Setup**: 
   - Terraform provisions datasets (core and staging) via terraform-gcp-infrastructure spec
   - Terraform creates all required tables (dimensions, facts, observations, ingest_runs)
   - Tables are pre-configured with partitioning and clustering
   - Dataset location matches region variable for data locality
   - Staging tables auto-expire after 7 days (configurable)
7. **Concepts Catalog**: Deploy concepts.yaml with application container
8. **Environment Variables**: Configure all settings via Cloud Run environment variables
   - BIGQUERY_DATASET_ID should match terraform bigquery_dataset_id variable
   - BIGQUERY_STAGING_DATASET_ID should match terraform bigquery_staging_dataset_id variable
9. **Service Account**: Grant Cloud Run service account permissions for:
   - Cloud Storage read access (for text_uri retrieval)
   - BigQuery write access (for data loading to both core and staging datasets)
   - Roles: roles/storage.objectViewer, roles/bigquery.dataEditor, roles/bigquery.jobUser
10. **Health Checks**: Configure Cloud Run health check endpoint at /health
11. **Logging**: Enable structured logging with JSON format for Cloud Logging integration
12. **Monitoring**: Set up Cloud Monitoring alerts for:
    - High error rates
    - Long processing times
    - Memory usage spikes
13. **Terraform Integration**: 
    - Run terraform-gcp-infrastructure spec tasks 11-18 to provision BigQuery resources
    - Verify BigQuery outputs match Tabular service configuration
    - Ensure dataset location matches Cloud Run service region

14. **Docker Image with Ollama**:
```dockerfile
FROM python:3.11-slim

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download BGE-M3 model (optional, speeds up first run)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"

# Copy application code
COPY src/ /app/src/
COPY config/ /app/config/
WORKDIR /app

# Create startup script
RUN echo '#!/bin/bash\n\
ollama serve &\n\
sleep 5\n\
ollama pull llama3.2:1b\n\
uvicorn src.eduscale.api.v1.routes_tabular:app --host 0.0.0.0 --port 8080' > /start.sh && chmod +x /start.sh

CMD ["/start.sh"]
```

