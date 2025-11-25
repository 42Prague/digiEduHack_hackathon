from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class ForceAcceptHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        scope = request.scope
        headers = dict(scope["headers"])
        current_accept = headers.get(b"accept", b"").decode("latin1").lower()

        required = ["application/json", "text/event-stream"]
        if not all(req in current_accept for req in required):
            new_accept = ", ".join(set([*current_accept.split(","), *required])).strip(", ")
            scope["headers"] = [
                (k, v) if k != b"accept" else (b"accept", new_accept.encode("latin1"))
                for k, v in scope["headers"]
            ]

        return await call_next(Request(scope, request.receive))
