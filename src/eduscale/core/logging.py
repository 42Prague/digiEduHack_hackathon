"""Logging configuration for EduScale Engine."""

import contextvars
import json
import logging
import sys
import traceback
from datetime import datetime
from typing import Any, Dict

# Context variable for storing GCS URI in request scope
gcs_uri_context: contextvars.ContextVar[str | None] = contextvars.ContextVar("gcs_uri", default=None)


class CloudLoggingFormatter(logging.Formatter):
    """JSON formatter for Google Cloud Logging.

    Formats log records as single-line JSON objects that Cloud Logging
    can properly parse and display. Exceptions and tracebacks are included
    as strings within the JSON structure.
    """

    # Map Python logging levels to Cloud Logging severity
    SEVERITY_MAP = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as single-line JSON.

        Args:
            record: Log record to format

        Returns:
            Single-line JSON string
        """
        # Base log entry
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "severity": self.SEVERITY_MAP.get(record.levelno, "DEFAULT"),
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add GCS URI from context if available
        gcs_uri = gcs_uri_context.get()
        if gcs_uri:
            log_entry["gcs_uri"] = gcs_uri

        # Add extra fields from logger.info(..., extra={...})
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                # Skip standard fields
                if key not in [
                    "name", "msg", "args", "created", "filename", "funcName",
                    "levelname", "levelno", "lineno", "module", "msecs",
                    "message", "pathname", "process", "processName",
                    "relativeCreated", "thread", "threadName", "exc_info",
                    "exc_text", "stack_info", "getMessage",
                ]:
                    log_entry[key] = value

        # Add exception information if present
        if record.exc_info:
            # Format traceback as single string
            exc_text = "".join(traceback.format_exception(*record.exc_info))
            log_entry["exception"] = exc_text
            log_entry["exception_type"] = record.exc_info[0].__name__ if record.exc_info[0] else "Unknown"
            log_entry["exception_message"] = str(record.exc_info[1]) if record.exc_info[1] else ""

        # Convert to single-line JSON
        return json.dumps(log_entry, default=str, ensure_ascii=False)


def setup_logging() -> None:
    """Configure structured logging for the application.

    Sets up logging to output structured logs to stdout, suitable for
    Cloud Run log ingestion. Log level is set based on environment.

    For Cloud environments (non-local), uses JSON formatting for proper
    Cloud Logging integration. For local development, uses simple text format.
    """
    from eduscale.core.config import settings

    # Determine log level based on environment
    log_level = logging.DEBUG if settings.ENV == "local" else logging.INFO

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    # Use JSON formatter for cloud environments, simple format for local
    if settings.ENV == "local":
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    else:
        formatter = CloudLoggingFormatter()

    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Set uvicorn loggers to appropriate level
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.setLevel(log_level)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.addHandler(handler)
        uvicorn_logger.propagate = False
