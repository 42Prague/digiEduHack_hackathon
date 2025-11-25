"""
Utilities for TONE (Token-Optimized Notation Engine) format responses.
"""
from typing import Any, Optional
from pydantic import BaseModel

try:
    from tone import encode as tone_encode
except ImportError:
    # Fallback if toneformat is not installed
    tone_encode = None


def to_tone_format(data: Any) -> Optional[str]:
    """
    Convert data (Pydantic model, dict, etc.) to TONE format string.
    
    Args:
        data: Pydantic model, dict, or any JSON-serializable data
        
    Returns:
        TONE format string, or None if conversion fails or toneformat is not installed
    """
    if tone_encode is None:
        return None
    
    try:
        # Convert Pydantic model to dict if needed
        if isinstance(data, BaseModel):
            # Exclude computed fields (like 'tone') to avoid recursion
            data_dict = data.model_dump(exclude={'tone'})
        elif isinstance(data, dict):
            # Exclude 'tone' field if present to avoid recursion
            data_dict = {k: v for k, v in data.items() if k != 'tone'}
        else:
            # Try to convert to dict
            data_dict = dict(data) if hasattr(data, '__dict__') else data
            # Exclude 'tone' if it's a dict-like object
            if isinstance(data_dict, dict):
                data_dict = {k: v for k, v in data_dict.items() if k != 'tone'}
        
        # Encode to TONE format
        return tone_encode(data_dict)
    except Exception:
        # Return None on any error
        return None

