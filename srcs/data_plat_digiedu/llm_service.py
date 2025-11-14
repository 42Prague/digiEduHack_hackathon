"""
====================================================================
LLM SERVICE UTILITY
Connect to Hugging Face LLM API via Flask service
====================================================================
"""

import requests
import os
from typing import List, Dict, Optional

# LLM Service Configuration
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm-service:8000")


def check_llm_available() -> bool:
    """Check if LLM service is available."""
    try:
        response = requests.get(f"{LLM_SERVICE_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False


def call_llm_chat(
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
    system_prompt: str = "You are a helpful assistant that analyzes educational research data.",
    max_retries: int = 3
) -> str:
    """
    Call LLM chat endpoint with conversation history.
    
    Args:
        message: User message to send
        history: List of previous messages [{"role": "user|assistant", "content": "..."}]
        system_prompt: System prompt to set context
        max_retries: Number of retry attempts on failure
        
    Returns:
        Assistant's reply as string
    """
    if history is None:
        history = []
    
    payload = {
        "message": message,
        "history": history,
        "system": system_prompt
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{LLM_SERVICE_URL}/chat",
                json=payload,
                timeout=90
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("reply", "")
            else:
                error_msg = response.json().get("error", "Unknown error")
                if attempt == max_retries - 1:
                    return f"Error: {error_msg}"
                    
        except requests.exceptions.Timeout:
            if attempt == max_retries - 1:
                return "Error: Request timed out. The model might be processing a complex query."
        except requests.exceptions.ConnectionError:
            if attempt == max_retries - 1:
                return "Error: Cannot connect to LLM service. Please ensure the service is running."
        except Exception as e:
            if attempt == max_retries - 1:
                return f"Error calling LLM: {str(e)}"
    
    return "Error: Maximum retries exceeded."


def call_llm_simple(prompt: str, temperature: float = 0.7) -> str:
    """
    Simple LLM call without conversation history.
    
    Args:
        prompt: The prompt to send to the LLM
        temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
        
    Returns:
        LLM response as string
    """
    # For temperature control, we could add it to the system prompt as a hint
    system_prompt = "You are a helpful assistant that analyzes educational research data."
    
    if temperature < 0.3:
        system_prompt += " Provide precise, factual, and concise responses."
    elif temperature > 0.7:
        system_prompt += " Be creative and provide detailed, exploratory insights."
    
    return call_llm_chat(
        message=prompt,
        history=[],
        system_prompt=system_prompt
    )


def summarize_text(text: str) -> str:
    """
    Summarize text using the LLM service.
    
    Args:
        text: Text to summarize
        
    Returns:
        Summary as string
    """
    try:
        response = requests.post(
            f"{LLM_SERVICE_URL}/summarize",
            data={"text": text},
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("summary", "")
        else:
            error_msg = response.json().get("error", "Unknown error")
            return f"Error: {error_msg}"
            
    except requests.exceptions.Timeout:
        return "Error: Request timed out."
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to LLM service."
    except Exception as e:
        return f"Error: {str(e)}"


def get_service_status() -> Dict[str, any]:
    """
    Get LLM service status information.
    
    Returns:
        Dictionary with status information
    """
    try:
        response = requests.get(f"{LLM_SERVICE_URL}/", timeout=2)
        if response.status_code == 200:
            return {
                "available": True,
                "url": LLM_SERVICE_URL,
                "provider": "Hugging Face",
                "status": "Connected"
            }
    except:
        pass
    
    return {
        "available": False,
        "url": LLM_SERVICE_URL,
        "provider": "Hugging Face",
        "status": "Disconnected"
    }

