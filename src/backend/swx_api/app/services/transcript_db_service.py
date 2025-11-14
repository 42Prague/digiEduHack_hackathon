"""
Transcript Database Service
---------------------------
Handles database operations for transcript records and cultural analysis.
"""

import logging
import uuid
from typing import Optional, Dict, Any
from sqlmodel import Session, select

from swx_api.app.models.transcript import Transcript, TranscriptCreate
from swx_api.app.models.cultural_analysis import (
    CulturalAnalysis,
    CulturalAnalysisCreate,
)

logger = logging.getLogger("transcript_db")


def create_transcript_record(
    db: Session,
    transcript_data: TranscriptCreate
) -> Transcript:
    """
    Create a new transcript record in the database.
    
    Args:
        db: Database session
        transcript_data: Transcript data to create
        
    Returns:
        Created Transcript record
    """
    transcript = Transcript(**transcript_data.model_dump())
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    
    logger.info(f"Created transcript record: {transcript.id}")
    return transcript


def get_transcript_by_id(db: Session, transcript_id: str) -> Optional[Transcript]:
    """
    Get transcript by ID.
    
    Args:
        db: Database session
        transcript_id: UUID string
        
    Returns:
        Transcript record or None
    """
    try:
        import uuid
        record_id = uuid.UUID(transcript_id)
        statement = select(Transcript).where(Transcript.id == record_id)
        return db.exec(statement).first()
    except (ValueError, Exception) as e:
        logger.error(f"Error fetching transcript {transcript_id}: {e}")
        return None


def create_cultural_analysis_record(
    db: Session,
    cultural_data: CulturalAnalysisCreate
) -> CulturalAnalysis:
    """
    Create a new cultural analysis record in the database.
    
    Args:
        db: Database session
        cultural_data: Cultural analysis data to create
        
    Returns:
        Created CulturalAnalysis record
    """
    analysis = CulturalAnalysis(**cultural_data.model_dump())
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    logger.info(f"Created cultural analysis record: {analysis.id} for transcript {analysis.transcript_id}")
    return analysis


def get_cultural_analysis_by_transcript_id(
    db: Session,
    transcript_id: uuid.UUID
) -> Optional[CulturalAnalysis]:
    """
    Get cultural analysis by transcript ID.
    
    Args:
        db: Database session
        transcript_id: Transcript UUID
        
    Returns:
        CulturalAnalysis record or None
    """
    try:
        statement = select(CulturalAnalysis).where(
            CulturalAnalysis.transcript_id == transcript_id
        )
        return db.exec(statement).first()
    except Exception as e:
        logger.error(f"Error fetching cultural analysis for transcript {transcript_id}: {e}")
        return None

