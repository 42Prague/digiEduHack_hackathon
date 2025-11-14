"""Configuration management for EduScale Engine."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    ENV: str = "local"
    SERVICE_NAME: str = "eduscale-engine"
    SERVICE_VERSION: str = "0.1.0"

    # GCP Configuration
    GCP_PROJECT_ID: str = ""
    GCP_REGION: str = "europe-west1"
    GCP_RUN_SERVICE: str = "eduscale-engine"

    # Storage Configuration
    STORAGE_BACKEND: str = "local"  # "gcs" or "local"
    GCS_BUCKET_NAME: str = ""

    # Upload Constraints
    MAX_UPLOAD_MB: int = 50
    ALLOWED_UPLOAD_MIME_TYPES: str = ""  # Comma-separated, empty = allow all
    DIRECT_UPLOAD_SIZE_THRESHOLD_MB: int = 31  # Files larger than this use signed URLs

    # MIME Decoder Service Configuration
    TRANSFORMER_SERVICE_URL: str = ""
    BACKEND_SERVICE_URL: str = ""
    REQUEST_TIMEOUT: int = 300  # seconds for Transformer calls
    BACKEND_UPDATE_TIMEOUT: int = 5  # seconds for Backend status updates
    LOG_LEVEL: str = "INFO"

    # Archive Extraction Configuration
    ENABLE_ARCHIVE_EXTRACTION: bool = True
    MAX_ARCHIVE_SIZE_MB: int = 1024
    MAX_FILES_PER_ARCHIVE: int = 100
    MAX_EXTRACTED_FILE_SIZE_MB: int = 500
    UPLOADS_BUCKET: str = ""  # GCS bucket name for uploads

    # Transformer Service Configuration
    MAX_FILE_SIZE_MB: int = 100
    SPEECH_LANGUAGE_EN: str = "en-US"
    SPEECH_LANGUAGE_CS: str = "cs-CZ"

    # Tabular Service Configuration
    BIGQUERY_DATASET_ID: str = "jedouscale_core"
    BIGQUERY_STAGING_DATASET_ID: str = ""  # Defaults to BIGQUERY_DATASET_ID
    CLEAN_LAYER_BASE_PATH: str = "./data/clean"
    CONCEPT_CATALOG_PATH: str = "./config/concepts.yaml"

    # AI Models Configuration
    # LLM via Featherless.ai (serverless, open-source)
    FEATHERLESS_API_KEY: str = ""  # API key from featherless.ai
    FEATHERLESS_BASE_URL: str = "https://api.featherless.ai/v1"
    FEATHERLESS_LLM_MODEL: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"  # Llama 3.1 8B for entity extraction
    LLM_ENABLED: bool = True
    
    # Embeddings via sentence-transformers (local)
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"  # 470MB, 50+ languages
    EMBEDDING_DIMENSION: int = 768

    # Ingestion Configuration
    INGEST_MAX_ROWS: int = 200_000
    PSEUDONYMIZE_IDS: bool = False

    # AI Analysis Settings
    FEEDBACK_ANALYSIS_ENABLED: bool = True
    ENTITY_RESOLUTION_THRESHOLD: float = 0.85  # Fuzzy matching threshold
    FEEDBACK_TARGET_THRESHOLD: float = 0.65  # Embedding similarity threshold
    MAX_TARGETS_PER_FEEDBACK: int = 10  # Max FeedbackTarget records per feedback
    ENTITY_CACHE_TTL_SECONDS: int = 3600  # Cache entity lookups for 1 hour

    # Natural Language Query (NLQ) Configuration
    NLQ_MAX_RESULTS: int = 100  # Maximum rows returned by NLQ queries
    NLQ_QUERY_TIMEOUT_SECONDS: int = 60  # Timeout for BigQuery queries
    BQ_MAX_BYTES_BILLED: int | None = None  # Optional limit on BigQuery bytes billed

    @property
    def bigquery_project(self) -> str:
        """Get BigQuery project ID from GCP_PROJECT_ID."""
        return self.GCP_PROJECT_ID

    @property
    def bigquery_staging_dataset(self) -> str:
        """Get staging dataset, defaulting to main dataset."""
        return self.BIGQUERY_STAGING_DATASET_ID or self.BIGQUERY_DATASET_ID

    @property
    def allowed_mime_types(self) -> list[str] | None:
        """Parse ALLOWED_UPLOAD_MIME_TYPES into a list."""
        if not self.ALLOWED_UPLOAD_MIME_TYPES:
            return None
        return [mt.strip() for mt in self.ALLOWED_UPLOAD_MIME_TYPES.split(",")]

    @property
    def max_upload_bytes(self) -> int:
        """Convert MAX_UPLOAD_MB to bytes."""
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def direct_upload_threshold_bytes(self) -> int:
        """Convert DIRECT_UPLOAD_SIZE_THRESHOLD_MB to bytes."""
        return self.DIRECT_UPLOAD_SIZE_THRESHOLD_MB * 1024 * 1024

    @property
    def max_archive_size_bytes(self) -> int:
        """Convert MAX_ARCHIVE_SIZE_MB to bytes."""
        return self.MAX_ARCHIVE_SIZE_MB * 1024 * 1024

    @property
    def max_extracted_file_size_bytes(self) -> int:
        """Convert MAX_EXTRACTED_FILE_SIZE_MB to bytes."""
        return self.MAX_EXTRACTED_FILE_SIZE_MB * 1024 * 1024


# Singleton settings instance
settings = Settings()
