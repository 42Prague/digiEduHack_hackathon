"""
Language Repository
-------------------
This module provides database interaction methods for managing language resources.

Features:
- Retrieve single or multiple language resources.
- Create, update, and delete language records.
- Support for bulk retrieval of translations.

Methods:
- `retrieve_all_language_resources()`: Fetch all language resources with pagination.
- `retrieve_all_bulk_language_resources()`: Retrieve translations for multiple languages.
- `retrieve_language_by_id()`: Fetch a single language record by its unique ID.
- `retrieve_language_by_code_and_key()`: Fetch a language entry by language code and key.
- `retrieve_by_language_code()`: Fetch all language records by a specific language code.
- `create_new_language()`: Insert a new language record into the database.
- `update_existing_language()`: Modify an existing language record.
- `delete_existing_language()`: Remove a language record from the database.
"""

import uuid
from sqlmodel import select
from swx_api.core.database.db import SessionDep
from swx_api.core.models.language import Language, LanguageCreate, LanguageUpdate


class LanguageRepository:
    """
    Database repository for handling language-related operations.

    Provides CRUD (Create, Read, Update, Delete) functionality for language records.
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
        query = select(Language).offset(skip).limit(limit)
        return db.exec(query).all()

    @staticmethod
    def retrieve_all_bulk_language_resources(db: SessionDep, languages: list[str]):
        """
        Retrieve all language resources for multiple languages in bulk.

        Args:
            db (SessionDep): Database session dependency.
            languages (list[str]): List of language codes to retrieve translations for.

        Returns:
            dict: A dictionary where the keys are language codes and the values are
                  dictionaries containing translation key-value pairs.
        """
        translations_dict = {}
        for lang in languages:
            translations = LanguageRepository.retrieve_by_language_code(db, lang)
            # Build a dictionary: key is the translation key, value is its translation value
            translations_dict[lang] = {t.key: t.value for t in translations}
        return translations_dict

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
        return db.get(Language, id)

    @staticmethod
    def retrieve_language_by_code_and_key(db: SessionDep, language_code: str, key: str):
        """
        Retrieve a single language resource by its language code and translation key.

        Args:
            db (SessionDep): Database session dependency.
            language_code (str): The language code (e.g., "en").
            key (str): The translation key.

        Returns:
            Language | None: The matching language record, or None if not found.
        """
        query = select(Language).where(
            Language.language_code == language_code, Language.key == key
        )
        return db.exec(query).one()

    @staticmethod
    def retrieve_by_language_code(db: SessionDep, language_code: str):
        """
        Retrieve all language resources by a given language code.

        Args:
            db (SessionDep): Database session dependency.
            language_code (str): The language code (e.g., "en", "cs").

        Returns:
            List[Language]: A list of language records for the specified language code.
        """
        query = select(Language).where(Language.language_code == language_code)
        return db.exec(query).all()

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
        obj = Language(**data.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

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
        obj = db.get(Language, id)
        if not obj:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

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
        obj = db.get(Language, id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True

    @staticmethod
    def create_bulk_languages(db: SessionDep, items: list[LanguageCreate]):
        """
        Insert multiple language records, skipping duplicates based on (language_code, key).

        Args:
            db (SessionDep): Database session dependency.
            items (list[LanguageCreate]): List of new language entries.

        Returns:
            List[Language]: Successfully created language records.
        """
        # Fetch all existing (language_code, key) pairs
        existing_keys = db.exec(
            select(Language.language_code, Language.key)
        ).all()
        existing_set = {(lang, key) for lang, key in existing_keys}

        # Filter only new entries
        unique_items = [
            item for item in items
            if (item.language_code, item.key) not in existing_set
        ]

        objs = [Language(**item.model_dump()) for item in unique_items]
        db.add_all(objs)
        db.commit()
        for obj in objs:
            db.refresh(obj)
        return objs
