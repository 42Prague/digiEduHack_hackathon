"""
Sentry Middleware
-----------------
This module initializes Sentry for error monitoring in production environments.

Features:
- Captures unhandled exceptions.
- Provides error tracking and logging with Sentry.

Functions:
- `setup_sentry_middleware()`: Configures Sentry SDK.
"""

import sentry_sdk
from swx_api.core.config.settings import settings
import sentry_sdk.transport


def setup_sentry_middleware():
    """
    Initializes Sentry for error monitoring.

    Behavior:
        - Only enabled if `settings.SENTRY_DSN` is set.
        - Disabled in local development environments.
    """
    if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
        sentry_sdk.init(
            dsn=str(settings.SENTRY_DSN),
            send_default_pii=True,
            traces_sample_rate=1.0,
            profile_session_sample_rate=1.0,
            profile_lifecycle="trace",
            transport=sentry_sdk.transport.HttpTransport
        )
