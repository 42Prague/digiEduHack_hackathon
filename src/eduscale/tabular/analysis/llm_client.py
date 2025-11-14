"""LLM client for entity extraction and sentiment analysis using Ollama.

This module provides an interface to Ollama for LLM-based tasks like
entity extraction from text and sentiment analysis.
"""

import json
import logging
from typing import Any

import requests

from eduscale.core.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with Ollama LLM API."""

    def __init__(self, endpoint: str | None = None, model: str | None = None):
        """Initialize LLM client.

        Args:
            endpoint: Ollama API endpoint (default: from settings)
            model: Model name (default: from settings)
        """
        self.endpoint = endpoint or settings.LLM_ENDPOINT
        self.model = model or settings.LLM_MODEL_NAME
        self.enabled = settings.LLM_ENABLED

        if not self.enabled:
            logger.warning("LLM is disabled in settings")

    def extract_entities(self, text: str) -> list[dict[str, str]]:
        """Extract named entities from text using LLM.

        Args:
            text: Input text (Czech or English)

        Returns:
            List of entities with format: [{"text": "name", "type": "person|subject|location"}]
            Returns empty list if LLM is disabled or extraction fails
        """
        if not self.enabled:
            logger.debug("LLM disabled, skipping entity extraction")
            return []

        if not text or not text.strip():
            return []

        prompt = f"""Extract person names, subjects, and locations from this Czech/English educational text.
Return ONLY a JSON array with this exact format: [{{"text": "name", "type": "person|subject|location"}}]
Do not include any explanation, only the JSON array.

Text: {text}

JSON:"""

        try:
            response = self._call_ollama(prompt, max_tokens=200)
            # Try to parse JSON response
            entities = json.loads(response.strip())

            if not isinstance(entities, list):
                logger.warning(f"LLM returned non-list response: {response}")
                return []

            # Validate entity format
            valid_entities = []
            for entity in entities:
                if isinstance(entity, dict) and "text" in entity and "type" in entity:
                    valid_entities.append(entity)
                else:
                    logger.warning(f"Invalid entity format: {entity}")

            logger.info(f"Extracted {len(valid_entities)} entities from text")
            return valid_entities

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}, response: {response}")
            return []
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []

    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment using LLM.

        Args:
            text: Input text (Czech or English)

        Returns:
            Sentiment score from -1.0 (very negative) to +1.0 (very positive)
            Returns 0.0 if LLM is disabled or analysis fails
        """
        if not self.enabled:
            logger.debug("LLM disabled, skipping sentiment analysis")
            return 0.0

        if not text or not text.strip():
            return 0.0

        prompt = f"""Analyze the sentiment of this educational feedback (Czech/English).
Return ONLY a single number from -1.0 (very negative) to +1.0 (very positive).
Do not include any explanation, only the number.

Text: {text}

Score:"""

        try:
            response = self._call_ollama(prompt, max_tokens=10)
            score = float(response.strip())

            # Clamp to valid range
            score = max(-1.0, min(1.0, score))

            logger.info(f"Sentiment score: {score:.3f}")
            return score

        except ValueError as e:
            logger.warning(f"Failed to parse sentiment score: {e}, response: {response}")
            return 0.0
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return 0.0

    def _call_ollama(self, prompt: str, max_tokens: int = 500) -> str:
        """Internal method to call Ollama API.

        Args:
            prompt: Prompt text
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response

        Raises:
            requests.RequestException: If API call fails
        """
        try:
            response = requests.post(
                f"{self.endpoint}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.1,  # Low temperature for deterministic outputs
                    },
                },
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            return result.get("response", "")

        except requests.RequestException as e:
            logger.error(f"Ollama API call failed: {e}")
            raise
