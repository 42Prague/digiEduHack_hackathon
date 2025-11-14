"""
Application Settings Configuration
----------------------------------
This module defines the global settings for the SwX-API.

Features:
- Reads environment variables from `.env` file.
- Configures API, database, security, email, and CORS settings.
- Provides dynamic property-based settings.

Configuration Sections:
- API Configuration
- Security & Authentication
- CORS (Cross-Origin Resource Sharing)
- Database Configuration
- Email Settings
- Superuser Defaults
"""

import secrets
from typing import Any, List, Literal, Union
from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application-wide settings, loaded from environment variables or `.env` file.

    Attributes:
        PROJECT_NAME (str): Name of the project.
        ROUTE_PREFIX (str): Base API route prefix.
        API_VERSIONS (List[str]): List of supported API versions.
        DEFAULT_API_VERSION (str): Default API version.
        BACKEND_HOST (str): Backend service host URL.
        FRONTEND_HOST (str): Frontend application URL.
        ENVIRONMENT (Literal): Deployment environment (`local`, `staging`, `production`).
        SECRET_KEY (str): Secret key for signing authentication tokens.
        ACCESS_TOKEN_EXPIRE_MINUTES (int): Expiry duration of access tokens (in minutes).
        REFRESH_TOKEN_EXPIRE_DAYS (int): Expiry duration of refresh tokens (in days).
        BACKEND_CORS_ORIGINS (str | list[str]): Allowed CORS origins.
        DOCKERIZED (bool): Whether the application runs in a Docker container.
        DATABASE_TYPE (Literal): Type of database (`sqlite`, `postgres`, `mysql`).
        DB_HOST (str): Database host address.
        DB_PORT (int): Database connection port.
        DB_USER (str): Database username.
        DB_PASSWORD (str): Database password.
        DB_NAME (str): Database name.
        SMTP settings: SMTP configurations for sending emails.
        FIRST_SUPERUSER (str): Default superuser email.
        FIRST_SUPERUSER_PASSWORD (str): Default superuser password.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # API Configuration
    PROJECT_NAME: str = Field("EduScale Engine", description="Name of the project")
    ROUTE_PREFIX: str = Field("/api", description="Base API route prefix")
    API_VERSIONS: str | List[str] = Field(default="v1,v2", description="Supported API versions (comma-separated or JSON array)")
    DEFAULT_API_VERSION: str = Field("v1", description="Default API version")

    BACKEND_HOST: str = Field("http://localhost:8000", description="Backend API host URL")
    FRONTEND_HOST: str = Field("http://localhost:5173", description="Frontend application URL")
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    LOG_LEVEL: Literal["debug", "info", "warning", "error", "critical", "production"] = "warning"

    # Security & Authentication
    PASSWORD_SECURITY_ALGORITHM: str = Field(default="HS256", description="Algorithm for password security")
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32), description="Secret key for JWT tokens")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 days
    REFRESH_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32),
                                    description="Secret key for refresh tokens")

    # CORS Settings
    BACKEND_CORS_ORIGINS: str | list[str] = Field("", description="Allowed CORS origins")

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def parse_cors_string(cls, v: Any) -> list[str]:
        """
        Parses a comma-separated string into a list of CORS origins.

        Args:
            v (Any): Input value from environment.

        Returns:
            list[str]: A list of CORS origins.

        Raises:
            ValueError: If the format is invalid.
        """
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(f"Invalid CORS origin format: {v}")

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def normalize_environment(cls, v: Any) -> str:
        """Normalize environment value (case-insensitive, map development->local)."""
        if isinstance(v, str):
            v_lower = v.lower().strip()
            if v_lower == "development":
                return "local"
            if v_lower in ["local", "staging", "production"]:
                return v_lower
        return "local"
    
    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def normalize_log_level(cls, v: Any) -> str:
        """Normalize log level value (case-insensitive)."""
        if isinstance(v, str):
            v_lower = v.lower().strip()
            if v_lower in ["debug", "info", "warning", "error", "critical", "production"]:
                return v_lower
        return "warning"
    
    @field_validator("API_VERSIONS", mode="before")
    @classmethod
    def parse_api_versions(cls, v: Any) -> Any:
        """
        Parses API versions from environment variable.
        Supports JSON array, comma-separated string, or already a list.

        Args:
            v (Any): Input value from environment.

        Returns:
            Any: A list of API versions (will be validated as List[str] after).
        """
        # Handle None or empty values - return default
        if v is None:
            return ["v1", "v2"]
        
        # Already a list - validate and return
        if isinstance(v, list):
            return [str(item).strip() for item in v if item]
        
        # String value - handle various formats
        if isinstance(v, str):
            v = v.strip()
            # Empty string
            if not v:
                return ["v1", "v2"]
            
            # Try JSON first (if it looks like JSON)
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        result = [str(item).strip() for item in parsed if item]
                        if result:
                            return result
                except (json.JSONDecodeError, TypeError, ValueError):
                    # If JSON parsing fails, fall through to comma-separated
                    pass
            
            # Fall back to comma-separated
            parts = [i.strip() for i in v.split(",") if i.strip()]
            if parts:
                return parts
        
        # Default fallback
        return ["v1", "v2"]
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def api_versions_list(self) -> List[str]:
        """
        Returns API_VERSIONS as a list, handling both string and list formats.
        
        Returns:
            List[str]: A list of API version strings.
        """
        if isinstance(self.API_VERSIONS, list):
            return [str(item).strip() for item in self.API_VERSIONS if item]
        elif isinstance(self.API_VERSIONS, str):
            # Parse comma-separated or JSON
            v = self.API_VERSIONS.strip()
            if not v:
                return ["v1", "v2"]
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if item]
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass
            # Comma-separated
            parts = [i.strip() for i in v.split(",") if i.strip()]
            if parts:
                return parts
        return ["v1", "v2"]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> List[str]:
        """
        Ensures CORS settings return a valid list.

        Returns:
            list[str]: List of allowed CORS origins.
        """
        return list(set(self.BACKEND_CORS_ORIGINS + [self.FRONTEND_HOST, self.BACKEND_HOST]))

    # Detect Docker Environment
    DOCKERIZED: bool = Field(default=False, description="Detects if the app runs inside Docker")

    # Database Configuration
    DATABASE_TYPE: Literal["sqlite", "postgres", "mysql"] = "postgres"
    DB_HOST: str = Field(default="localhost", description="Database host")
    DB_PORT: int = Field(default=5432, description="Database port")
    DB_USER: str = "swx_user"
    DB_PASSWORD: str = "changeme"
    DB_NAME: str = "swx_db"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Generates a dynamic database connection URL.

        Returns:
            str: The full database connection string.
        """
        # Use "db" as hostname if in Docker, otherwise use DB_HOST from env
        # In Docker Compose, the database service is named "db"
        # Check if we're in Docker by looking for common Docker indicators
        import os
        is_docker = (
            os.path.exists("/.dockerenv") or
            os.environ.get("DOCKERIZED", "").lower() in ("true", "1", "yes") or
            self.DOCKERIZED
        )
        
        # Use "db" as hostname if in Docker, otherwise use DB_HOST from env
        db_host = "db" if is_docker else self.DB_HOST
        # Fallback: if DB_HOST is explicitly set to "db", use it regardless of DOCKERIZED
        if self.DB_HOST == "db":
            db_host = "db"

        if self.DATABASE_TYPE == "sqlite":
            return f"sqlite:///./{self.DB_NAME}.db"
        elif self.DATABASE_TYPE == "mysql":
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{db_host}:{self.DB_PORT}/{self.DB_NAME}"
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{db_host}:{self.DB_PORT}/{self.DB_NAME}"

    # Email Configuration
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str | None = None
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @property
    def emails_enabled(self) -> bool:
        """
        Determines if email sending is enabled.

        Returns:
            bool: True if email configuration is set correctly, otherwise False.
        """
        return all([self.SMTP_HOST, self.SMTP_USER, self.SMTP_PASSWORD, self.EMAILS_FROM_EMAIL])

    # Superuser Configuration
    FIRST_SUPERUSER: str = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "securepassword"

    # 🔹 Social Login Flags
    ENABLE_GOOGLE_LOGIN: bool = True
    ENABLE_FACEBOOK_LOGIN: bool = True

    # 🔹 Google OAuth
    GOOGLE_AUTH_URL: str | None = None
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None
    GOOGLE_SCOPE: str = "openid email profile"

    # 🔹 Facebook OAuth
    FACEBOOK_AUTH_URL: str | None = None
    FACEBOOK_CLIENT_ID: str | None = None
    FACEBOOK_CLIENT_SECRET: str | None = None
    FACEBOOK_REDIRECT_URI: str | None = None
    FACEBOOK_SCOPE: str = "email,public_profile"

    # 🔹 Sentry
    SENTRY_DSN: str | None = None

    # 🔹 Transport / Golemio
    GOLEMIO_API_KEY: str | None = None
    OTP_URL: str | None = None
    NOMINATIM_URL: str | None = None
    STOPS_FILE: str = "stops.txt"


# Instantiate settings
settings = Settings()
