from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import redis.asyncio as redis
from typing import Optional


class RedisSessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str, cookie_name: str = "session_id", max_age: int = 900):
        super().__init__(app)
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.cookie_name = cookie_name
        self.max_age = max_age
        self.prefix = "session:"

    async def dispatch(self, request: Request, call_next):

        print("[RedisSession] All headers:")
        for key, value in request.headers.items():
            print(f"  {key}: {value}")


        session_id: Optional[str] = (
                request.headers.get("x-session-id")
                or request.cookies.get(self.cookie_name)
        )

        print(f"[RedisSession] Extracted session-id: {session_id or 'None'}")

        session_data = {}

        if session_id:
            redis_key = f"{self.prefix}{session_id}"
            session_data = await self.redis.hgetall(redis_key)

            if session_data:
                await self.redis.expire(redis_key, self.max_age)
                print(f"[RedisSession] Loaded session {session_id}: {session_data}")
            else:
                print(f"[RedisSession] No session data found for ID: {session_id}")
        else:
            print("[RedisSession] No session ID provided")


        request.state.session_id = session_id
        request.state.session_data = session_data or {}

        return await call_next(request)
