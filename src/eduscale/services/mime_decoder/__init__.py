"""
MIME Decoder Service

This service acts as the file processing coordinator in the data pipeline.
It receives Cloud Storage OBJECT_FINALIZE events from Eventarc, detects file types,
and routes files to the appropriate Transformer service for processing.
"""

from eduscale.services.mime_decoder.classifier import FileCategory, classify_mime_type
from eduscale.services.mime_decoder.models import (
    CloudEvent,
    StorageObjectData,
    ProcessingRequest,
)

__all__ = [
    "CloudEvent",
    "StorageObjectData",
    "ProcessingRequest",
    "FileCategory",
    "classify_mime_type",
]
