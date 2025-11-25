import uuid
from swx_api.core.database.db import SessionDep
from swx_api.app.repositories.api_logs_repository import ApiLogsRepository
from swx_api.app.models.api_logs import ApiLogsCreate, ApiLogsUpdate


class ApiLogsService:
    @staticmethod
    def retrieve_all_api_logs_resources(db: SessionDep, skip: int = 0, limit: int = 100):
        """
        Retrieve all API log entries from the system (admin-only).

        Args:
            db (SessionDep): Active database session.
            skip (int): Pagination offset.
            limit (int): Maximum number of logs to return.

        Returns:
            List[ApiLogs]: List of all API logs.

        Use Case:
            Display a complete audit trail or metrics dashboard for admins.
        """
        return ApiLogsRepository.retrieve_all_api_logs_resources(db, skip=skip, limit=limit)

    @staticmethod
    def retrieve_logs_by_user_id(
        db: SessionDep,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ):
        """
        Retrieve all API log entries tied to the user's API keys.

        Args:
            db (SessionDep): DB session.
            user_id (UUID): User whose logs are being retrieved.
            skip (int): Pagination offset.
            limit (int): Limit per page.

        Returns:
            List[ApiLogs]: Logs tied to user's keys.

        Use Case:
            Show "My Logs" view in a developer dashboard.
        """
        return ApiLogsRepository.retrieve_logs_by_user_id(db, user_id, skip, limit)

    @staticmethod
    def retrieve_api_logs_by_id(db: SessionDep, id: uuid.UUID):
        """
        Retrieve a single log entry by its UUID.

        Args:
            db (SessionDep): DB session.
            id (UUID): Log ID.

        Returns:
            ApiLogs | None: The log entry or None.

        Use Case:
            Fetch a specific request's log detail (e.g. request time, latency).
        """
        return ApiLogsRepository.retrieve_api_logs_by_id(db, id)

    @staticmethod
    def create_new_api_logs(db: SessionDep, data: ApiLogsCreate):
        """
        Persist a new API log entry.

        Args:
            db (SessionDep): Active DB session.
            data (ApiLogsCreate): Input payload containing log info.

        Returns:
            ApiLogs: The newly created log entry.

        Use Case:
            Automatically called by logging middleware after tool execution.
        """
        return ApiLogsRepository.create_new_api_logs(db, data)

    @staticmethod
    def update_existing_api_logs(db: SessionDep, id: uuid.UUID, data: ApiLogsUpdate):
        """
        Update specific fields of an existing log entry.

        Args:
            db (SessionDep): DB session.
            id (UUID): Log ID.
            data (ApiLogsUpdate): Patch data.

        Returns:
            ApiLogs | None: The updated object, or None if not found.

        Use Case:
            Optional metadata adjustments or tagging (e.g. `tag: 'slow query'`).
        """
        return ApiLogsRepository.update_existing_api_logs(db, id, data)

    @staticmethod
    def delete_existing_api_logs(db: SessionDep, id: uuid.UUID):
        """
        Hard-delete a log entry by its UUID.

        Args:
            db (SessionDep): DB session.
            id (UUID): The log ID.

        Returns:
            bool: True if deleted, False if not found.

        Use Case:
            Cleanup old logs or admin-initiated data purging.
        """
        return ApiLogsRepository.delete_existing_api_logs(db, id)

    @staticmethod
    def compute_user_usage_summary(db: SessionDep, user_id: uuid.UUID):
        """
        Compute a summary of a user's total API usage.

        Args:
            db (SessionDep): DB session.
            user_id (UUID): ID of the user.

        Returns:
            dict:
                {
                    "total_calls": int,
                    "first_call_at": datetime | None,
                    "last_call_at": datetime | None
                }

        Use Case:
            Used in analytics dashboard to display user usage stats.
        """
        return ApiLogsRepository.compute_user_usage_summary(db, user_id)
