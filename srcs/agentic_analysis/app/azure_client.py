from __future__ import annotations

from urllib.parse import urlparse

from openai import AzureOpenAI, OpenAI

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


def _build_client():
    endpoint = settings.azure_openai_endpoint.strip()
    if not endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT must be set")

    parsed = urlparse(endpoint)
    hostname = parsed.hostname or ""

    if "openai.azure.com" in hostname:
        azure_endpoint = _strip_known_suffixes(endpoint)
        return AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=azure_endpoint,
            api_version=settings.azure_openai_api_version,
        )

    # Fallback to public OpenAI endpoint for local testing.
    # If the endpoint already points to api.openai.com, rely on the SDK default
    # so we don't accidentally double-prefix paths such as /openai/v1.
    base_url = endpoint.rstrip("/")
    parsed_base = urlparse(base_url)
    if parsed_base.hostname == "api.openai.com":
        base_url = None
    elif base_url.endswith("/openai/v1"):
        base_url = base_url[: -len("/openai/v1")] + "/v1"
    elif base_url.endswith("/openai"):
        base_url = base_url[: -len("/openai")] + "/v1"
    elif not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1"

    return OpenAI(
        api_key=settings.azure_openai_api_key,
        base_url=base_url,
    )


client = _build_client()
