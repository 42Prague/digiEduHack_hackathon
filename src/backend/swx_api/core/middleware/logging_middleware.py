"""
Logging Middleware
------------------
This module configures logging for the FastAPI application.

Features:
- Logs all incoming HTTP requests and their response times.
- Captures application warnings as logs.
- Stores logs in a rotating file system.

Classes:
- `LoggingMiddleware`: Middleware to log HTTP requests.

Logs:
- Console logs for real-time debugging.
- Rotating file logs for persistent records.
"""

import json
import logging
import os
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from swx_api.core.config.settings import settings

# Get environment settings
ENVIRONMENT = settings.ENVIRONMENT
LOG_LEVEL = settings.LOG_LEVEL  # Default to WARNING

# Ensure logs directory exists
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

# Create a logger instance
logger = logging.getLogger("SwX-API")

# Convert LOG_LEVEL to valid logging level
LOG_LEVEL_MAPPING = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

logger.setLevel(LOG_LEVEL_MAPPING.get(LOG_LEVEL, logging.WARNING))  # Default to WARNING

# Log format (structured JSON format for production)
class JSONFormatter(logging.Formatter):
    """Custom log formatter that outputs logs in JSON format."""
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "file": record.filename,
            "line": record.lineno,
        }
        return json.dumps(log_record)

# Console Handler (Only enabled in development)
if ENVIRONMENT == "local":
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

# File Handler (Rotating logs, max 5MB per file, 10 backups)
log_filename = os.path.join(LOG_DIR, "swx_api.log")
file_handler = RotatingFileHandler(log_filename, maxBytes=5 * 1024 * 1024, backupCount=10)
file_handler.setFormatter(JSONFormatter())
logger.addHandler(file_handler)

# Capture warnings as logs
logging.captureWarnings(True)

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming HTTP requests and their response times.
    """
    async def dispatch(self, request: Request, call_next):
        """
        Logs request details and response duration.

        Args:
            request: The incoming request object.
            call_next: The next middleware or request handler.

        Logs:
            - Request method and URL.
            - Response status code and duration.
            - Categorized logging (INFO, WARNING, CRITICAL).
        """
        start_time = time.time()

        response = await call_next(request)

        duration = round(time.time() - start_time, 4)
        log_msg = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": duration
        }

        if response.status_code >= 500:
            logger.critical(json.dumps(log_msg))
        elif response.status_code >= 400:
            logger.warning(json.dumps(log_msg))
        else:
            if ENVIRONMENT == "local":  # Only log successful requests in development
                logger.info(json.dumps(log_msg))

        return response
