"""
Language Routes
---------------
This module defines the API routes for managing language resources.

Features:
- Provides endpoints for retrieving, creating, updating, and deleting language records.
- Implements pagination and filtering for optimized queries.
- Enforces admin-level authentication for modification routes.

Routes:
- `GET /utils/language/`: Retrieve all language records.
- `GET /utils/language/bulk`: Retrieve multiple language records in bulk.
- `GET /utils/language/{id}`: Retrieve a single language record by ID.
- `GET /utils/language/code/{language_code}`: Retrieve all records for a given language code.
- `GET /utils/language/{language_code}/{key}`: Retrieve a specific translation by language code and key.
- `POST /utils/language/`: Create a new language record (Admin Only).
- `POST /utils/language/bulk`: Create multiple language records (Admin Only).
- `PUT /utils/language/{id}`: Update an existing language record (Admin Only).
- `DELETE /utils/language/{id}`: Delete an existing language record (Admin Only).
"""

import uuid
from typing import List, Dict, Any

from fastapi import APIRouter, Request, Depends, Query

from swx_api.core.controllers.language_controller import LanguageController
from swx_api.core.database.db import SessionDep
from swx_api.core.models.common import Message
from swx_api.core.models.language import (
    LanguageCreate,
    LanguageUpdate,
    LanguagePublic,
    LanguageCreateSchema,
    BulkLanguageResponse,
)
from swx_api.core.security.dependencies import get_current_active_superuser

from swx_api.core.models.common import PaginatedResponse

# Initialize API router with a prefix for language utilities
router = APIRouter(prefix="/utils/language")


@router.get(
    "/",
    response_model=PaginatedResponse[LanguagePublic],
    summary="Get all language resources",
    description="Retrieve all language resources with optional pagination.",
    operation_id="get_all_languages",
)
def get_all_language(
        request: Request,
        db: SessionDep,
        skip: int = Query(0, description="Number of items to skip."),
        limit: int = Query(100, description="Maximum number of items to return."),
):
    """
    Retrieve all language resources with pagination.

    Args:
        request (Request): The HTTP request object.
        db (SessionDep): Database session dependency.
        skip (int): Number of records to skip for pagination.
        limit (int): Maximum number of records to return.

    Returns:
        list[LanguagePublic]: A list of language records.
    """
    return LanguageController.retrieve_all_language_resources(
        request, db, skip=skip, limit=limit
    )


@router.get(
    "/bulk",
    response_model=Dict[str, Dict[str, str]],
    summary="Retrieve all language translations in bulk",
    description="Retrieve multiple language translations at once by specifying the required languages.",
    operation_id="get_bulk_language_translations",
)
def get_language_by_all_bulk(db: SessionDep, languages: List[str] = Query(...)):
    """
    Retrieve translations for multiple languages in bulk.

    Args:
        db (SessionDep): Database session dependency.
        languages (list[str]): List of language codes to retrieve translations for.

    Returns:
        dict: A dictionary where each language code maps to its corresponding translations.
    """
    return LanguageController.retrieve_all_bulk_language_resources(db, languages)


@router.get(
    "/code/{language_code}",
    response_model=List[LanguagePublic],
    summary="Retrieve language resources by language code",
    description="Fetch all language resources that match a given language code.",
    operation_id="get_languages_by_code",
)
def get_language_by_code(request: Request, language_code: str, db: SessionDep):
    """
    Retrieve all language resources for a given language code.

    Args:
        request (Request): The HTTP request object.
        language_code (str): The language code (e.g., "en").
        db (SessionDep): Database session dependency.

    Returns:
        list[LanguagePublic]: A list of language records for the specified language code.
    """
    return LanguageController.retrieve_by_language_code(request, language_code, db)


@router.get(
    "/{language_code}/{key}",
    response_model=LanguagePublic,
    summary="Retrieve translation by language code and key",
    description="Fetch a single language translation using both language code and key.",
    operation_id="get_language_by_code_and_key",
)
def get_language_by_code_and_key(
        request: Request, language_code: str, key: str, db: SessionDep
):
    """
    Retrieve a specific translation entry by its language code and key.

    Args:
        request (Request): The HTTP request object.
        language_code (str): The language code (e.g., "en").
        key (str): The translation key.
        db (SessionDep): Database session dependency.

    Returns:
        LanguagePublic: The matching language record.
    """
    return LanguageController.retrieve_language_by_code_and_key(
        request, db, language_code, key
    )


@router.get(
    "/{id}",
    response_model=LanguagePublic,
    summary="Retrieve language resource by ID",
    description="Fetch a single language resource using its unique identifier.",
    operation_id="get_language_by_id",
)
def get_language_by_id(request: Request, id: uuid.UUID, db: SessionDep):
    """
    Retrieve a single language resource by its unique ID.

    Args:
        request (Request): The HTTP request object.
        id (uuid.UUID): The unique identifier of the language record.
        db (SessionDep): Database session dependency.

    Returns:
        LanguagePublic: The language record matching the provided ID.
    """
    return LanguageController.retrieve_language_by_id(request, id, db)


@router.post(
    "/",
    response_model=LanguagePublic,
    status_code=201,
    summary="Create a new language record (Admin Only)",
    description="Allows an administrator to create a new language translation entry.",
    operation_id="create_language",
)
def create_language(request: Request, data: LanguageCreate, db: SessionDep):
    """
    Create a new language resource.

    Args:
        request (Request): The HTTP request object.
        data (LanguageCreate): The language data to be created.
        db (SessionDep): Database session dependency.

    Returns:
        LanguagePublic: The newly created language record.
    """
    return LanguageController.create_new_language(request, data, db)


@router.post(
    "/bulk",
    response_model=Message,
    status_code=201,
    summary="Create multiple language records in bulk (Admin Only)",
    description="Allows an administrator to create multiple language records at once.",
    operation_id="create_bulk_languages",
)
def create_bulk_languages(request: Request, data: List[LanguageCreateSchema], db: SessionDep) -> Any:
    """
    Create multiple language resources in bulk.

    Args:
        request (Request): The HTTP request object.
        data (list[LanguageCreateSchema]): A list of language data to be created.
        db (SessionDep): Database session dependency.

    Returns:
        Message: A response message indicating the operation status.
    """
    return LanguageController.create_new_bulk_language(request, data, db)


@router.put(
    "/{id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=LanguagePublic,
    summary="Update an existing language record (Admin Only)",
    description="Allows an administrator to modify an existing language translation.",
    operation_id="update_language",
)
def update_language(request: Request, id: uuid.UUID, data: LanguageUpdate, db: SessionDep):
    """
    Update an existing language resource.

    Args:
        request (Request): The HTTP request object.
        id (uuid.UUID): The unique identifier of the language record.
        data (LanguageUpdate): The updated data.
        db (SessionDep): Database session dependency.

    Returns:
        LanguagePublic: The updated language record.
    """
    return LanguageController.update_existing_language(request, id, data, db)


@router.delete(
    "/{id}",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=204,
    summary="Delete a language record (Admin Only)",
    description="Allows an administrator to remove a language record permanently.",
    operation_id="delete_language",
)
def delete_language(request: Request, id: uuid.UUID, db: SessionDep):
    """
    Delete an existing language resource.

    Args:
        request (Request): The HTTP request object.
        id (uuid.UUID): The unique identifier of the language record.
        db (SessionDep): Database session dependency.

    Returns:
        None: If the deletion is successful.
    """
    return LanguageController.delete_existing_language(request, id, db)
