"""
Recommendations Service
-----------------------
Generates AI-powered recommendations based on cultural analysis scores and metadata.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlmodel import Session, select, func

from swx_api.app.models.cultural_analysis import CulturalAnalysis
from swx_api.app.models.transcript import Transcript
from swx_api.app.services.llm_client import LLMClient, LLMConfig

logger = logging.getLogger("recommendations")


def get_average_scores_by_region(db: Session, region_id: str) -> Dict[str, float]:
    """
    Calculate average cultural scores for a region.
    
    Args:
        db: Database session
        region_id: Region identifier
        
    Returns:
        Dictionary with average scores
    """
    try:
        # Get all transcripts for the region
        # Note: JSONB query syntax may vary by database - using text search for compatibility
        from sqlalchemy import text
        transcripts = db.exec(
            select(Transcript).where(
                text("upload_metadata->>'region_id' = :region_id").bindparams(region_id=region_id)
            )
        ).all()
    except Exception as e:
        logger.error(f"Database error in get_average_scores_by_region: {e}")
        return {}
    
    if not transcripts:
        return {}
    
    transcript_ids = [t.id for t in transcripts]
    
    # Get cultural analysis for these transcripts
    analyses = db.exec(
        select(CulturalAnalysis).where(
            CulturalAnalysis.transcript_id.in_(transcript_ids)
        )
    ).all()
    
    if not analyses:
        return {}
    
    # Calculate averages
    totals = {
        "mindset_shift": 0,
        "collaboration": 0,
        "teacher_confidence": 0,
        "municipality_cooperation": 0,
        "sentiment": 0,
    }
    
    count = len(analyses)
    for analysis in analyses:
        totals["mindset_shift"] += analysis.mindset_shift_score
        totals["collaboration"] += analysis.collaboration_score
        totals["teacher_confidence"] += analysis.teacher_confidence_score
        totals["municipality_cooperation"] += analysis.municipality_cooperation_score
        totals["sentiment"] += analysis.sentiment_score
    
    return {
        "avg_mindset_shift": totals["mindset_shift"] / count,
        "avg_collaboration": totals["collaboration"] / count,
        "avg_teacher_confidence": totals["teacher_confidence"] / count,
        "avg_municipality_cooperation": totals["municipality_cooperation"] / count,
        "avg_sentiment": totals["sentiment"] / count,
    }


def generate_rule_based_recommendations(
    scores: Dict[str, int],
    region_averages: Dict[str, float],
    metadata: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    Generate rule-based recommendations.
    
    Args:
        scores: Cultural scores for the school/transcript
        region_averages: Average scores for the region
        metadata: Metadata (school_type, intervention_type, etc.)
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    collaboration = scores.get("collaboration_score", 0)
    avg_collaboration = region_averages.get("avg_collaboration", 50)
    
    if collaboration < avg_collaboration:
        recommendations.append({
            "type": "intervention",
            "category": "collaboration",
            "title": "Improve Team Collaboration",
            "description": "Collaboration score is below region average. Consider implementing team-building workshops or collaborative teaching practices.",
            "priority": "high"
        })
    
    teacher_confidence = scores.get("teacher_confidence_score", 0)
    avg_confidence = region_averages.get("avg_teacher_confidence", 50)
    
    if teacher_confidence < avg_confidence:
        recommendations.append({
            "type": "intervention",
            "category": "leadership",
            "title": "Enhance Teacher Confidence",
            "description": "Teacher confidence is below average. Recommend leadership support programs, mentoring, or professional development opportunities.",
            "priority": "high"
        })
    
    municipality_cooperation = scores.get("municipality_cooperation_score", 0)
    avg_municipality = region_averages.get("avg_municipality_cooperation", 50)
    
    if municipality_cooperation < avg_municipality:
        recommendations.append({
            "type": "intervention",
            "category": "municipality",
            "title": "Strengthen Municipal Cooperation",
            "description": "Municipality cooperation is below average. Suggest regular meetings with municipal education department and joint planning sessions.",
            "priority": "medium"
        })
    
    mindset_shift = scores.get("mindset_shift_score", 0)
    avg_mindset = region_averages.get("avg_mindset_shift", 50)
    
    if mindset_shift < avg_mindset:
        recommendations.append({
            "type": "intervention",
            "category": "mindset",
            "title": "Promote Mindset Shift",
            "description": "Mindset shift score is below average. Consider implementing mentoring programs or culture change initiatives.",
            "priority": "high"
        })
    
    return recommendations


def generate_ai_recommendations(
    scores: Dict[str, int],
    metadata: Dict[str, Any],
    rule_based: List[Dict[str, str]]
) -> str:
    """
    Generate AI-powered recommendation text using LLM.
    
    Args:
        scores: Cultural scores
        metadata: Metadata
        rule_based: Rule-based recommendations
        
    Returns:
        AI-generated recommendation text
    """
    try:
        # Prefer Featherless.ai if available (same as cultural analysis)
        import os
        config = LLMConfig.from_env()
        
        # Override to use Featherless if available, otherwise use configured provider
        if not config.api_key or config.provider != "featherless":
            # Try to get Featherless API key
            featherless_key = os.getenv("FEATHERLESS_API_KEY")
            if featherless_key:
                config = LLMConfig(
                    provider="featherless",
                    model=os.getenv("INGESTION_LLM_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct"),
                    api_key=featherless_key,
                )
                logger.info("Using Featherless.ai for AI recommendations")
            else:
                logger.warning("FEATHERLESS_API_KEY not set, using configured provider for recommendations")
        
        client = LLMClient(config)
        
        prompt = f"""Given these cultural analysis scores and metadata, write 3 specific recommendations for improvement.

Scores:
- Mindset Shift: {scores.get('mindset_shift_score', 0)}/100
- Collaboration: {scores.get('collaboration_score', 0)}/100
- Teacher Confidence: {scores.get('teacher_confidence_score', 0)}/100
- Municipality Cooperation: {scores.get('municipality_cooperation_score', 0)}/100
- Sentiment: {scores.get('sentiment_score', 50)}/100

Metadata:
- School Type: {metadata.get('school_type', 'unknown')}
- Intervention Type: {metadata.get('intervention_type', 'unknown')}
- Region: {metadata.get('region_id', 'unknown')}

Rule-based recommendations identified:
{chr(10).join([f"- {r['title']}: {r['description']}" for r in rule_based[:3]])}

Write 3 actionable recommendations (2-3 sentences each) that build on these insights.
Focus on practical, implementable actions.
Return only the recommendations, one per line."""
        
        response = client.ai_analyze(prompt)
        return response.strip()
        
    except Exception as e:
        logger.error(f"AI recommendation generation failed: {e}")
        return "AI recommendations unavailable. Please refer to rule-based recommendations above."


def get_recommendations(
    db: Session,
    school_id: Optional[str] = None,
    region_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate recommendations for a school or region.
    
    Args:
        db: Database session
        school_id: Optional school identifier
        region_id: Optional region identifier
        
    Returns:
        Recommendations dictionary
    """
    # Get region averages
    if region_id:
        region_averages = get_average_scores_by_region(db, region_id)
    else:
        region_averages = {}
    
    # Get school-specific data if provided
    school_recommendations = []
    region_recommendations = []
    intervention_recommendations = []
    culture_warnings = []
    strengths = []
    
    if school_id:
        try:
            # Get transcripts for this school
            from sqlalchemy import text
            transcripts = db.exec(
                select(Transcript).where(
                    text("upload_metadata->>'school_id' = :school_id").bindparams(school_id=school_id)
                )
            ).all()
        except Exception as e:
            logger.error(f"Database error fetching transcripts for school {school_id}: {e}")
            transcripts = []
        
        if transcripts:
            # Get latest cultural analysis
            from swx_api.app.services.transcript_db_service import get_cultural_analysis_by_transcript_id
            
            latest_transcript = transcripts[-1]  # Most recent
            analysis = get_cultural_analysis_by_transcript_id(db, latest_transcript.id)
            
            if analysis:
                scores = {
                    "mindset_shift_score": analysis.mindset_shift_score,
                    "collaboration_score": analysis.collaboration_score,
                    "teacher_confidence_score": analysis.teacher_confidence_score,
                    "municipality_cooperation_score": analysis.municipality_cooperation_score,
                    "sentiment_score": analysis.sentiment_score,
                }
                
                metadata = latest_transcript.upload_metadata
                
                # Generate rule-based recommendations
                rule_based = generate_rule_based_recommendations(
                    scores, region_averages, metadata
                )
                school_recommendations = rule_based
                
                # Generate AI recommendations
                try:
                    ai_text = generate_ai_recommendations(scores, metadata, rule_based)
                    # Split AI text into individual recommendations if it's multi-line
                    if ai_text and ai_text.strip() and not ai_text.startswith("Analysis not available"):
                        # Split by newlines and filter empty lines
                        ai_recommendations = [line.strip() for line in ai_text.split('\n') if line.strip()]
                        for rec_text in ai_recommendations[:3]:  # Limit to 3 recommendations
                            school_recommendations.append({
                                "type": "ai",
                                "category": "general",
                                "title": "AI-Generated Recommendation",
                                "description": rec_text,
                                "priority": "medium"
                            })
                    else:
                        # If AI failed, add a note but don't add empty recommendation
                        logger.warning("AI recommendations generation returned empty or error message")
                except Exception as e:
                    logger.error(f"Failed to generate AI recommendations: {e}")
                    # Don't add failed AI recommendation to the list
                
                # Identify strengths
                if analysis.collaboration_score >= 80:
                    strengths.append("Strong collaboration culture")
                if analysis.teacher_confidence_score >= 80:
                    strengths.append("High teacher confidence")
                if analysis.municipality_cooperation_score >= 80:
                    strengths.append("Excellent municipal cooperation")
                
                # Culture warnings
                if not analysis.culture_change_detected:
                    culture_warnings.append("No significant culture change detected. Consider intervention review.")
                if analysis.sentiment_score < 40:
                    culture_warnings.append("Low sentiment detected. May need additional support.")
    
    return {
        "school_recommendations": school_recommendations,
        "region_recommendations": region_recommendations,
        "intervention_recommendations": intervention_recommendations,
        "culture_warnings": culture_warnings,
        "strengths": strengths,
    }

