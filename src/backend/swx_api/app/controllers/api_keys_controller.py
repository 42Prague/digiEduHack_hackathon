# Controller for handling API key operations.
import uuid
from typing import List

from fastapi import HTTPException, Request, Depends
from swx_api.app.models.api_keys import (
    ApiKeysCreate,
    ApiKeysUpdate,
    ApiKeysRead,
    ApiKeysReadWithKey,
)
from swx_api.app.services.api_keys_service import ApiKeysService
from swx_api.core.database.db import SessionDep
from swx_api.core.middleware.logging_middleware import logger
from swx_api.core.utils.language_helper import translate

from swx_api.core.models.common import PaginatedResponse


class ApiKeysController:
    @staticmethod
    async def get_valid_api_key(
            db: SessionDep,
            api_key: str,
    ) -> ApiKeysRead:
        """
        Dependency to validate an API key from the X-API-Key header.

        Args:
            db (SessionDep): Active DB session.
            api_key (str): The raw API key to validate.

        Returns:
            ApiKeysRead: The validated key object or raises HTTPException.
        """
        success, result = ApiKeysService.validate_and_increment_usage(db, api_key)

        print(f"[/debug] success: {success}, api_key_obj: {result}")

        if not success:
            logger.warning("API Key validation failed: %s", result)
            raise HTTPException(
                status_code=result["status"],
                detail={
                    "error": {
                        "code": result["status"],
                        "message": result["detail"]
                    }
                }
            )
        return result

    @staticmethod
    def list_api_keys(
            request: Request,
            db: SessionDep,
            skip: int = 0,
            limit: int = 100,
    ) -> List[ApiKeysRead]:
        """
        Admin-only: List all API keys with pagination.
        """
        try:
            return ApiKeysService.list_api_keys(db, skip=skip, limit=limit)
        except Exception as e:
            logger.error("Error in list_api_keys: %s", e)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @staticmethod
    def list_api_keys_for_user(
            request: Request,
            db: SessionDep,
            current_user,
            skip: int = 0,
            limit: int = 100,
    ) -> PaginatedResponse:
        """
        List all API keys that belong to the current user.

        Returns:
            PaginatedResponse: Paginated response with total, skip, limit, and items.
        """
        try:
            items = ApiKeysService.list_api_keys_for_user(db, current_user.id, skip, limit)
            total = len(items)  # Ideally you'd fetch the real count from the DB

            return PaginatedResponse(
                total=total,
                skip=skip,
                limit=limit,
                items=items,
            )
        except Exception as e:
            logger.error("Error in list_api_keys_for_user: %s", e)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @staticmethod
    def get_api_key_by_id(
            request: Request,
            id: uuid.UUID,
            db: SessionDep,
    ) -> ApiKeysRead:
        """
        Retrieve a single API key by UUID (admin).

        Raises:
            HTTPException(404) if not found.

        Returns:
            ApiKeysRead: The requested key.
        """
        item = ApiKeysService.get_api_key_by_id(db, id)
        if not item:
            raise HTTPException(
                status_code=404,
                detail=translate(request, "api_keys.not_found"),
            )
        return item

    @staticmethod
    def create_api_key(
            request: Request,
            data: ApiKeysCreate,
            db: SessionDep,
    ) -> ApiKeysReadWithKey:
        """
        Create a new API key for the user (enforced: one active key per user).

        Returns:
            ApiKeysReadWithKey: Created key and value.
        """
        try:
            return ApiKeysService.create_api_key(db, data)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error in create_api_key: %s", e)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @staticmethod
    def update_api_key(
            request: Request,
            id: uuid.UUID,
            data: ApiKeysUpdate,
            db: SessionDep,
    ) -> ApiKeysRead:
        """
        Admin-only: Update key metadata.

        Returns:
            ApiKeysRead: Updated key data.
        """
        item = ApiKeysService.update_api_key(db, id, data)
        if not item:
            raise HTTPException(
                status_code=404,
                detail=translate(request, "api_keys.not_found"),
            )
        return item

    @staticmethod
    def delete_api_key(
            request: Request,
            id: uuid.UUID,
            db: SessionDep,
            current_user,
    ) -> None:
        """
        Soft-delete (revoke) a key if it belongs to the current user.

        Raises:
            403 - Access denied if the key isn't owned by the user.
            404 - If the key doesn't exist.
        """
        api_key = ApiKeysService.get_api_key_by_id(db, id)

        if not api_key or api_key.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        success = ApiKeysService.delete_api_key(db, id)
        if not success:
            raise HTTPException(status_code=404, detail="API Key not found")
