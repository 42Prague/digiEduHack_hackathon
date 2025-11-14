"""Main application entrypoint for EduScale Engine."""

from fastapi import FastAPI

from eduscale.api.v1 import routes_health
from eduscale.api.v1.routes_nlq import router as nlq_router, ui_router as nlq_ui_router
from eduscale.api.v1.routes_tabular import router as tabular_router
from eduscale.api.v1.routes_upload import router as upload_router, ui_router
from eduscale.core.config import settings
from eduscale.core.logging import setup_logging


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    # Initialize logging first
    setup_logging()

    # Create FastAPI application
    app = FastAPI(
        title=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
    )

    # Register routers
    app.include_router(routes_health.router, tags=["health"])
    app.include_router(tabular_router, tags=["tabular"])
    app.include_router(upload_router)
    app.include_router(ui_router)
    app.include_router(nlq_router, tags=["nlq"])
    app.include_router(nlq_ui_router)

    return app


# Export app instance for ASGI servers
app = create_app()
