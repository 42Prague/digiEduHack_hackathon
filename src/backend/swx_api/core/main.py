import os
from contextlib import asynccontextmanager, AsyncExitStack

import ngrok
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk import capture_exception
from fastapi import FastAPI, Request, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from swx_api.app.config.settings import app_settings
from swx_api.core.background_task import start_cache_refresh
from swx_api.core.config.settings import settings
from swx_api.core.middleware.logging_middleware import logger
from swx_api.core.router import router
from swx_api.core.utils.domain_router import DomainRouterMiddleware
from swx_api.core.utils.loader import load_middleware

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=0.2,
    environment=settings.ENVIRONMENT,
    release=f"swx-api@{app_settings.PROJECT_VERSION}",
    send_default_pii=True
)


@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:

        @asynccontextmanager
        async def custom_lifespan(_):
            # Disable translation cache refresh for hackathon (not needed)
            # start_cache_refresh()
            if app_settings.USE_NGROK and app_settings.NGROK_AUTH_TOKEN:
                logger.info("Starting ngrok tunnel...")
                try:
                    ngrok.set_auth_token(app_settings.NGROK_AUTH_TOKEN)
                    listener = await ngrok.forward(app_settings.APP_PORT)
                    app.state.public_url = listener.url()
                    logger.info(f"🔗 NGROK Tunnel ready: {app.state.public_url}")
                except Exception as e:
                    logger.error(f"Ngrok tunnel error: {e}")
            yield
            if app_settings.USE_NGROK:
                try:
                    ngrok.disconnect()
                    logger.info("Ngrok tunnel closed.")
                except Exception as e:
                    logger.warning(f"Ngrok shutdown failed: {e}")
            logger.info("Shutdown complete.")

        await stack.enter_async_context(custom_lifespan(app))
        yield


#  Initialize FastAPI app
app = FastAPI(
    title=app_settings.PROJECT_NAME,
    version=app_settings.PROJECT_VERSION,
    openapi_url=f"{settings.ROUTE_PREFIX}/openapi.json",
    lifespan=combined_lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#  Unified error format
def create_error_response(
    error_type: str,
    message: str,
    details: dict = None,
    status_code: int = 500
) -> JSONResponse:
    """Create a unified error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "type": error_type,
                "message": message,
                "details": details or {},
            }
        }
    )


#  Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc):
    error_type = "NotFound" if exc.status_code == 404 else "InternalError"
    return create_error_response(
        error_type=error_type,
        message=str(exc.detail) if exc.detail else "An error occurred",
        status_code=exc.status_code
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc):
    return create_error_response(
        error_type="ValidationError",
        message="Request validation failed",
        details={"fields": jsonable_encoder(exc.errors())},
        status_code=422
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    capture_exception(exc)
    return create_error_response(
        error_type="InternalError",
        message="An internal server error occurred",
        details={"detail": str(exc)} if settings.ENVIRONMENT == "local" else {},
        status_code=500
    )


#  Load global middleware
load_middleware(app)

#  Register all API routes
app.include_router(router)


#  Root route
@app.get("/")
def read_root(request: Request):
    return {
        "message": "Welcome to EduScale Engine API 🎓",
        "version": app_settings.PROJECT_VERSION,
        "description": "Open-source data infrastructure for Eduzměna Foundation - DigiEduHack 2025",
        "ngrok_url": getattr(request.app.state, "public_url", None) if app_settings.USE_NGROK else None,
    }


#  Optional health check endpoint
@app.get("/healthz", include_in_schema=False)
def health_check():
    return {"status": "ok"}


@app.get("/sentry-test")
def sentry_test():
    1 / 0  # 🔥 This will raise a ZeroDivisionError


# 🔐 Wrap app with Sentry middleware
app = SentryAsgiMiddleware(app)

#  Apply final domain-based middleware wrapping
app = DomainRouterMiddleware(app)
