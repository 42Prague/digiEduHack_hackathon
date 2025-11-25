"""
Metadata Validation Service
----------------------------
Validates metadata for audio/transcript ingestion.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from fastapi import HTTPException


# Allowed enum values
ALLOWED_SCHOOL_TYPES = {
    "primary",
    "secondary",
    "gymnasium",
    "kindergarten",
    "special"
}

ALLOWED_INTERVENTION_TYPES = {
    "mentoring_program",
    "leadership_workshop",
    "team_training",
    "municipal_collaboration",
    "teacher_course",
    "other"
}

ALLOWED_PARTICIPANT_ROLES = {
    "teacher",
    "principal",
    "coordinator",
    "municipality"
}

# Allowed file extensions
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a"}
ALLOWED_TEXT_EXTENSIONS = {".txt", ".json", ".md"}  # Added .md for Markdown files
ALLOWED_EXTENSIONS = ALLOWED_AUDIO_EXTENSIONS | ALLOWED_TEXT_EXTENSIONS

# Allowed regions (can be expanded)
ALLOWED_REGIONS = {
    "praha", "brno", "ostrava", "plzen", "liberec", "olomouc",
    "ceske_budejovice", "hradec_kralove", "usti_nad_labem", "pardubice",
    "zlín", "karlovy_vary", "jihlava", "melnik", "kladno", "other"
}


def validate_metadata(metadata: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate metadata structure and values.
    
    Args:
        metadata: Metadata dictionary from client
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = [
        "school_id",
        "region_id",
        "school_type",
        "intervention_type",
        "participant_role",
        "interview_date"
    ]
    
    # Check all required fields exist
    for field in required_fields:
        if field not in metadata:
            return False, f"Missing required field: {field}"
    
    # Validate school_type
    school_type = metadata.get("school_type", "").lower()
    if school_type not in ALLOWED_SCHOOL_TYPES:
        return False, f"Invalid school_type: {school_type}. Allowed: {', '.join(ALLOWED_SCHOOL_TYPES)}"
    
    # Validate intervention_type
    intervention_type = metadata.get("intervention_type", "").lower()
    if intervention_type not in ALLOWED_INTERVENTION_TYPES:
        return False, f"Invalid intervention_type: {intervention_type}. Allowed: {', '.join(ALLOWED_INTERVENTION_TYPES)}"
    
    # Validate participant_role
    participant_role = metadata.get("participant_role", "").lower()
    if participant_role not in ALLOWED_PARTICIPANT_ROLES:
        return False, f"Invalid participant_role: {participant_role}. Allowed: {', '.join(ALLOWED_PARTICIPANT_ROLES)}"
    
    # Validate region_id (case-insensitive)
    region_id = metadata.get("region_id", "").lower()
    if region_id not in ALLOWED_REGIONS:
        return False, f"Invalid region_id: {region_id}. Allowed: {', '.join(ALLOWED_REGIONS)}"
    
    # Validate interview_date format (YYYY-MM-DD)
    interview_date_str = metadata.get("interview_date", "")
    try:
        datetime.strptime(interview_date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return False, f"Invalid interview_date format: {interview_date_str}. Expected YYYY-MM-DD"
    
    # Validate string fields for unsafe characters
    string_fields = ["school_id", "region_id"]
    unsafe_pattern = re.compile(r'[<>"\']|\.\./|\.\.\\')
    for field in string_fields:
        value = str(metadata.get(field, ""))
        if unsafe_pattern.search(value):
            return False, f"Unsafe characters detected in {field}"
    
    return True, None


def validate_file_extension(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate file extension is allowed.
    
    Args:
        filename: Original filename
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filename:
        return False, "Filename is required"
    
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Invalid file extension: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    return True, None


def determine_file_type(filename: str) -> str:
    """
    Determine if file is audio or transcript based on extension.
    
    Args:
        filename: Original filename
        
    Returns:
        'audio' or 'transcript'
    """
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in ALLOWED_AUDIO_EXTENSIONS:
        return "audio"
    return "transcript"

