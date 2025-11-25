import uuid
import json
from fastapi import Request, Response, HTTPException
import redis.asyncio as redis
from swx_api.app.config.settings import app_settings

redis_client = redis.from_url(app_settings.REDIS_URL, decode_responses=True)

SESSION_TIMEOUT = int(app_settings.SESSION_TIMEOUT)

async def create_session(username: str, response: Response) -> str:
    session_id = str(uuid.uuid4())
    await redis_client.hset(f"session:{session_id}", mapping={"user": username, "status": "active"})
    await redis_client.expire(f"session:{session_id}", SESSION_TIMEOUT)

    response.set_cookie(
        key=app_settings.SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=True,
        max_age=SESSION_TIMEOUT,
    )
    return session_id

async def get_session(request: Request):
    session_id = request.cookies.get(app_settings.SESSION_COOKIE_NAME)
    if not session_id:
        raise HTTPException(status_code=403, detail="No session cookie found")

    session_data = await redis_client.hgetall(f"session:{session_id}")
    if not session_data:
        response = Response()
        response.delete_cookie(app_settings.SESSION_COOKIE_NAME)
        raise HTTPException(status_code=404, detail="Session expired or invalid")

    # Extend expiration (sliding session)
    await redis_client.expire(f"session:{session_id}", SESSION_TIMEOUT)
    return session_id, session_data

async def destroy_session(response: Response, session_id: str):
    await redis_client.delete(f"session:{session_id}")
    response.delete_cookie(app_settings.SESSION_COOKIE_NAME)
