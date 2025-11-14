from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import traceback

from swx_api.app.services.api_keys_service import ApiKeysService
from swx_api.core.database.db import get_db
from swx_api.core.utils.helper import extract_api_key
from swx_api.core.middleware.logging_middleware import logger


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.auth_status = "missing"  # default if no header

        try:
            api_key = extract_api_key(request)
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"error": {"code": e.status_code, "message": e.detail}}
            )

        if not api_key:
            request.state.auth_status = "missing"
            return JSONResponse(
                status_code=400,
                content={"error": {"code": 400, "message": "Missing API Key"}}
            )

        db_gen = get_db()
        db = next(db_gen)

        try:
            success, result = ApiKeysService.validate_and_increment_usage(db, api_key)

            logger.debug("[/debug] API Key Validation result", extra={
                "success": success,
                "result": str(result)
            })

            if not success:
                request.state.auth_status = "invalid"
                return JSONResponse(
                    status_code=result["status"],
                    content={"error": {
                        "code": result["status"],
                        "message": result["detail"]
                    }}
                )

            # All good → result is the ApiKeys object
            api_key_obj = result
            request.state.api_key_id = api_key_obj.id
            request.state.user_id = api_key_obj.user_id
            request.state.client_name = getattr(api_key_obj, "client_name", None)
            request.state.client_version = getattr(api_key_obj, "client_version", None)
            request.state.auth_status = "success"

            logger.debug("[/debug] API key metadata attached", extra={
                "api_key_id": str(api_key_obj.id),
                "user_id": str(api_key_obj.user_id),
                "client_name": request.state.client_name,
                "client_version": request.state.client_version
            })

        except Exception as e:
            logger.exception(f"[/debug] Exception during API key validation: {str(e)}")
            traceback.print_exc()

            request.state.auth_status = "invalid"
            return JSONResponse(
                status_code=401,
                content={"error": {"code": 401, "message": "Unauthorized"}}
            )

        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

        return await call_next(request)
