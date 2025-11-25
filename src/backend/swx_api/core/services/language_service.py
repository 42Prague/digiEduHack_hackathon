"""
Language Service
----------------
This module provides a service layer for managing language resources.

Features:
- Acts as an interface between the repository and API endpoints.
- Implements business logic for language resource operations.

Methods:
- `retrieve_all_language_resources()`: Fetch all language resources.
- `retrieve_all_bulk_language_resources()`: Retrieve translations for multiple languages.
- `retrieve_language_by_id()`: Fetch a single language resource by its unique ID.
- `retrieve_by_language_code()`: Fetch all translations for a specific language.
- `retrieve_language_by_code_and_key()`: Fetch a specific translation key-value pair.
- `create_new_language()`: Insert a new language record.
- `update_existing_language()`: Modify an existing language record.
- `delete_existing_language()`: Remove a language record.
"""

import uuid
from swx_api.core.database.db import SessionDep
from swx_api.core.repositories.language_repository import LanguageRepository
from swx_api.core.models.language import LanguageCreate, LanguageUpdate


class LanguageService:
    """
    Service layer for handling language-related operations.

    Provides an abstraction layer between the API routes and the repository,
    ensuring business logic is properly handled.
    """

    @staticmethod
    def retrieve_all_language_resources(
        db: SessionDep, skip: int = 0, limit: int = 100
    ):
        """
        Retrieve all language resources with pagination.

        Args:
            db (SessionDep): Database session dependency.
            skip (int): Number of records to skip for pagination.
            limit (int): Maximum number of records to return.

        Returns:
            List[Language]: A list of language records.
        """
        return LanguageRepository.retrieve_all_language_resources(
            db, skip=skip, limit=limit
        )

    @staticmethod
    def retrieve_all_bulk_language_resources(db: SessionDep, languages: list[str]):
        """
        Retrieve translations for multiple languages in bulk.

        Args:
            db (SessionDep): Database session dependency.
            languages (list[str]): List of language codes to retrieve translations for.

        Returns:
            dict: A dictionary where the keys are language codes and the values are
                  dictionaries containing translation key-value pairs.
        """
        return LanguageRepository.retrieve_all_bulk_language_resources(db, languages)

    @staticmethod
    def retrieve_language_by_id(db: SessionDep, id: uuid.UUID):
        """
        Retrieve a single language resource by its unique ID.

        Args:
            db (SessionDep): Database session dependency.
            id (uuid.UUID): The unique identifier of the language record.

        Returns:
            Language | None: The matching language record, or None if not found.
        """
        return LanguageRepository.retrieve_language_by_id(db, id)

    @staticmethod
    def retrieve_by_language_code(db: SessionDep, language_code: str):
        """
        Retrieve all translations for a given language code.

        Args:
            db (SessionDep): Database session dependency.
            language_code (str): The language code (e.g., "en", "cs").

        Returns:
            List[Language]: A list of language records for the specified language code.
        """
        return LanguageRepository.retrieve_by_language_code(db, language_code)

    @staticmethod
    def retrieve_language_by_code_and_key(db: SessionDep, language_code: str, key: str):
        """
        Retrieve a specific translation entry by its language code and key.

        Args:
            db (SessionDep): Database session dependency.
            language_code (str): The language code (e.g., "en").
            key (str): The translation key.

        Returns:
            Language | None: The matching language record, or None if not found.
        """
        return LanguageRepository.retrieve_language_by_code_and_key(
            db, language_code, key
        )

    @staticmethod
    def create_new_language(db: SessionDep, data: LanguageCreate):
        """
        Create a new language resource in the database.

        Args:
            db (SessionDep): Database session dependency.
            data (LanguageCreate): The data for the new language record.

        Returns:
            Language: The newly created language record.
        """
        return LanguageRepository.create_new_language(db, data)

    @staticmethod
    def update_existing_language(db: SessionDep, id: uuid.UUID, data: LanguageUpdate):
        """
        Update an existing language resource.

        Args:
            db (SessionDep): Database session dependency.
            id (uuid.UUID): The unique identifier of the language record.
            data (LanguageUpdate): The updated data.

        Returns:
            Language | None: The updated language record, or None if not found.
        """
        return LanguageRepository.update_existing_language(db, id, data)

    @staticmethod
    def delete_existing_language(db: SessionDep, id: uuid.UUID):
        """
        Delete an existing language resource from the database.

        Args:
            db (SessionDep): Database session dependency.
            id (uuid.UUID): The unique identifier of the language record.

        Returns:
            bool: True if the record was successfully deleted, False if not found.
        """
        return LanguageRepository.delete_existing_language(db, id)

    @staticmethod
    def create_bulk_languages(db: SessionDep, items: list[LanguageCreate]):
        """
        Create multiple language records in bulk.

        Args:
            db (SessionDep): Database session dependency.
            items (list[LanguageCreate]): List of language creation data.

        Returns:
            List[Language]: Created language records.
        """
        return LanguageRepository.create_bulk_languages(db, items)
