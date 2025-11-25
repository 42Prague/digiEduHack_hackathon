from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from swx_api.app.services import analytics_service, nlp_service, response_utils
from swx_api.app.services.recommendations_service import get_recommendations
from swx_api.app.services.region_insights_service import get_region_insights
from swx_api.core.database.db import SessionDep

router = APIRouter(prefix="/analytics")


@router.get("/summary")
async def analytics_summary(format: str = Query("json")):
    payload = analytics_service.get_combined_metrics()
    return response_utils.tone_or_json(payload, format)


@router.get("/trends")
async def analytics_trends(
    metric: str = Query(..., description="Metric/column name to track across regions"),
    format: str = Query("json"),
    db: SessionDep = None,
):
    if not metric:
        raise HTTPException(status_code=400, detail="metric parameter is required")
    payload = analytics_service.get_metric_trend(metric, db_session=db)
    return response_utils.tone_or_json(payload, format)


@router.get("/themes")
async def analytics_themes(format: str = Query("json")):
    payload = {"themes": nlp_service.get_all_themes()}
    return response_utils.tone_or_json(payload, format)


@router.get("/cost-benefit")
async def analytics_cost_benefit(
    intervention: str = Query(..., description="Intervention name (e.g., 'teacher_training', 'mentoring')"),
    metric: str = Query(..., description="Outcome metric to measure (e.g., 'student_satisfaction', 'test_scores')"),
    cost: float = Query(None, description="Optional cost per participant (CZK)"),
    format: str = Query("json"),
):
    """Calculate cost-benefit analysis for an intervention."""
    if not intervention or not metric:
        raise HTTPException(status_code=400, detail="intervention and metric parameters are required")
    payload = analytics_service.calculate_cost_benefit(intervention, metric, cost)
    return response_utils.tone_or_json(payload, format)


@router.get("/regions")
async def analytics_regions(format: str = Query("json")):
    """Get all unique regions across all datasets for multi-level filtering."""
    from swx_api.app.services import ingestion_service
    
    all_regions = set()
    for dataset in ingestion_service.list_datasets():
        summary_path = Path(dataset.get("summary_path", ""))
        if summary_path.exists():
            import json
            with summary_path.open("r", encoding="utf-8") as fp:
                summary_data = json.load(fp)
                summary = summary_data.get("summary", {})
                regions = summary.get("regions")
                if regions:
                    all_regions.update(regions)
    
    payload = {
        "regions": sorted(list(all_regions)),
        "count": len(all_regions),
    }
    return response_utils.tone_or_json(payload, format)


@router.get("/recommendations")
async def analytics_recommendations(
    school_id: str = Query(None, description="School identifier"),
    region_id: str = Query(None, description="Region identifier"),
    db: SessionDep = None,
):
    """
    Get AI-powered recommendations for a school or region.
    
    Args:
        school_id: Optional school identifier
        region_id: Optional region identifier
        db: Database session
        
    Returns:
        Recommendations dictionary
    """
    # Allow calling without params - return empty recommendations
    if not school_id and not region_id:
        return {
            "school_recommendations": [],
            "region_recommendations": [],
            "intervention_recommendations": [],
            "culture_warnings": [],
            "strengths": [],
        }
    
    try:
        recommendations = get_recommendations(db, school_id=school_id, region_id=region_id)
        return recommendations
    except Exception as e:
        import logging
        logger = logging.getLogger("analytics_route")
        logger.warning(f"Error in recommendations: {e}")
        # Return empty recommendations instead of 500 error
        return {
            "school_recommendations": [],
            "region_recommendations": [],
            "intervention_recommendations": [],
            "culture_warnings": [],
            "strengths": [],
        }


@router.get("/region_insights")
async def analytics_region_insights(
    region_id: str = Query(..., description="Region identifier"),
    db: SessionDep = None,
):
    """
    Get comprehensive insights for a region.
    
    Args:
        region_id: Region identifier
        db: Database session
        
    Returns:
        Region insights dictionary
    """
    try:
        insights = get_region_insights(db, region_id)
        if not insights:
            # Return empty insights structure instead of 404 for graceful degradation
            return {
                "region_id": region_id,
                "summary": {
                    "total_transcripts": 0,
                    "avg_mindset_shift": 0,
                    "avg_collaboration": 0,
                    "avg_confidence": 0,
                    "avg_municipality_cooperation": 0,
                    "avg_sentiment": 0,
                },
                "top_schools": [],
                "schools_needing_support": [],
                "intervention_effectiveness": {},
                "frequent_themes": [],
            }
        return insights
    except Exception as e:
        import logging
        logger = logging.getLogger("analytics_route")
        logger.warning(f"Error in region_insights for {region_id}: {e}")
        # Return empty insights structure instead of error
        return {
            "region_id": region_id,
            "summary": {
                "total_transcripts": 0,
                "avg_mindset_shift": 0,
                "avg_collaboration": 0,
                "avg_confidence": 0,
                "avg_municipality_cooperation": 0,
                "avg_sentiment": 0,
            },
            "top_schools": [],
            "schools_needing_support": [],
            "intervention_effectiveness": {},
            "frequent_themes": [],
        }

