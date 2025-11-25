"""
User Model
----------
This module defines the User model and related schemas.

Features:
- Stores user authentication details.
- Supports multiple authentication providers.
- Includes schemas for user creation, updates, and password management.

Schemas:
- `User`: Represents a stored user in the database.
- `UserCreate`: Handles user registration.
- `UserUpdate`: Schema for updating user information.
- `UserPublic`: Public representation of user data.
- `UsersPublic`: Response schema for multiple users.
- `UserUpdatePassword`: Schema for changing user passwords.
- `UserNewPassword`: Schema for setting a new password.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import EmailStr
from sqlalchemy import Column, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel, Relationship


from swx_api.core.models.base import Base


class UserBase(Base):
    """
    Base model for shared user fields.

    Attributes:
        email (EmailStr): Unique email address.
        is_active (bool): Indicates if the user account is active.
        full_name (Optional[str]): The user's full name (optional).
        preferred_language (str): Preferred language for UI interaction.
    """

    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    full_name: Optional[str] = Field(default=None, max_length=255)
    preferred_language: str = Field(
        default="en", sa_column=Column(String(5), server_default=text("'en'"))
    )


class User(UserBase, table=True):
    """
    Database model representing a user.

    Attributes:
        id (uuid.UUID): Unique user identifier.
        hashed_password (Optional[str]): Hashed password for authentication.
        auth_provider (str): The authentication provider (default: 'local').
        provider_id (Optional[str]): External authentication provider ID.
        avatar_url (Optional[str]): URL to the user's profile picture.
        identifier (str): Unique user identifier used by Chainlit.
        metadata (dict): JSON metadata for custom attributes.
        createdAt (str): Timestamp when the user was created.
    """

    __tablename__ = "user"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: Optional[str] = Field(default=None, max_length=255)
    auth_provider: str = Field(default="local", max_length=50)
    provider_id: Optional[str] = Field(default=None, unique=True, max_length=255)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # Defaults to current UTC time
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # Defaults to current UTC time



class UserCreate(SQLModel):
    """
    Schema for creating a new user.

    Attributes:
        email (EmailStr): User email (required).
        password (str): Password (8-40 characters).
        full_name (Optional[str]): User's full name (optional).
        preferred_language (Optional[str]): Preferred language (default: 'en').
    """

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: Optional[str] = Field(default=None, max_length=255)
    preferred_language: Optional[str] = Field(default="en", max_length=3)


class UserUpdate(SQLModel):
    """
    Schema for updating an existing user.

    Attributes:
        email (Optional[EmailStr]): New email (if updating).
        password (Optional[str]): New password (if updating).
        preferred_language (Optional[str]): Updated preferred language.
    """

    email: Optional[EmailStr] = Field(default=None, max_length=255)
    password: Optional[str] = Field(default=None, min_length=8, max_length=40)
    preferred_language: Optional[str] = Field(default="en", max_length=3)


class UserPublic(UserBase):
    """
    Schema for publicly visible user data.

    Attributes:
        id (uuid.UUID): Unique user identifier.
        auth_provider (str): Authentication provider (e.g., 'local', 'google').
        avatar_url (Optional[str]): Profile picture URL.
        preferred_language (str): User's selected language.
    """

    id: uuid.UUID
    auth_provider: str
    avatar_url: Optional[str] = None
    preferred_language: str

    class Config:
        from_attributes = True


class UsersPublic(SQLModel):
    """
    Schema for a list of public users.

    Attributes:
        data (list[UserPublic]): List of user data.
        count (int): Total number of users in the response.
    """

    data: list[UserPublic]
    count: int


class UserUpdatePassword(SQLModel):
    """
    Schema for updating a user's password.

    Attributes:
        current_password (Optional[str]): User's current password.
        new_password (Optional[str]): New password (8-40 characters).
    """

    current_password: Optional[str] = Field(default=None, max_length=255)
    new_password: Optional[str] = Field(default=None, min_length=8, max_length=40)


class UserNewPassword(SQLModel):
    """
    Schema for setting a new password.

    Attributes:
        token (Optional[str]): Reset token.
        new_password (Optional[str]): New password (8-40 characters).
    """

    token: Optional[str] = Field(default=None, max_length=255)
    new_password: Optional[str] = Field(default=None, min_length=8, max_length=40)

class PasswordRecoverRequest(SQLModel):
    """
    Schema for initiating a password recovery.

    Attributes:
        email (EmailStr): The user's email address for sending the reset link.
    """
    email: EmailStr
