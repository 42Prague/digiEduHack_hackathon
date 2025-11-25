from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

import json

import httpx
from openai import OpenAI


DEFAULT_THEMES = [
    "No LLM configured. Provide INGESTION_LLM_PROVIDER or fallback to manual themes.",
]


@dataclass
class LLMConfig:
    provider: str
    model: str
    api_key: Optional[str] = None
    endpoint: Optional[str] = None

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """
        Load LLM configuration from environment variables.
        
        Default: "heuristic" (no external AI, zero privacy risk)
        Recommended: "ollama" (self-hosted, EU-compliant)
        Optional: "openai" (⚠️ REQUIRES EU deployment - Azure OpenAI EU region only)
        Optional: "featherless" (Premium models via Featherless.ai)
        
        For hackathon compliance:
        - Use "heuristic" or "ollama" for production
        - "openai" only if Azure OpenAI EU is properly configured
        - "featherless" for premium models (requires FEATHERLESS_API_KEY)
        - NEVER use US-based OpenAI API with real educational data
        """
        provider = os.getenv("INGESTION_LLM_PROVIDER", "heuristic").lower()
        # Default model depends on provider
        if provider == "ollama":
            model = os.getenv("INGESTION_LLM_MODEL", "llama3")
        elif provider == "featherless":
            model = os.getenv("INGESTION_LLM_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct")
        else:
            model = os.getenv("INGESTION_LLM_MODEL", "gpt-4o-mini")
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("FEATHERLESS_API_KEY")
        endpoint = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")

        return cls(provider=provider, model=model, api_key=api_key, endpoint=endpoint)


class LLMClient:
    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._featherless_client: Optional[OpenAI] = None

    def extract_themes(self, text: str) -> List[str]:
        provider = self.config.provider

        if provider == "openai" and self.config.api_key:
            return self._extract_with_openai(text)
        if provider == "featherless" and self.config.api_key:
            return self._extract_with_featherless(text)
        if provider == "ollama":
            return self._extract_with_ollama(text)
        if provider == "heuristic":
            return self._extract_with_heuristic(text)

        return DEFAULT_THEMES

    def ai_analyze(self, prompt: str) -> str:
        """
        Generic AI analysis function using the configured provider.
        Returns the raw text response from the model.
        """
        provider = self.config.provider

        if provider == "featherless" and self.config.api_key:
            return self._analyze_with_featherless(prompt)
        if provider == "openai" and self.config.api_key:
            return self._analyze_with_openai(prompt)
        if provider == "ollama":
            return self._analyze_with_ollama(prompt)
        
        # Fallback for heuristic
        return "Analysis not available: No AI provider configured."

    def _extract_with_openai(self, text: str) -> List[str]:
        """
        Extract themes using OpenAI API.
        
        ⚠️ HACKATHON COMPLIANCE WARNING:
        - This uses US-based OpenAI API endpoint
        - For production/hackathon: Use Azure OpenAI (EU region) instead
        - Or use Ollama (self-hosted) for EU compliance
        - This method should only be used for development/testing
        """
        # TODO: Update to use Azure OpenAI EU endpoint for production
        # Example: https://your-resource.openai.azure.com/openai/deployments/...
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        body: Dict[str, object] = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that summarises qualitative datasets. "
                        "Extract 3-5 key themes. Respond with a JSON array of strings."
                    ),
                },
                {
                    "role": "user",
                    "content": text[:6000],
                },
            ],
            "response_format": {"type": "json_schema", "json_schema": {"name": "themes", "schema": {
                "type": "object",
                "properties": {"themes": {"type": "array", "items": {"type": "string"}}},
                "required": ["themes"],
            }}},
        }

        with httpx.Client(timeout=30.0) as client:
            # ⚠️ WARNING: This uses US-based OpenAI. For production, use Azure OpenAI EU.
            response = client.post("https://api.openai.com/v1/chat/completions", json=body, headers=headers)
            response.raise_for_status()
            payload = response.json()

        themes: List[str]
        try:
            content = payload["choices"][0]["message"]["content"]
            data = json.loads(content)
            raw_themes = data.get("themes", [])
            themes = [str(item) for item in raw_themes]
        except Exception:
            themes = DEFAULT_THEMES
        return themes

    def _extract_with_ollama(self, text: str) -> List[str]:
        """
        Extract themes using Ollama (self-hosted LLM).
        
        Uses /api/chat endpoint (Ollama v0.1.0+) for better compatibility.
        Falls back to /api/generate for older Ollama versions.
        """
        # Try /api/chat first (newer Ollama versions)
        chat_endpoint = self.config.endpoint.rstrip("/") + "/api/chat"
        chat_body = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts key themes from qualitative datasets. Return a JSON array of 3-5 short theme strings."
                },
                {
                    "role": "user",
                    "content": f"Extract 3 to 5 key themes from the following qualitative dataset. Return them as a JSON array of short strings.\n\n{text[:6000]}"
                }
            ],
            "format": "json",
            "stream": False
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                # Try /api/chat endpoint (newer Ollama)
                try:
                    response = client.post(chat_endpoint, json=chat_body)
                    response.raise_for_status()
                    payload = response.json()
                    
                    # Parse response from /api/chat
                    if isinstance(payload, dict) and "message" in payload:
                        content = payload["message"].get("content", "")
                        try:
                            data = json.loads(content)
                            # Handle different response formats
                            if isinstance(data, list):
                                # Direct array of strings
                                themes = [str(item) for item in data]
                            elif isinstance(data, dict):
                                # Object with themes array
                                raw_themes = data.get("themes", [])
                                if raw_themes:
                                    # Handle array of objects with "name" field
                                    if isinstance(raw_themes[0], dict):
                                        themes = [str(t.get("name", t)) for t in raw_themes]
                                    else:
                                        themes = [str(t) for t in raw_themes]
                                else:
                                    themes = []
                            else:
                                themes = []
                            return themes if themes else DEFAULT_THEMES
                        except json.JSONDecodeError:
                            # If not JSON, try to extract themes from text
                            # Look for list-like patterns in the text
                            import re
                            # Try to find JSON array in text
                            array_match = re.search(r'\[.*?\]', content, re.DOTALL)
                            if array_match:
                                try:
                                    data = json.loads(array_match.group())
                                    if isinstance(data, list):
                                        themes = [str(item) for item in data if item]
                                        if themes:
                                            return themes
                                except:
                                    pass
                            return DEFAULT_THEMES
                except (httpx.HTTPError, KeyError):
                    # Fallback to /api/generate (older Ollama versions)
                    generate_endpoint = self.config.endpoint.rstrip("/") + "/api/generate"
                    generate_body = {
                        "model": self.config.model,
                        "prompt": (
                            "Extract 3 to 5 key themes from the following qualitative dataset. "
                            "Return them as a JSON array of short strings.\n\n"
                            f"{text[:6000]}"
                        ),
                        "format": "json",
                    }
                    response = client.post(generate_endpoint, json=generate_body)
                    response.raise_for_status()
                    payload = response.json()
                    
                    # Parse response from /api/generate
                    if isinstance(payload, dict) and "response" in payload:
                        data = json.loads(payload["response"])
                        if isinstance(data, list):
                            themes = [str(item) for item in data]
                        else:
                            raw_themes = data.get("themes", [])
                            themes = [str(item) for item in raw_themes]
                        return themes if themes else DEFAULT_THEMES
        except Exception as e:
            # If Ollama fails, return default themes
            print(f"⚠️ Ollama error: {e}")
            return DEFAULT_THEMES
        
        return DEFAULT_THEMES

    @staticmethod
    def _extract_with_heuristic(text: str) -> List[str]:
        words = [word.strip(".,!?\"'()[]") for word in text.lower().split()]
        freq: Dict[str, int] = {}
        stopwords = {
            "the",
            "and",
            "to",
            "a",
            "of",
            "in",
            "that",
            "for",
            "with",
            "is",
            "on",
            "it",
            "as",
            "are",
            "was",
            "were",
            "be",
            "by",
            "this",
            "or",
            "an",
            "from",
        }
        for word in words:
            if len(word) < 4 or word in stopwords:
                continue
            freq[word] = freq.get(word, 0) + 1

        ranked = sorted(freq.items(), key=lambda item: item[1], reverse=True)
        return [word for word, _ in ranked[:5]] or DEFAULT_THEMES

    def _extract_with_featherless(self, text: str) -> List[str]:
        """Extract themes using Featherless.ai API."""
        try:
            response = self._analyze_with_featherless(
                f"Extract 3 to 5 key themes from the following qualitative dataset. Return them as a JSON array of short strings.\n\n{text[:6000]}"
            )
            # Parse JSON response
            data = json.loads(response)
            if isinstance(data, list):
                return [str(item) for item in data]
            elif isinstance(data, dict):
                themes = data.get("themes", [])
                return [str(t) for t in themes] if themes else DEFAULT_THEMES
            return DEFAULT_THEMES
        except Exception as e:
            print(f"⚠️ Featherless error: {e}")
            return DEFAULT_THEMES

    def _analyze_with_featherless(self, prompt: str) -> str:
        """
        Analyze using Featherless.ai API via the OpenAI SDK.
        Uses the Responses endpoint with the configured premium model.
        """
        if not self.config.api_key:
            raise ValueError("FEATHERLESS_API_KEY is not configured")

        client = self._get_featherless_client()

        response = client.responses.create(
            model=self.config.model,
            input=[
                {
                    "role": "system",
                    "content": "You are an expert educational researcher analyzing school culture and intervention impact.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        # Responses API provides a helper for concatenated text
        if hasattr(response, "output_text"):
            return response.output_text.strip()

        # Fallback: attempt to use the first output message
        try:
            data = response.to_dict() if hasattr(response, "to_dict") else response  # type: ignore[attr-defined]
            output = data.get("output") or data.get("choices") or []
            if output:
                # Responses API -> output list with content chunks
                first = output[0]
                if isinstance(first, dict):
                    content = first.get("content")
                    if isinstance(content, list) and content:
                        text_block = content[0]
                        if isinstance(text_block, dict):
                            return str(text_block.get("text") or text_block.get("value") or "").strip()
                    if "message" in first:
                        return str(first["message"].get("content", "")).strip()
            raise ValueError("Featherless response did not contain output text")
        except Exception as exc:  # pragma: no cover - defensive parsing
            raise ValueError(f"Invalid response from Featherless API: {exc}") from exc

    def _get_featherless_client(self) -> OpenAI:
        """
        Lazily instantiate the OpenAI SDK client configured for Featherless.
        """
        if self._featherless_client:
            return self._featherless_client

        base_url = self.config.endpoint or "https://api.featherless.ai/v1"
        self._featherless_client = OpenAI(
            api_key=self.config.api_key,
            base_url=base_url,
        )
        return self._featherless_client

    def _analyze_with_openai(self, prompt: str) -> str:
        """Analyze using OpenAI-compatible API."""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        body: Dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert educational researcher analyzing school culture and intervention impact.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                "https://api.openai.com/v1/chat/completions",
                json=body,
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()

        try:
            return payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid response from OpenAI API: {e}") from e

    def _analyze_with_ollama(self, prompt: str) -> str:
        """Analyze using Ollama API."""
        chat_endpoint = self.config.endpoint.rstrip("/") + "/api/chat"
        chat_body = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert educational researcher analyzing school culture and intervention impact.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "stream": False,
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(chat_endpoint, json=chat_body)
                response.raise_for_status()
                payload = response.json()

                if isinstance(payload, dict) and "message" in payload:
                    return payload["message"].get("content", "")
                return ""
        except Exception as e:
            raise ValueError(f"Ollama analysis error: {e}") from e

