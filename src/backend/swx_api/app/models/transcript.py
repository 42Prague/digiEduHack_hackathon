"""
Transcript Model
----------------
Database model for storing audio/transcript ingestion with metadata and cultural analysis.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from swx_api.core.models.base import Base


class Transcript(Base, table=True):
    """
    Database model for transcript records.
    
    Stores audio/transcript files with metadata, transcription text,
    and cultural analysis results.
    """
    
    __tablename__ = "transcripts"
    __table_args__ = {"extend_existing": True}
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # File information
    file_type: str = Field(description="Type: 'audio' or 'transcript'")
    original_filename: str = Field(max_length=500)
    
    # File paths (stored as JSON for flexibility)
    file_paths: Dict[str, str] = Field(
        default_factory=dict,
        sa_column=Column(JSONB),
        description="Paths to raw file, transcript, metadata, cultural analysis, etc."
    )
    
    # Metadata (from client) - using upload_metadata to avoid SQLAlchemy reserved name conflict
    upload_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB),
        description="Uploaded metadata: school_id, region_id, school_type, etc."
    )
    
    # Transcript text
    transcript_text: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Transcribed or uploaded text content"
    )
    
    clean_text: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Cleaned transcript text"
    )
    
    # File paths (explicit fields for easier querying)
    raw_file_path: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Path to raw uploaded file"
    )
    
    transcript_path: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Path to processed transcript file"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TranscriptCreate(SQLModel):
    """Schema for creating a transcript record."""
    file_type: str
    original_filename: str
    file_paths: Dict[str, str]
    upload_metadata: Dict[str, Any]
    transcript_text: Optional[str] = None
    cultural_scores: Optional[Dict[str, Any]] = None
    themes: Optional[list] = None
    sentiment: Optional[float] = None


class TranscriptPublic(SQLModel):
    """Public schema for transcript responses."""
    id: uuid.UUID
    file_type: str
    original_filename: str
    metadata: Dict[str, Any]  # Alias for upload_metadata in response
    transcript_available: bool
    cultural_analysis: Optional[Dict[str, Any]] = None
    created_at: datetime
    message: Optional[str] = None

