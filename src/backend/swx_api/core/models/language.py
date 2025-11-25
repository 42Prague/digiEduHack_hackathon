"""
Language Model
--------------
This module defines the Language model used for managing application translations.

Features:
- Stores translations for different languages.
- Supports bulk import of translations.
- Includes different schemas for creating, updating, and retrieving translations.

Schemas:
- `Language`: Main database model.
- `LanguageCreate`: Schema for creating new translations.
- `LanguageUpdate`: Schema for updating translations.
- `LanguagePublic`: Public representation of the Language model.
- `LanguageCreateSchema`: Schema with validation constraints.
- `BulkLanguageResponse`: Response format for bulk inserts.
"""

import uuid
from typing import Optional, List
from sqlmodel import SQLModel, Field
from swx_api.core.models.base import Base


class LanguageBase(Base):
    """
    Base model for language translations.

    Attributes:
        language_code (str): The language code (e.g., 'en', 'cs').
        key (str): The translation key (e.g., 'welcome_message').
        value (str): The translated text.
    """

    language_code: str = Field(max_length=5, index=True)  # e.g., 'en', 'cs'
    key: str = Field(max_length=255, index=True)  # e.g., 'welcome_message'
    value: str = Field()  # Translated text


class Language(LanguageBase, table=True):
    """
    Language model for storing translations in the database.

    Attributes:
        id (uuid.UUID): Unique identifier for each translation entry.
    """

    __tablename__ = "language"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class LanguageCreate(LanguageBase):
    """
    Schema for creating new language translations.
    """
    pass


class LanguageUpdate(LanguageBase):
    """
    Schema for updating existing language translations.

    Attributes:
        language_code (Optional[str]): New language code (if changed).
        key (Optional[str]): New translation key (if changed).
        value (Optional[str]): New translation value (if changed).
    """

    language_code: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None


class LanguagePublic(Language):
    """
    Public representation of a Language entry.

    Attributes:
        id (uuid.UUID): Unique identifier.
    """

    pass


class LanguageCreateSchema(LanguageBase):
    """
    Schema with validation constraints for creating a new translation.

    Attributes:
        language_code (str): Language code (e.g., 'en', 'cs'), min length 2.
        key (str): Translation key, min length 1.
        value (str): Translation value, min length 1.
    """

    language_code: str = Field(
        ..., min_length=2, max_length=5, description="Language code (e.g., 'en', 'cs')"
    )
    key: str = Field(..., min_length=1, max_length=255, description="Translation key")
    value: str = Field(..., min_length=1, description="Translation value")


class BulkLanguageResponse(LanguageBase):
    """
    Response schema for bulk language insertions.

    Attributes:
        message (str): Status message.
        inserted_count (int): Number of successfully inserted translations.
        failed_keys (List[str]): List of failed keys.
    """

    message: str
    inserted_count: int
    failed_keys: List[str]
