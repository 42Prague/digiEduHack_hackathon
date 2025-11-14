"""
Region Insights Service
-----------------------
Generates comprehensive insights and analytics for regions.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlmodel import Session, select, func

from swx_api.app.models.cultural_analysis import CulturalAnalysis
from swx_api.app.models.transcript import Transcript

logger = logging.getLogger("region_insights")


def get_region_insights(db: Session, region_id: str) -> Optional[Dict[str, Any]]:
    """
    Generate comprehensive insights for a region.
    
    Args:
        db: Database session
        region_id: Region identifier
        
    Returns:
        Region insights dictionary
    """
    try:
        # Get all transcripts for the region
        from sqlalchemy import text
        transcripts = db.exec(
            select(Transcript).where(
                text("upload_metadata->>'region_id' = :region_id").bindparams(region_id=region_id)
            )
        ).all()
    except Exception as e:
        logger.error(f"Database error in get_region_insights: {e}")
        return None
    
    if not transcripts:
        return None
    
    transcript_ids = [t.id for t in transcripts]
    
    # Get all cultural analysis for these transcripts
    analyses = db.exec(
        select(CulturalAnalysis).where(
            CulturalAnalysis.transcript_id.in_(transcript_ids)
        )
    ).all()
    
    if not analyses:
        return None
    
    # Calculate summary statistics
    total_count = len(analyses)
    
    avg_mindset_shift = sum(a.mindset_shift_score for a in analyses) / total_count
    avg_collaboration = sum(a.collaboration_score for a in analyses) / total_count
    avg_confidence = sum(a.teacher_confidence_score for a in analyses) / total_count
    avg_municipality = sum(a.municipality_cooperation_score for a in analyses) / total_count
    avg_sentiment = sum(a.sentiment_score for a in analyses) / total_count
    
    # Calculate medians
    mindset_scores = sorted([a.mindset_shift_score for a in analyses])
    collaboration_scores = sorted([a.collaboration_score for a in analyses])
    confidence_scores = sorted([a.teacher_confidence_score for a in analyses])
    
    median_mindset = mindset_scores[len(mindset_scores) // 2] if mindset_scores else 0
    median_collaboration = collaboration_scores[len(collaboration_scores) // 2] if collaboration_scores else 0
    median_confidence = confidence_scores[len(confidence_scores) // 2] if confidence_scores else 0
    
    # Find top schools (by average of all scores)
    school_scores = {}
    for transcript in transcripts:
        school_id = transcript.upload_metadata.get("school_id")
        if not school_id:
            continue
        
        analysis = next((a for a in analyses if a.transcript_id == transcript.id), None)
        if analysis:
            avg_score = (
                analysis.mindset_shift_score +
                analysis.collaboration_score +
                analysis.teacher_confidence_score +
                analysis.municipality_cooperation_score +
                analysis.sentiment_score
            ) / 5
            
            if school_id not in school_scores or avg_score > school_scores[school_id]["score"]:
                school_scores[school_id] = {
                    "score": avg_score,
                    "transcript_id": transcript.id,
                    "analysis": analysis,
                }
    
    # Sort schools by score
    top_schools = sorted(
        school_scores.items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )[:5]
    
    top_schools_list = [
        {
            "school_id": school_id,
            "average_score": data["score"],
            "mindset_shift": data["analysis"].mindset_shift_score,
            "collaboration": data["analysis"].collaboration_score,
            "teacher_confidence": data["analysis"].teacher_confidence_score,
        }
        for school_id, data in top_schools
    ]
    
    # Find schools needing support (bottom performers)
    bottom_schools = sorted(
        school_scores.items(),
        key=lambda x: x[1]["score"],
        reverse=False
    )[:5]
    
    schools_needing_support = [
        {
            "school_id": school_id,
            "average_score": data["score"],
            "mindset_shift": data["analysis"].mindset_shift_score,
            "collaboration": data["analysis"].collaboration_score,
            "teacher_confidence": data["analysis"].teacher_confidence_score,
        }
        for school_id, data in bottom_schools
    ]
    
    # Analyze intervention effectiveness
    intervention_scores = {}
    for transcript in transcripts:
        intervention_type = transcript.upload_metadata.get("intervention_type")
        if not intervention_type:
            continue
        
        analysis = next((a for a in analyses if a.transcript_id == transcript.id), None)
        if analysis:
            if intervention_type not in intervention_scores:
                intervention_scores[intervention_type] = []
            
            intervention_scores[intervention_type].append({
                "mindset_shift": analysis.mindset_shift_score,
                "collaboration": analysis.collaboration_score,
                "teacher_confidence": analysis.teacher_confidence_score,
                "municipality_cooperation": analysis.municipality_cooperation_score,
                "sentiment": analysis.sentiment_score,
            })
    
    # Calculate averages per intervention
    intervention_effectiveness = {}
    for intervention_type, scores_list in intervention_scores.items():
        count = len(scores_list)
        if count > 0:
            intervention_effectiveness[intervention_type] = {
                "count": count,
                "avg_mindset_shift": sum(s["mindset_shift"] for s in scores_list) / count,
                "avg_collaboration": sum(s["collaboration"] for s in scores_list) / count,
                "avg_teacher_confidence": sum(s["teacher_confidence"] for s in scores_list) / count,
                "avg_municipality_cooperation": sum(s["municipality_cooperation"] for s in scores_list) / count,
                "avg_sentiment": sum(s["sentiment"] for s in scores_list) / count,
            }
    
    # Extract frequent themes
    all_themes = []
    for analysis in analyses:
        if analysis.themes:
            all_themes.extend(analysis.themes)
    
    # Count theme frequency
    theme_counts = {}
    for theme in all_themes:
        theme_counts[theme] = theme_counts.get(theme, 0) + 1
    
    frequent_themes = sorted(
        theme_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    return {
        "region_id": region_id,
        "summary": {
            "total_transcripts": total_count,
            "avg_mindset_shift": round(avg_mindset_shift, 2),
            "avg_collaboration": round(avg_collaboration, 2),
            "avg_confidence": round(avg_confidence, 2),
            "avg_municipality_cooperation": round(avg_municipality, 2),
            "avg_sentiment": round(avg_sentiment, 2),
            "median_mindset_shift": median_mindset,
            "median_collaboration": median_collaboration,
            "median_teacher_confidence": median_confidence,
        },
        "top_schools": top_schools_list,
        "schools_needing_support": schools_needing_support,
        "intervention_effectiveness": intervention_effectiveness,
        "frequent_themes": [{"theme": theme, "count": count} for theme, count in frequent_themes],
    }

