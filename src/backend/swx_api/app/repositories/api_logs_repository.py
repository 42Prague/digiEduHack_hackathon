import uuid
from sqlmodel import select
from sqlalchemy import func

from swx_api.core.database.db import SessionDep
from swx_api.app.models.api_logs import ApiLogs, ApiLogsCreate, ApiLogsUpdate
from swx_api.app.models.api_keys import ApiKeys


class ApiLogsRepository:
    @staticmethod
    def retrieve_all_api_logs_resources(db: SessionDep, skip: int = 0, limit: int = 100):
        """
        Retrieve all API log entries with pagination.

        Args:
            db (SessionDep): Database session.
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.

        Returns:
            List[ApiLogs]: List of API log entries.

        Example:
            [
                {
                    "id": "b1d6e8ea-b32f-4a5e-85dc-b167bfc1a7e1",
                    "api_key_id": "f1a7c35e-0f93-45fd-83ec-5109b42d7b35",
                    "endpoint": "/transport/departures",
                    "method": "GET",
                    "status_code": 200,
                    "duration_ms": 123,
                    "created_at": "2025-07-27T08:01:22Z"
                },
                ...
            ]
        """
        query = select(ApiLogs).offset(skip).limit(limit)
        return db.exec(query).all()

    @staticmethod
    def retrieve_logs_by_user_id(
        db: SessionDep,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ):
        """
        Retrieve all API logs belonging to the user's API keys.

        Args:
            db (SessionDep): Database session.
            user_id (UUID): User's unique ID.
            skip (int): Offset for pagination.
            limit (int): Number of logs to return.

        Returns:
            List[ApiLogs]: Logs for the user’s API keys.

        Notes:
            This uses a subquery to fetch all API key IDs belonging to the user,
            and returns all logs linked to those keys.
        """
        subquery = select(ApiKeys.id).where(ApiKeys.user_id == user_id).subquery()

        query = (
            select(ApiLogs)
            .where(ApiLogs.api_key_id.in_(subquery))
            .offset(skip)
            .limit(limit)
        )

        return db.exec(query).all()

    @staticmethod
    def retrieve_api_logs_by_id(db: SessionDep, id: uuid.UUID):
        """
        Retrieve a single API log entry by ID.

        Args:
            db (SessionDep): Database session.
            id (UUID): Log ID.

        Returns:
            ApiLogs | None: Log entry or None if not found.
        """
        return db.get(ApiLogs, id)

    @staticmethod
    def create_new_api_logs(db: SessionDep, data: ApiLogsCreate):
        """
        Create and persist a new API log entry.

        Args:
            db (SessionDep): Database session.
            data (ApiLogsCreate): Data for the new log.

        Returns:
            ApiLogs: The created log record.
        """
        obj = ApiLogs(**data.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update_existing_api_logs(db: SessionDep, id: uuid.UUID, data: ApiLogsUpdate):
        """
        Update fields on an existing API log.

        Args:
            db (SessionDep): Database session.
            id (UUID): Log ID.
            data (ApiLogsUpdate): Partial fields to update.

        Returns:
            ApiLogs | None: Updated log or None if not found.
        """
        obj = db.get(ApiLogs, id)
        if not obj:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete_existing_api_logs(db: SessionDep, id: uuid.UUID):
        """
        Permanently delete a log entry.

        Args:
            db (SessionDep): Database session.
            id (UUID): Log ID.

        Returns:
            bool: True if deleted, False if not found.
        """
        obj = db.get(ApiLogs, id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True

    @staticmethod
    def compute_user_usage_summary(db: SessionDep, user_id: uuid.UUID):
        """
        Aggregate total API calls and usage timeline for a user.

        Args:
            db (SessionDep): Database session.
            user_id (UUID): ID of the user whose stats to compute.

        Returns:
            dict: {
                "total_calls": int,
                "first_call_at": datetime | None,
                "last_call_at": datetime | None
            }

        Example:
            {
                "total_calls": 1983,
                "first_call_at": "2025-07-01T10:00:00Z",
                "last_call_at": "2025-07-27T08:05:43Z"
            }
        """
        subquery = select(ApiKeys.id).where(ApiKeys.user_id == user_id).subquery()

        result = db.exec(
            select(
                func.count(ApiLogs.id),
                func.min(ApiLogs.created_at),
                func.max(ApiLogs.created_at)
            ).where(ApiLogs.api_key_id.in_(subquery))
        ).one()

        return {
            "total_calls": result[0],
            "first_call_at": result[1],
            "last_call_at": result[2],
        }
