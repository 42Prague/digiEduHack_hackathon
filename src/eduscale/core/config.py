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
