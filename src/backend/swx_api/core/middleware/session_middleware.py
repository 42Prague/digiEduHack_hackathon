"""
Session Middleware
------------------
This module configures session management using Starlette's SessionMiddleware.

Features:
- Manages session-based authentication.
- Uses secure session storage.

Functions:
- `setup_session_middleware(app)`: Applies session settings to the FastAPI app.
"""

from starlette.middleware.sessions import SessionMiddleware
from swx_api.core.config.settings import settings

from swx_api.app.config.settings import app_settings


def setup_session_middleware(app):
    """
    Configures SessionMiddleware for session-based authentication.

    Args:
        app: The FastAPI application instance.

    Behavior:
        - Uses `settings.SECRET_KEY` for encryption.
        - Session duration is set to 1 day (86400 seconds).
        - Uses `same_site="lax"` for session security.
        - Does not enforce HTTPS-only mode (set `https_only=True` in production).
    """
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,  # Ensure this is a strong key
        max_age=86400,  # 1 day
        same_site="lax",
        https_only=True,
    )
