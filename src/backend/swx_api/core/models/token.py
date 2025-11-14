"""
Token Model
-----------
This module defines token-related schemas used for authentication.

Features:
- Defines access and refresh token schemas.
- Supports different authentication providers.
- Includes request schemas for token refreshing and password resets.

Schemas:
- `Token`: Represents an access token with an optional refresh token.
- `TokenPayload`: Stores user authentication payload data.
- `TokenRefreshRequest`: Handles refresh token requests.
- `NewPassword`: Schema for resetting passwords.
- `LogoutRequest`: Schema for logout operations.
"""

from sqlmodel import SQLModel, Field
from swx_api.core.models.base import Base


class TokenBase(Base):
    """
    Base schema for authentication tokens.

    Attributes:
        access_token (str): The access token issued to the user.
        refresh_token (str | None): The refresh token for session continuation.
    """

    access_token: str
    refresh_token: str | None = None


class Token(TokenBase):
    """
    Schema for authentication token responses.

    Attributes:
        token_type (str): The type of token (default: 'bearer').
    """

    token_type: str = "bearer"


class TokenPayload(SQLModel):
    """
    Schema for parsing authentication tokens.

    Attributes:
        sub (str): User email or user ID.
        auth_provider (str): Authentication provider (e.g., 'local', 'google', 'facebook').
    """

    sub: str
    auth_provider: str = "local"


class TokenRefreshRequest(SQLModel):
    """
    Request schema for refreshing an authentication token.

    Attributes:
        refresh_token (str): The refresh token issued to the user.
    """

    refresh_token: str


class NewPassword(SQLModel):
    """
    Schema for resetting a user's password.

    Attributes:
        token (str): The reset token for password recovery.
        new_password (str): The new password (8-40 characters).
    """

    token: str
    new_password: str = Field(min_length=8, max_length=40)


class RefreshTokenRequest(SQLModel):
    """
    Request schema for obtaining a new refresh token.

    Attributes:
        refresh_token (str): The current refresh token.
    """

    refresh_token: str


class LogoutRequest(SQLModel):
    """
    Request schema for logging out a user.

    Attributes:
        refresh_token (str): The refresh token to be invalidated.
    """

    refresh_token: str
