"""
CloudEvents models for MIME Decoder service.

Implements CloudEvents 1.0 specification for Cloud Storage events.
See: https://github.com/cloudevents/spec/blob/v1.0/spec.md
"""

import logging
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class StorageObjectData(BaseModel):
    """
    Cloud Storage object metadata from OBJECT_FINALIZE event.

    This contains the actual file information from the Cloud Storage event payload.
    """

    bucket: str = Field(..., description="Cloud Storage bucket name")
    name: str = Field(..., description="Object path (file name)")
    contentType: str = Field(
        ..., alias="contentType", description="MIME type of the file"
    )
    size: str = Field(..., description="File size in bytes (as string)")
    timeCreated: datetime = Field(
        ..., alias="timeCreated", description="Timestamp when file was created"
    )
    updated: datetime = Field(
        ..., description="Timestamp when file was last updated"
    )
    generation: Optional[str] = Field(
        None, description="Object generation number for versioning"
    )
    metageneration: Optional[str] = Field(
        None, description="Object metadata generation number"
    )

    class Config:
        populate_by_name = True


class CloudEvent(BaseModel):
    """
    CloudEvents 1.0 specification for Cloud Storage events.

    Eventarc delivers events in this format to Cloud Run services.
    See: https://cloud.google.com/eventarc/docs/cloudevents
    """

    specversion: str = Field(
        ..., description="CloudEvents specification version (always '1.0')"
    )
    type: str = Field(..., description="Event type (e.g., 'google.cloud.storage.object.v1.finalized')")
    source: str = Field(..., description="Event source (Cloud Storage bucket URI)")
    subject: str = Field(..., description="Subject of the event (object path)")
    id: str = Field(..., description="Unique event identifier")
    time: datetime = Field(..., description="Timestamp when event occurred")
    datacontenttype: str = Field(
        ..., description="Content type of the data payload (always 'application/json')"
    )
    data: StorageObjectData = Field(..., description="Event payload with file metadata")


class ProcessingRequest(BaseModel):
    """
    Internal processing request after file type classification.

    This is passed to downstream services (Transformer, Tabular) for further processing.
    """

    file_id: str = Field(..., description="Unique file identifier (derived from object name)")
    region_id: str = Field(..., description="Region identifier (extracted from object path)")
    bucket: str = Field(..., description="Cloud Storage bucket name")
    object_name: str = Field(..., description="Object path in bucket")
    content_type: str = Field(..., description="MIME type of the file")
    file_category: str = Field(
        ..., description="Classified file category (text, csv, excel, image, audio, archive, other)"
    )
    size_bytes: int = Field(..., description="File size in bytes")
    event_id: str = Field(..., description="Original CloudEvent ID for tracing")
    timestamp: datetime = Field(..., description="Event timestamp")

    @classmethod
    def from_cloud_event(cls, event: CloudEvent, file_category: str) -> "ProcessingRequest":
        """
        Create a ProcessingRequest from a CloudEvent and classified file category.
        
        Extracts file_id and region_id from object path pattern: uploads/{region_id}/{file_id}.{ext}

        Args:
            event: The CloudEvent received from Eventarc
            file_category: The classified file category (text, image, audio, etc.)

        Returns:
            ProcessingRequest ready for downstream processing
        """
        object_path = event.data.name
        
        # Parse path pattern: uploads/{region_id}/{file_id}_{original_filename}
        # Example: uploads/region-cz-01/abc123_report.pdf
        path_pattern = r"^uploads/([^/]+)/([^_]+)_(.+)$"
        match = re.match(path_pattern, object_path)
        
        if match:
            region_id = match.group(1)
            file_id = match.group(2)
            original_filename = match.group(3)
            logger.info(
                f"Extracted metadata from path",
                extra={
                    "object_path": object_path,
                    "region_id": region_id,
                    "file_id": file_id,
                    "original_filename": original_filename
                }
            )
        else:
            # Fallback: use defaults if path doesn't match expected pattern
            logger.warning(
                f"Object path does not match expected pattern 'uploads/{{region_id}}/{{file_id}}_{{filename}}'",
                extra={
                    "object_path": object_path,
                    "expected_pattern": "uploads/{region_id}/{file_id}_{filename}"
                }
            )
            # Extract file_id from filename (last part of path, first part before underscore)
            filename = object_path.split("/")[-1]
            file_id = filename.split("_")[0] if "_" in filename else filename.split(".")[0]
            region_id = "unknown"

        return cls(
            file_id=file_id,
            region_id=region_id,
            bucket=event.data.bucket,
            object_name=event.data.name,
            content_type=event.data.contentType,
            file_category=file_category,
            size_bytes=int(event.data.size),
            event_id=event.id,
            timestamp=event.time,
        )
