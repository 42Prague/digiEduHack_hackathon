"""
Refresh Token Model
-------------------
This module defines the RefreshToken model used for handling authentication tokens.

Features:
- Stores refresh tokens securely.
- Tracks token expiration and user association.
- Supports creating, updating, and publicly exposing refresh tokens.

Schemas:
- `RefreshToken`: Main database model.
- `RefreshTokenCreate`: Schema for creating refresh tokens.
- `RefreshTokenUpdate`: Schema for updating refresh tokens.
- `RefreshTokenPublic`: Public representation of the refresh token.
"""

from typing import Optional
import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from swx_api.core.models.base import Base


class RefreshTokenBase(Base):
    """
    Base model for refresh tokens.

    Attributes:
        token (str): The refresh token.
        expires_at (datetime): Expiration time of the token.
        created_at (datetime): Timestamp of when the token was issued.
    """

    token: str = Field(..., nullable=False)  # Required refresh token
    expires_at: datetime = Field(nullable=False)  # Expiry timestamp
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # Defaults to current UTC time


class RefreshToken(RefreshTokenBase, table=True):
    """
    RefreshToken model for storing issued refresh tokens.

    Attributes:
        id (uuid.UUID): Unique identifier for each token.
        user_email (str): Email associated with the token.
    """

    __tablename__ = "refresh_token"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_email: str = Field(index=True)  # Indexed for efficient lookups


class RefreshTokenCreate(RefreshTokenBase):
    """
    Schema for creating a new refresh token.

    Inherits:
        RefreshTokenBase: Base fields for refresh tokens.
    """
    pass


class RefreshTokenUpdate(RefreshTokenBase):
    """
    Schema for updating an existing refresh token.

    Inherits:
        RefreshTokenBase: Base fields for refresh tokens.
    """
    pass


class RefreshTokenPublic(RefreshToken):
    """
    Public schema for exposing refresh tokens.

    Inherits:
        RefreshToken: Main refresh token model.
    """
    pass
