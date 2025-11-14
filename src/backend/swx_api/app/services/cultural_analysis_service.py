"""
Cultural Analysis Service

Analyzes teacher interview transcripts using Michael Fullan's theory of school culture change.
Uses premium AI models (Featherless.ai) to extract cultural metrics and insights.
"""
from __future__ import annotations

import json
import logging
from typing import Dict, Any, Optional

from swx_api.app.services.llm_client import LLMClient, LLMConfig

logger = logging.getLogger("cultural_analysis")

CULTURAL_ANALYSIS_PROMPT = """You are an educational researcher analyzing teacher interviews. 
Using Michael Fullan's theory of school culture change, extract the following information:

1. mindset_shift_score (0-100)
2. teacher_confidence_score (0-100)
3. collaboration_score (0-100)
4. cooperation_municipality_score (0-100)
5. sentiment (0-100)
6. top 3-5 themes mentioned
7. practical_change (short sentence about what changed)
8. mindset_change (short sentence about mindset shift)
9. impact_summary (5-7 sentence summary of the intervention's impact)
10. did the interview show culture change? (yes/no + short reason)

RETURN JSON ONLY:

{{
  "mindset_shift_score": ...,
  "teacher_confidence_score": ...,
  "collaboration_score": ...,
  "cooperation_municipality_score": ...,
  "sentiment": ...,
  "themes": [...],
  "practical_change": "...",
  "mindset_change": "...",
  "impact_summary": "...",
  "culture_change_detected": true/false,
  "reason": "..."
}}

Transcript:
{transcript}"""


def analyze_cultural_transcript(transcript: str) -> Dict[str, Any]:
    """
    Analyze a teacher interview transcript for cultural change indicators.
    
    Args:
        transcript: The transcribed text from a teacher interview
        
    Returns:
        Dictionary containing cultural analysis scores and insights
    """
    if not transcript or not transcript.strip():
        logger.warning("Empty transcript provided for cultural analysis")
        return _get_default_analysis()
    
    try:
        # Use Featherless.ai for cultural analysis
        config = LLMConfig.from_env()
        
        # Override to use Featherless if available, otherwise use configured provider
        if not config.api_key or config.provider != "featherless":
            # Try to get Featherless API key
            import os
            featherless_key = os.getenv("FEATHERLESS_API_KEY")
            if featherless_key:
                config = LLMConfig(
                    provider="featherless",
                    model="meta-llama/Meta-Llama-3.1-8B-Instruct",
                    api_key=featherless_key,
                    endpoint=None,
                )
            else:
                logger.warning("FEATHERLESS_API_KEY not set, using configured provider")
        
        client = LLMClient(config)
        
        # Build prompt with transcript
        prompt = CULTURAL_ANALYSIS_PROMPT.format(transcript=transcript[:8000])
        
        # Get AI analysis
        response_text = client.ai_analyze(prompt)
        
        # Parse JSON response
        analysis = _parse_analysis_response(response_text)
        
        logger.info("Cultural analysis completed successfully")
        return analysis
        
    except Exception as e:
        logger.error(f"Error in cultural analysis: {e}", exc_info=True)
        return _get_default_analysis()


def _parse_analysis_response(response_text: str) -> Dict[str, Any]:
    """
    Parse the AI response and extract structured data.
    Handles various response formats (JSON, markdown code blocks, etc.)
    """
    if not response_text:
        return _get_default_analysis()
    
    # Try to extract JSON from response (might be wrapped in markdown code blocks)
    import re
    
    # Look for JSON code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        response_text = json_match.group(1)
    
    # Look for standalone JSON object
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        response_text = json_match.group(0)
    
    try:
        data = json.loads(response_text)
        
        # Validate and normalize the response
        return {
            "mindset_shift_score": int(data.get("mindset_shift_score", 0)),
            "teacher_confidence_score": int(data.get("teacher_confidence_score", 0)),
            "collaboration_score": int(data.get("collaboration_score", 0)),
            "cooperation_municipality_score": int(data.get("cooperation_municipality_score", 0)),
            "sentiment": int(data.get("sentiment", 50)),
            "themes": data.get("themes", []),
            "practical_change": str(data.get("practical_change", "")),
            "mindset_change": str(data.get("mindset_change", "")),
            "impact_summary": str(data.get("impact_summary", "")),
            "culture_change_detected": bool(data.get("culture_change_detected", False)),
            "reason": str(data.get("reason", "")),
        }
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from AI response: {e}")
        logger.debug(f"Response text: {response_text[:500]}")
        return _get_default_analysis()


def _get_default_analysis() -> Dict[str, Any]:
    """Return default analysis when AI analysis fails or is unavailable."""
    return {
        "mindset_shift_score": 0,
        "teacher_confidence_score": 0,
        "collaboration_score": 0,
        "cooperation_municipality_score": 0,
        "sentiment": 50,
        "themes": [],
        "practical_change": "Analysis not available",
        "mindset_change": "Analysis not available",
        "impact_summary": "Cultural analysis was not performed. Please ensure FEATHERLESS_API_KEY is configured.",
        "culture_change_detected": False,
        "reason": "Analysis unavailable",
    }

