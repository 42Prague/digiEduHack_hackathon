# import time
# import uuid
# from datetime import datetime
# from typing import Optional
#
# from fastapi import Request
# from starlette.middleware.base import BaseHTTPMiddleware
# from starlette.responses import StreamingResponse
#
# from swx_api.app.controllers.api_logs_controller import ApiLogsController
# from swx_api.app.models.api_logs import ApiLogsCreate
# from swx_api.core.database.db import get_db
#
#
# class APILogMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         request_time = datetime.utcnow()
#         start_time = time.time()
#
#         # Try to read request body safely
#         try:
#             request_body = await request.json()
#         except Exception:
#             request_body = {}
#
#         # Process the request and capture the response
#         response = await call_next(request)
#         body = b"".join([chunk async for chunk in response.body_iterator])
#         response_text = body.decode("utf-8", errors="ignore")[:1000]
#         latency_ms = int((time.time() - start_time) * 1000)
#         response_time = datetime.utcnow()
#
#         # Extract metadata
#         api_key_id: Optional[uuid.UUID] = getattr(request.state, "api_key_id", None)
#         user_id: Optional[uuid.UUID] = getattr(request.state, "user_id", None)
#         client_name = getattr(request.state, "client_name", None)
#         client_version = getattr(request.state, "client_version", None)
#         tool_name = getattr(request.state, "tool_name", None)
#
#         # Log only if key + user available
#         if api_key_id and user_id:
#             db_gen = get_db()
#             db = next(db_gen)
#             try:
#                 log = ApiLogsCreate(
#                     api_key_id=api_key_id,
#                     user_id=user_id,
#                     path=request.url.path,
#                     tool_name=tool_name,
#                     status_code=response.status_code,
#                     request_body=request_body,
#                     response_body={"text": response_text},
#                     ip_address=request.client.host,
#                     user_agent=request.headers.get("user-agent"),
#                     client_name=client_name,
#                     client_version=client_version,
#                     request_time=request_time,
#                     response_time=response_time,
#                     latency_ms=latency_ms,
#                 )
#                 # Sync method call (no await)
#                 ApiLogsController.create_new_api_logs(request, log, db)
#             except Exception as e:
#                 print("[LOGGING ERROR]", e)
#                 db.rollback()
#             finally:
#                 try:
#                     next(db_gen)
#                 except StopIteration:
#                     pass
#
#         return StreamingResponse(
#             content=aiter_bytes([body]),
#             status_code=response.status_code,
#             headers=dict(response.headers),
#             media_type=response.media_type
#         )
#
#
# async def aiter_bytes(chunks):
#     for chunk in chunks:
#         yield chunk

import time
import uuid
from datetime import datetime
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from swx_api.app.controllers.api_logs_controller import ApiLogsController
from swx_api.app.models.api_logs import ApiLogsCreate
from swx_api.core.database.db import get_db


class APILogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_time = datetime.utcnow()
        start_time = time.time()

        # Try to read request body safely
        try:
            request_body = await request.json()
        except Exception:
            request_body = {}

        response = await call_next(request)

        # Capture the body
        body = b"".join([chunk async for chunk in response.body_iterator])
        response_text = body.decode("utf-8", errors="ignore")[:1000]
        latency_ms = int((time.time() - start_time) * 1000)
        response_time = datetime.utcnow()

        # Metadata
        api_key_id: Optional[uuid.UUID] = getattr(request.state, "api_key_id", None)
        user_id: Optional[uuid.UUID] = getattr(request.state, "user_id", None)
        client_name = getattr(request.state, "client_name", None)
        client_version = getattr(request.state, "client_version", None)
        tool_name = getattr(request.state, "tool_name", None)

        # Determine auth status
        if api_key_id and user_id:
            auth_status = "success"
        elif api_key_id or user_id:
            auth_status = "invalid"
        else:
            auth_status = "missing"

        db_gen = get_db()
        db = next(db_gen)

        try:
            log = ApiLogsCreate(
                api_key_id=api_key_id,
                user_id=user_id,
                path=request.url.path,
                tool_name=tool_name,
                status_code=response.status_code,
                request_body=request_body,
                response_body={"text": response_text},
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                client_name=client_name,
                client_version=client_version,
                request_time=request_time,
                response_time=response_time,
                latency_ms=latency_ms,
                auth_status=auth_status,
            )
            ApiLogsController.create_new_api_logs(request, log, db)
        except Exception as e:
            print("[LOGGING ERROR]", e)
            db.rollback()
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

        return StreamingResponse(
            content=aiter_bytes([body]),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )


async def aiter_bytes(chunks):
    for chunk in chunks:
        yield chunk
