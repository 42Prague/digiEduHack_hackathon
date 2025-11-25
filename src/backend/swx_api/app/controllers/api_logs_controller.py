import uuid
from fastapi import HTTPException, Request
from swx_api.core.database.db import SessionDep
from swx_api.app.services.api_logs_service import ApiLogsService
from swx_api.app.models.api_logs import ApiLogsCreate, ApiLogsUpdate, ApiLogsPublic
from swx_api.app.models.api_keys import ApiKeys
from swx_api.core.middleware.logging_middleware import logger
from swx_api.core.utils.language_helper import translate

from swx_api.core.models.common import PaginatedResponse


class ApiLogsController:
    @staticmethod
    def retrieve_all_api_logs_resources(
        request: Request,
        db: SessionDep,
        skip: int = 0,
        limit: int = 100,
    ):
        """
        Retrieve all API log entries (admin-only).

        Args:
            request (Request): FastAPI request object.
            db (SessionDep): Database session dependency.
            skip (int): Number of logs to skip.
            limit (int): Number of logs to return.

        Returns:
            List[ApiLogsPublic]: Paginated list of all log entries.

        Raises:
            HTTPException(500): On unexpected errors.
        """
        try:
            return ApiLogsService.retrieve_all_api_logs_resources(db, skip=skip, limit=limit)
        except Exception as e:
            logger.error("Error in retrieve_all_api_logs_resources: %s", e)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @staticmethod
    def retrieve_logs_for_user(
        request: Request,
        db: SessionDep,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ):
        """
        Retrieve logs for all API keys owned by a specific user.

        Args:
            request (Request): Request context.
            db (SessionDep): Active database session.
            user_id (UUID): Authenticated user's ID.
            skip (int): Offset for pagination.
            limit (int): Limit of records.

        Returns:
            List[ApiLogsPublic]: Logs linked to user's API keys.

        Raises:
            HTTPException(500): On unexpected errors.
        """
        try:
            items = ApiLogsService.retrieve_logs_by_user_id(db, user_id, skip, limit)
            total = len(items)

            return PaginatedResponse(
                total=total,
                skip=skip,
                limit=limit,
                items=items,
            )
        except Exception as e:
            logger.error("Error in retrieve_logs_for_user: %s", e)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @staticmethod
    def retrieve_log_for_user_by_id(
        request: Request,
        db: SessionDep,
        log_id: uuid.UUID,
        user_id: uuid.UUID,
    ):
        """
        Retrieve a specific API log if it belongs to the authenticated user.

        Args:
            request (Request): Request context.
            db (SessionDep): DB session.
            log_id (UUID): ID of the log.
            user_id (UUID): User making the request.

        Returns:
            ApiLogsPublic: Log entry if owned by user.

        Raises:
            HTTPException(403): If user doesn't own the API key.
            HTTPException(404): If log not found.
        """
        log = ApiLogsService.retrieve_api_logs_by_id(db, log_id)
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")

        key = db.get(ApiKeys, log.api_key_id)
        if not key or key.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return log

    @staticmethod
    def retrieve_api_logs_by_id(request: Request, id: uuid.UUID, db: SessionDep):
        """
        Retrieve a log entry by ID (admin only).

        Args:
            request (Request): Request context.
            id (UUID): Log entry ID.
            db (SessionDep): DB session.

        Returns:
            ApiLogsPublic: The log entry.

        Raises:
            HTTPException(404): If log not found.
        """
        item = ApiLogsService.retrieve_api_logs_by_id(db, id)
        if not item:
            raise HTTPException(status_code=404, detail=translate(request, "api_logs.not_found"))
        return item

    @staticmethod
    def create_new_api_logs(request: Request, data: ApiLogsCreate, db: SessionDep):
        """
        Create a new log entry (usually called internally by middleware).

        Args:
            request (Request): Request context.
            data (ApiLogsCreate): Log input.
            db (SessionDep): DB session.

        Returns:
            ApiLogsPublic: The newly created log.

        Raises:
            HTTPException(500): On failure.
        """
        try:
            return ApiLogsService.create_new_api_logs(db, data)
        except Exception as e:
            logger.error("Error in create_new_api_logs: %s", e)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @staticmethod
    def update_existing_api_logs(request: Request, id: uuid.UUID, data: ApiLogsUpdate, db: SessionDep):
        """
        Update an existing log (admin only).

        Args:
            request (Request): Request context.
            id (UUID): Log ID.
            data (ApiLogsUpdate): Updated fields.
            db (SessionDep): DB session.

        Returns:
            ApiLogsPublic: Updated log entry.

        Raises:
            HTTPException(404): If log not found.
        """
        item = ApiLogsService.update_existing_api_logs(db, id, data)
        if not item:
            raise HTTPException(status_code=404, detail=translate(request, "api_logs.not_found"))
        return item

    @staticmethod
    def delete_existing_api_logs(request: Request, id: uuid.UUID, db: SessionDep):
        """
        Delete a log entry by ID (admin only).

        Args:
            request (Request): Request context.
            id (UUID): Log ID.
            db (SessionDep): DB session.

        Returns:
            None

        Raises:
            HTTPException(404): If log not found.
        """
        success = ApiLogsService.delete_existing_api_logs(db, id)
        if not success:
            raise HTTPException(status_code=404, detail=translate(request, "api_logs.not_found"))
        return None

    @staticmethod
    def get_user_usage_summary(db: SessionDep, user_id: uuid.UUID):
        """
        Return summary metrics for user's API usage.

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

        Example:
            {
                "total_calls": 128,
                "first_call_at": "2025-07-15T09:32:00Z",
                "last_call_at": "2025-07-27T11:21:04Z"
            }
        """
        return ApiLogsService.compute_user_usage_summary(db, user_id)
