"""
Transcript Routes
-----------------
API endpoints for transcript management and retrieval.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException
from sqlmodel import Session, select, and_, or_

from swx_api.app.models.transcript import Transcript, TranscriptPublic
from swx_api.app.models.cultural_analysis import CulturalAnalysis
from swx_api.app.services.transcript_db_service import (
    get_transcript_by_id,
    get_cultural_analysis_by_transcript_id,
)
from swx_api.app.services.data_quality_service import get_dq_report
from swx_api.core.database.db import SessionDep

router = APIRouter(prefix="/transcripts")
logger = logging.getLogger("transcripts_route")


@router.get("/{transcript_id}")
async def get_transcript(
    transcript_id: str,
    db: SessionDep,
):
    """
    Get a full transcript record by ID.
    
    Returns:
        Complete transcript record with metadata, text, cultural analysis, and DQ report
    """
    try:
        from sqlalchemy.exc import OperationalError
        
        # Get transcript from database
        try:
            transcript = get_transcript_by_id(db, transcript_id)
        except OperationalError as e:
            logger.warning(f"Database connection error when fetching transcript {transcript_id}: {e}")
            raise HTTPException(
                status_code=503,
                detail="Database unavailable. Please try again later."
            )
        
        if not transcript:
            raise HTTPException(
                status_code=404,
                detail=f"Transcript not found: {transcript_id}"
            )
        
        # Get cultural analysis
        cultural_analysis = None
        cultural_analysis_record = get_cultural_analysis_by_transcript_id(db, transcript.id)
        
        if cultural_analysis_record:
            cultural_analysis = {
                "mindset_shift_score": cultural_analysis_record.mindset_shift_score,
                "collaboration_score": cultural_analysis_record.collaboration_score,
                "teacher_confidence_score": cultural_analysis_record.teacher_confidence_score,
                "municipality_cooperation_score": cultural_analysis_record.municipality_cooperation_score,
                "sentiment_score": cultural_analysis_record.sentiment_score,
                "themes": cultural_analysis_record.themes or [],
                "practical_change": cultural_analysis_record.practical_change,
                "mindset_change": cultural_analysis_record.mindset_change,
                "impact_summary": cultural_analysis_record.impact_summary,
                "culture_change_detected": cultural_analysis_record.culture_change_detected,
            }
        
        # Get DQ report if available
        dq_report = None
        if transcript.file_paths and "cultural_analysis" in transcript.file_paths:
            # Try to get DQ report from dataset name
            dataset_name = Path(transcript.file_paths.get("cultural_analysis", "")).stem.replace("_cultural", "")
            try:
                dq_report = get_dq_report(dataset_name)
            except Exception as e:
                logger.warning(f"Could not load DQ report for {dataset_name}: {e}")
        
        # Build response
        response = {
            "id": str(transcript.id),
            "metadata": transcript.upload_metadata,
            "transcript_text": transcript.transcript_text,
            "clean_text": transcript.clean_text,
            "cultural_analysis": cultural_analysis,
            "dq_report": dq_report,
            "file_paths": transcript.file_paths,
            "file_type": transcript.file_type,
            "original_filename": transcript.original_filename,
            "created_at": transcript.created_at.isoformat() if transcript.created_at else None,
            "updated_at": transcript.updated_at.isoformat() if transcript.updated_at else None,
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transcript {transcript_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/")
async def list_transcripts(
    db: SessionDep,
    school_id: Optional[str] = Query(None, description="Filter by school ID"),
    region_id: Optional[str] = Query(None, description="Filter by region ID"),
    school_type: Optional[str] = Query(None, description="Filter by school type"),
    intervention_type: Optional[str] = Query(None, description="Filter by intervention type"),
    participant_role: Optional[str] = Query(None, description="Filter by participant role"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
):
    """
    List transcripts with optional filters.
    
    Returns:
        List of transcript summaries
    """
    try:
        from sqlalchemy import text
        from sqlalchemy.exc import OperationalError
        
        # Build query
        query = select(Transcript)
        conditions = []
        
        # Apply filters using JSONB queries
        if school_id:
            conditions.append(
                text("upload_metadata->>'school_id' = :school_id").bindparams(school_id=school_id)
            )
        if region_id:
            conditions.append(
                text("upload_metadata->>'region_id' = :region_id").bindparams(region_id=region_id)
            )
        if school_type:
            conditions.append(
                text("upload_metadata->>'school_type' = :school_type").bindparams(school_type=school_type)
            )
        if intervention_type:
            conditions.append(
                text("upload_metadata->>'intervention_type' = :intervention_type").bindparams(intervention_type=intervention_type)
            )
        if participant_role:
            conditions.append(
                text("upload_metadata->>'participant_role' = :participant_role").bindparams(participant_role=participant_role)
            )
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                conditions.append(Transcript.created_at >= date_from_obj)
            except ValueError:
                pass
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
                conditions.append(Transcript.created_at <= date_to_obj)
            except ValueError:
                pass
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Execute query
        transcripts = db.exec(query).all()
        
        # Build response
        results = []
        for transcript in transcripts:
            metadata = transcript.upload_metadata or {}
            results.append({
                "id": str(transcript.id),
                "school_id": metadata.get("school_id"),
                "region_id": metadata.get("region_id"),
                "school_type": metadata.get("school_type"),
                "intervention_type": metadata.get("intervention_type"),
                "participant_role": metadata.get("participant_role"),
                "interview_date": metadata.get("interview_date"),
                "created_at": transcript.created_at.isoformat() if transcript.created_at else None,
            })
        
        return results
        
    except OperationalError as e:
        # Database connection error - return empty array for graceful degradation
        logger.warning(f"Database connection error when listing transcripts: {e}. Returning empty list.")
        return []
    except Exception as e:
        logger.error(f"Error listing transcripts: {e}", exc_info=True)
        # Return empty array instead of crashing for hackathon demo
        return []

