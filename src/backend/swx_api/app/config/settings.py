"""
Application Settings Configuration
----------------------------------
This module defines the global settings for EduScale Engine.

It extends the base CoreSettings class from swx_api/core/config/settings.
"""

from pydantic import Field
from pydantic_settings import SettingsConfigDict
from swx_api.core.config.settings import Settings as CoreSettings


class AppSettings(CoreSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )
    USE_NGROK: bool = Field(default=False)
    NGROK_AUTH_TOKEN: str = Field(default="")
    PROJECT_VERSION: str = Field(default="1.0")

    APP_PORT: int = Field(default=8000)
    REDIS_URL: str = Field(default="REDIS_URL")
    REDIS_HOST: str = Field(default="czfb-redis")
    REDIS_PORT: int = Field(default="6379")
    SESSION_SECRET_KEY: str = Field(default="DLgd15zT1qP4YYo5PEkJ_4DPPMi7iXSfp3vDTns1Xi")
    SESSION_COOKIE_NAME: str = Field(default="session_id")
    SESSION_TIMEOUT: int = Field(default=900)


# Create global settings instance
app_settings = AppSettings()
