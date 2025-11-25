"""
Unified Response Service
-----------------------
Creates consistent response structures for all ingestion endpoints.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from swx_api.app.services.llm_client import LLMClient, LLMConfig
from swx_api.app.services.data_quality_service import generate_dq_report

logger = logging.getLogger("unified_response")


def generate_text_summary(text: str, max_sentences: int = 4) -> str:
    """
    Generate a short natural-language summary of text using LLM.
    
    Args:
        text: Text to summarize
        max_sentences: Maximum number of sentences in summary
        
    Returns:
        Summary string
    """
    if not text or not text.strip():
        return ""
    
    try:
        # Truncate text if too long
        text_sample = text[:4000] if len(text) > 4000 else text
        
        prompt = f"""Summarize the following text in {max_sentences} sentences. 
Focus on key points and main ideas.

Text:
{text_sample}

Summary:"""
        
        config = LLMConfig.from_env()
        client = LLMClient(config)
        
        summary = client.ai_analyze(prompt)
        
        # Clean up summary
        summary = summary.strip()
        if not summary:
            return ""
        
        return summary
        
    except Exception as e:
        logger.warning(f"Summary generation failed: {e}")
        return ""


def create_unified_ingestion_response(
    result: Dict[str, Any],
    file_type: str = "file",
    metadata: Optional[Dict[str, Any]] = None,
    cultural_analysis: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a unified ingestion response structure.
    
    Args:
        result: Result from ingestion service
        file_type: Type of file (file, audio, transcript)
        metadata: Optional metadata (for audio uploads)
        cultural_analysis: Optional cultural analysis (for transcripts)
        
    Returns:
        Unified response dictionary
    """
    # Determine classification
    classification = result.get("classification", "qualitative")
    if file_type in ["audio", "transcript"]:
        classification = "transcript" if file_type == "transcript" else "audio"
    
    # Generate auto_summary for qualitative/transcript data
    auto_summary = None
    if classification in ["qualitative", "transcript"]:
        text_to_summarize = result.get("clean_text") or result.get("transcript_text") or ""
        if text_to_summarize:
            try:
                auto_summary = generate_text_summary(text_to_summarize)
            except Exception as e:
                logger.warning(f"Auto-summary generation failed: {e}")
    
    # Build unified response
    response = {
        "success": True,
        "dataset_id": result.get("name") or result.get("id"),
        "filename": result.get("filename", ""),
        "file_type": file_type,
        "stored_path": result.get("stored_path", ""),
        "normalized_path": result.get("normalized_path", ""),
        "classification": classification,
        "row_count": result.get("row_count"),
        "columns": result.get("columns"),
        "numeric_ratio": result.get("numeric_ratio"),
        "summary": result.get("summary", {}),
        "summary_path": result.get("summary_path", ""),
        "dq_report_path": result.get("dq_report_path"),
        "auto_summary": auto_summary,
    }
    
    # Add metadata if provided (for audio uploads)
    if metadata:
        response["metadata"] = metadata
    
    # Add cultural analysis if provided (for transcripts)
    if cultural_analysis:
        response["cultural_analysis"] = cultural_analysis
    elif classification == "transcript":
        # Provide default structure if missing
        response["cultural_analysis"] = {
            "mindset_shift_score": None,
            "collaboration_score": None,
            "teacher_confidence_score": None,
            "municipality_cooperation_score": None,
            "sentiment_score": None,
            "themes": [],
            "practical_change": "",
            "mindset_change": "",
            "impact_summary": "",
            "culture_change_detected": False,
        }
    
    return response

