"""
Cultural Analysis Model
-----------------------
Database model for storing cultural analysis results from transcript analysis.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, ForeignKey, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel, Relationship

from swx_api.core.models.base import Base


class CulturalAnalysis(Base, table=True):
    """
    Database model for cultural analysis results.
    
    Stores detailed cultural analysis scores and insights from transcript analysis.
    """
    
    __tablename__ = "cultural_analysis"
    __table_args__ = {"extend_existing": True}
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Foreign key to transcript
    transcript_id: uuid.UUID = Field(
        foreign_key="transcripts.id",
        description="Reference to the transcript record"
    )
    
    # Cultural scores (0-100)
    mindset_shift_score: int = Field(
        default=0,
        description="Mindset shift score (0-100)"
    )
    
    collaboration_score: int = Field(
        default=0,
        description="Collaboration score (0-100)"
    )
    
    teacher_confidence_score: int = Field(
        default=0,
        description="Teacher confidence score (0-100)"
    )
    
    municipality_cooperation_score: int = Field(
        default=0,
        description="Municipality cooperation score (0-100)"
    )
    
    sentiment_score: int = Field(
        default=50,
        description="Sentiment score (0-100)"
    )
    
    # Themes (stored as JSON array)
    themes: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Extracted themes from transcript"
    )
    
    # Textual insights
    practical_change: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Description of practical changes observed"
    )
    
    mindset_change: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Description of mindset changes observed"
    )
    
    impact_summary: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="5-7 sentence summary of intervention impact"
    )
    
    # Culture change detection
    culture_change_detected: bool = Field(
        default=False,
        description="Whether culture change was detected"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CulturalAnalysisCreate(SQLModel):
    """Schema for creating a cultural analysis record."""
    transcript_id: uuid.UUID
    mindset_shift_score: int = 0
    collaboration_score: int = 0
    teacher_confidence_score: int = 0
    municipality_cooperation_score: int = 0
    sentiment_score: int = 50
    themes: Optional[List[str]] = None
    practical_change: Optional[str] = None
    mindset_change: Optional[str] = None
    impact_summary: Optional[str] = None
    culture_change_detected: bool = False


class CulturalAnalysisPublic(SQLModel):
    """Public schema for cultural analysis responses."""
    id: uuid.UUID
    transcript_id: uuid.UUID
    mindset_shift_score: int
    collaboration_score: int
    teacher_confidence_score: int
    municipality_cooperation_score: int
    sentiment_score: int
    themes: Optional[List[str]] = None
    practical_change: Optional[str] = None
    mindset_change: Optional[str] = None
    impact_summary: Optional[str] = None
    culture_change_detected: bool
    created_at: datetime

