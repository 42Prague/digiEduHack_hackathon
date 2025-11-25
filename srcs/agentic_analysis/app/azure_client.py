from __future__ import annotations

from urllib.parse import urlparse

from openai import OpenAI

from .settings import settings


def _strip_known_suffixes(url: str) -> str:
    value = url.rstrip("/")
    suffixes = ("/openai/v1", "/openai", "/v1")
    changed = True
    while changed:
        changed = False
        for suffix in suffixes:
            if value.endswith(suffix):
                value = value[: -len(suffix)].rstrip("/")
                changed = True
    return value


def _build_client() -> OpenAI:
    endpoint = settings.azure_openai_endpoint.strip()
    if not endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT must be set")

    normalized = endpoint.rstrip("/")
    parsed = urlparse(normalized)
    hostname = parsed.hostname or ""

    default_headers = {}
    default_query = {}
    api_key = settings.azure_openai_api_key
    base_url = normalized or None

    if "openai.azure.com" in hostname:
        # Azure OpenAI requires deployment-specific paths and an api-version query param.
        resource_base = _strip_known_suffixes(normalized)
        deployment = settings.azure_openai_model
        base_url = endpoint
        default_query["api-version"] = settings.azure_openai_api_version
        # Azure expects the API key in the `api-key` header rather than Authorization bearer.
        default_headers["api-key"] = api_key
        #api_key = None  # Prevent OpenAI SDK from sending the key as Bearer token.
    
    else:
        # Standard OpenAI endpoint: let the SDK handle default base URL when possible.
        if hostname == "api.openai.com":
            base_url = None
        elif base_url and base_url.endswith("/openai/v1"):
            base_url = base_url[: -len("/openai/v1")] + "/v1"
        elif base_url and base_url.endswith("/openai"):
            base_url = base_url[: -len("/openai")] + "/v1"
        elif base_url and not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"

    return OpenAI(
        api_key=api_key,
        base_url=base_url,
        default_headers=default_headers or None,
        default_query=default_query or None,
    )


client = _build_client()
