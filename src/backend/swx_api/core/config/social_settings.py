"""
Social Login Settings
---------------------
This module defines the configuration settings for social authentication.

Features:
- Enables or disables social login options.
- Supports Google and Facebook OAuth authentication.
- Loads credentials from environment variables.

Schemas:
- `SocialLoginSettings`: Configures social login and OAuth settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SocialLoginSettings(BaseSettings):
    """
    Configuration settings for social authentication.

    Attributes:
        ENABLE_SOCIAL_LOGIN (bool): Enables or disables social login globally.
        ENABLE_GOOGLE_LOGIN (bool): Enables Google authentication.
        ENABLE_FACEBOOK_LOGIN (bool): Enables Facebook authentication.
        ENABLE_GITHUB_LOGIN (bool): Enables GitHub authentication.

        GOOGLE_AUTH_URL (Optional[str]): Google OAuth authorization URL.
        GOOGLE_CLIENT_ID (Optional[str]): Google OAuth client ID.
        GOOGLE_CLIENT_SECRET (Optional[str]): Google OAuth client secret.
        GOOGLE_REDIRECT_URI (Optional[str]): Redirect URI for Google authentication.
        GOOGLE_SCOPE (Optional[str]): Google OAuth scope.

        FACEBOOK_AUTH_URL (Optional[str]): Facebook OAuth authorization URL.
        FACEBOOK_CLIENT_ID (Optional[str]): Facebook OAuth client ID.
        FACEBOOK_CLIENT_SECRET (Optional[str]): Facebook OAuth client secret.
        FACEBOOK_REDIRECT_URI (Optional[str]): Redirect URI for Facebook authentication.
        FACEBOOK_SCOPE (Optional[str]): Facebook OAuth scope.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    # Enable/Disable Social Login
    ENABLE_SOCIAL_LOGIN: bool = Field(default=True, description="Enables or disables social login globally.")
    ENABLE_GOOGLE_LOGIN: bool = Field(default=True, description="Enables Google authentication.")
    ENABLE_FACEBOOK_LOGIN: bool = Field(default=False, description="Enables Facebook authentication.")
    ENABLE_GITHUB_LOGIN: bool = Field(default=False, description="Enables GitHub authentication.")

    # Google OAuth Settings
    GOOGLE_AUTH_URL: str | None = Field(default=None, env="GOOGLE_AUTH_URL",
                                        description="Google OAuth authorization URL.")
    GOOGLE_CLIENT_ID: str | None = Field(default=None, env="GOOGLE_CLIENT_ID", description="Google OAuth client ID.")
    GOOGLE_CLIENT_SECRET: str | None = Field(default=None, env="GOOGLE_CLIENT_SECRET",
                                             description="Google OAuth client secret.")
    GOOGLE_REDIRECT_URI: str | None = Field(default=None, env="GOOGLE_REDIRECT_URI",
                                            description="Redirect URI for Google authentication.")
    GOOGLE_SCOPE: str | None = Field(default=None, env="GOOGLE_SCOPE", description="Google OAuth scope.")

    # Facebook OAuth Settings
    FACEBOOK_AUTH_URL: str | None = Field(default=None, env="FACEBOOK_AUTH_URL",
                                          description="Facebook OAuth authorization URL.")
    FACEBOOK_CLIENT_ID: str | None = Field(default=None, env="FACEBOOK_CLIENT_ID",
                                           description="Facebook OAuth client ID.")
    FACEBOOK_CLIENT_SECRET: str | None = Field(default=None, env="FACEBOOK_CLIENT_SECRET",
                                               description="Facebook OAuth client secret.")
    FACEBOOK_REDIRECT_URI: str | None = Field(default=None, env="FACEBOOK_REDIRECT_URI",
                                              description="Redirect URI for Facebook authentication.")
    FACEBOOK_SCOPE: str | None = Field(default=None, env="FACEBOOK_SCOPE", description="Facebook OAuth scope.")


# Instantiate settings
social_settings = SocialLoginSettings()
