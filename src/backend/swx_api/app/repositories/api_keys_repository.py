# Repository for managing API key records in the database.
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlmodel import select
from swx_api.app.models.api_keys import ApiKeys, ApiKeysCreate, ApiKeysUpdate
from swx_api.app.utils.security import generate_api_key
from swx_api.core.database.db import SessionDep


class ApiKeysRepository:
    @staticmethod
    def list_api_keys(
            db: SessionDep,
            skip: int = 0,
            limit: int = 100
    ) -> List[ApiKeys]:
        """
        Retrieve all API keys (admin-level).

        Args:
            db (SessionDep): Active database session.
            skip (int): Items to skip.
            limit (int): Max number of results.

        Returns:
            List[ApiKeys]: All API keys in the system.
        """
        query = select(ApiKeys).offset(skip).limit(limit)
        return db.exec(query).all()

    @staticmethod
    def list_api_keys_for_user(
            db: SessionDep,
            user_id: uuid.UUID,
            skip: int = 0,
            limit: int = 100
    ) -> List[ApiKeys]:
        """
        Retrieve API keys owned by a specific user.

        Args:
            db (SessionDep): DB session.
            user_id (UUID): User ID.
            skip (int): Offset.
            limit (int): Limit.

        Returns:
            List[ApiKeys]: Keys linked to this user.
        """
        query = select(ApiKeys).where(ApiKeys.user_id == user_id).offset(skip).limit(limit)
        return db.exec(query).all()

    @staticmethod
    def get_api_key_by_key(
            db: SessionDep,
            key_str: str
    ) -> Optional[ApiKeys]:
        """
        Find an API key by the key string.

        Args:
            db (SessionDep): DB session.
            key_str (str): The key itself.

        Returns:
            ApiKeys | None: The key object or None.
        """
        statement = select(ApiKeys).where(ApiKeys.key == key_str)
        return db.exec(statement).first()

    @staticmethod
    def increment_usage_count(
            db: SessionDep,
            api_key: ApiKeys
    ) -> None:
        """
        Increase the usage count for a given key.

        Args:
            db (SessionDep): DB session.
            api_key (ApiKeys): Target key to increment.
        """
        api_key.usage_count += 1
        db.add(api_key)
        db.commit()

    @staticmethod
    def get_api_key_by_id(
            db: SessionDep,
            id: uuid.UUID
    ) -> Optional[ApiKeys]:
        """
        Retrieve a specific API key by its ID.

        Args:
            db (SessionDep): DB session.
            id (UUID): API key ID.

        Returns:
            ApiKeys | None: The found key or None.
        """
        return db.get(ApiKeys, id)

    @staticmethod
    def create_api_key(
            db: SessionDep,
            api_key: ApiKeys
    ) -> ApiKeys:
        """
        Insert a new API key into the DB.

        Args:
            db (SessionDep): DB session.
            api_key (ApiKeys): Key instance to save.

        Returns:
            ApiKeys: Persisted key.
        """
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return api_key

    @staticmethod
    def update_api_key(
            db: SessionDep,
            id: uuid.UUID,
            data: ApiKeysUpdate
    ) -> Optional[ApiKeys]:
        """
        Update an existing API key by ID.

        Args:
            db (SessionDep): DB session.
            id (UUID): Key ID.
            data (ApiKeysUpdate): Update payload.

        Returns:
            ApiKeys | None: Updated key or None.
        """
        obj = db.get(ApiKeys, id)
        if not obj:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete_api_key(
            db: SessionDep,
            id: uuid.UUID
    ) -> bool:
        """
        Soft-delete an API key (revoke it).

        Args:
            db (SessionDep): DB session.
            id (UUID): Key ID.

        Returns:
            bool: True if revoked or already revoked, False if not found.
        """
        api_key = ApiKeysRepository.get_api_key_by_id(db, id)
        if not api_key:
            return False

        if api_key.revoked:
            return True

        api_key.revoked = True
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return True
