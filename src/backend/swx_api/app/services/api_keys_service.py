# Service layer for managing API key business logic.

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlmodel import select

from swx_api.app.models.api_keys import ApiKeysCreate, ApiKeysUpdate, ApiKeys
from swx_api.app.repositories.api_keys_repository import ApiKeysRepository
from swx_api.app.utils.security import generate_api_key
from swx_api.core.database.db import SessionDep
from swx_api.core.middleware.logging_middleware import logger

MAX_USAGE_LIMIT = 10000


class ApiKeysService:
    @staticmethod
    def list_api_keys(
            db: SessionDep,
            skip: int = 0,
            limit: int = 100
    ) -> list[ApiKeys]:
        """
        Admin-only: Retrieve all API keys.

        Returns:
            List of ApiKeys (raw model).
        """
        return ApiKeysRepository.list_api_keys(db, skip=skip, limit=limit)

    @staticmethod
    def list_api_keys_for_user(
            db: SessionDep,
            user_id: uuid.UUID,
            skip: int = 0,
            limit: int = 100
    ) -> list[ApiKeys]:
        """
        Retrieve API keys belonging to a specific user.

        Returns:
            List of ApiKeys for the user.
        """
        return ApiKeysRepository.list_api_keys_for_user(db, user_id, skip, limit)

    @staticmethod
    def get_api_key_by_key(
            db: SessionDep,
            key: str
    ) -> ApiKeys | None:
        """
        Look up an API key by its key string.

        Returns:
            ApiKeys or None.
        """
        return ApiKeysRepository.get_api_key_by_key(db, key)

    @staticmethod
    def increment_usage_count(
            db: SessionDep,
            api_key: ApiKeys
    ) -> None:
        """
        Increment the usage counter for a valid API key.
        """
        ApiKeysRepository.increment_usage_count(db, api_key)

    @staticmethod
    def validate_and_increment_usage(
            db: SessionDep,
            key_str: str
    ) -> tuple[bool, ApiKeys | dict]:
        """
        Validate a key, enforce revocation/expiry/limits, and increment usage.

        Returns:
            Tuple (bool success, ApiKeys | error dict).
        """
        try:
            api_key = ApiKeysService.get_api_key_by_key(db, key_str)

            if not api_key:
                return False, {"status": 401, "detail": "Invalid API Key"}

            if api_key.revoked:
                return False, {"status": 403, "detail": "API Key has been revoked"}

            # Ensure timezone-aware expiry check
            expires_at = api_key.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if expires_at < datetime.now(timezone.utc):
                return False, {"status": 403, "detail": "API Key has expired"}

            if api_key.usage_count >= MAX_USAGE_LIMIT:
                return False, {"status": 429, "detail": "API Key usage limit exceeded"}

            ApiKeysService.increment_usage_count(db, api_key)
            return True, api_key

        except Exception as e:
            logger.error("Error validating API key: %s", e)
            return False, {"status": 500, "detail": "Internal Server Error"}

    @staticmethod
    def get_api_key_by_id(
            db: SessionDep,
            id: uuid.UUID
    ) -> ApiKeys | None:
        """
        Retrieve an API key by its UUID.

        Returns:
            ApiKeys or None
        """
        return ApiKeysRepository.get_api_key_by_id(db, id)

    @staticmethod
    def create_api_key(
            db: SessionDep,
            data: ApiKeysCreate
    ) -> ApiKeys:
        """
        Create a new API key for a user (1 active key max).

        Raises:
            HTTPException 400 if key already exists.

        Returns:
            Created ApiKeys instance.
        """
        existing = db.exec(
            select(ApiKeys).where(
                ApiKeys.user_id == data.user_id,
                ApiKeys.revoked == False,
                ApiKeys.expires_at >= datetime.now(timezone.utc)
            )
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="User already has an active API key."
            )

        key_str = generate_api_key()
        expires_at = datetime.now(timezone.utc) + timedelta(days=365)

        api_key = ApiKeys(
            key=key_str,
            name="Production Key",
            revoked=False,
            usage_count=0,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            user_id=data.user_id,
        )

        return ApiKeysRepository.create_api_key(db, api_key)

    @staticmethod
    def update_api_key(
            db: SessionDep,
            id: uuid.UUID,
            data: ApiKeysUpdate
    ) -> ApiKeys | None:
        """
        Update API key metadata like name or expiration.

        Returns:
            Updated ApiKeys or None.
        """
        return ApiKeysRepository.update_api_key(db, id, data)

    @staticmethod
    def delete_api_key(
            db: SessionDep,
            id: uuid.UUID
    ) -> bool:
        """
        Soft-delete (revoke) an API key by marking `revoked=True`.

        Returns:
            True if revoked or already revoked, False if not found.
        """
        return ApiKeysRepository.delete_api_key(db, id)
