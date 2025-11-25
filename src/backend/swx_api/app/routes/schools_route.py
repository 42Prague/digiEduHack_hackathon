from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from swx_api.app.services import response_utils, schools_service
from swx_api.core.database.db import SessionDep

router = APIRouter(prefix="/schools")


@router.get("/search")
async def search_schools(
    query: str = Query(..., description="Name, district, or region query"),
    format: str = Query("json"),
):
    if not query:
        raise HTTPException(status_code=400, detail="query parameter is required")
    payload = {"results": schools_service.search_schools(query)}
    return response_utils.tone_or_json(payload, format)


@router.get("/compare")
async def compare_schools(
    names: str = Query(..., description="Comma-separated school names"),
    metric: str = Query(None, description="Optional metric to focus on: collaboration_score, mindset_shift_score, sentiment, teacher_confidence, intervention_effectiveness"),
    format: str = Query("json"),
):
    parsed: List[str] = [name.strip() for name in names.split(",") if name.strip()]
    if not parsed:
        raise HTTPException(status_code=400, detail="names parameter must contain at least one school")

    comparisons = schools_service.compare_schools(parsed, metric=metric)
    if not comparisons:
        raise HTTPException(status_code=404, detail="No matching schools found")
    payload = {"comparisons": comparisons}
    return response_utils.tone_or_json(payload, format)


@router.get("/compare_by_dimension")
async def compare_by_dimension(
    dimension: str = Query(..., description="Dimension to compare: school_type, intervention_type, participant_role"),
    school_type: Optional[str] = Query(None, description="Filter by school type"),
    intervention_type: Optional[str] = Query(None, description="Filter by intervention type"),
    participant_role: Optional[str] = Query(None, description="Filter by participant role"),
    date_from: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    db: SessionDep = None,
):
    """
    Compare data by dimension with optional filters.
    
    Args:
        dimension: Dimension to compare by
        school_type: Optional school type filter
        intervention_type: Optional intervention type filter
        participant_role: Optional participant role filter
        date_from: Optional start date
        date_to: Optional end date
        db: Database session
        
    Returns:
        Comparison results grouped by dimension
    """
    if dimension not in ["school_type", "intervention_type", "participant_role"]:
        raise HTTPException(
            status_code=400,
            detail="dimension must be one of: school_type, intervention_type, participant_role"
        )
    
    try:
        result = schools_service.compare_by_dimension(
            db=db,
            dimension=dimension,
            school_type=school_type,
            intervention_type=intervention_type,
            participant_role=participant_role,
            date_from=date_from,
            date_to=date_to,
        )
        return result
    except Exception as e:
        import logging
        logger = logging.getLogger("schools_route")
        logger.error(f"Error in compare_by_dimension: {e}", exc_info=True)
        # Return empty result instead of 500 error
        return {"dimension": dimension, "groups": {}}

