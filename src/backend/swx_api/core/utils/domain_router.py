from starlette.types import ASGIApp, Receive, Scope, Send
from swx_api.core.middleware.logging_middleware import logger


def get_sub_app_for_host(host: str) -> ASGIApp | None:
    # Normalize host (remove 'www.' and trailing dots)
    clean_host = host.lower().lstrip("www.").rstrip(".")
    # No sub-apps configured
    return None


class DomainRouterMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        host_header = dict(scope["headers"]).get(b"host", b"").decode()
        logger.debug(f"[DomainRouter] Incoming host: {host_header}")

        sub_app = get_sub_app_for_host(host_header)

        if sub_app:
            logger.debug(f"[DomainRouter] Routing to sub-app for host: {host_header}")
            await sub_app(scope, receive, send)
        else:
            # Only log warning for non-localhost hosts (localhost is expected)
            if "localhost" not in host_header.lower() and "127.0.0.1" not in host_header:
                logger.debug(f"[DomainRouter] No sub-app found for host: {host_header} (using default app)")
            await self.app(scope, receive, send)
