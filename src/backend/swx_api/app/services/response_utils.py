from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse, PlainTextResponse, Response

from swx_api.core.utils.tone_utils import to_tone_format


def tone_or_json(payload: Any, format_pref: str = "json") -> Response:
    if format_pref.lower() == "tone":
        tone = to_tone_format(payload)
        if tone:
            return PlainTextResponse(tone, media_type="text/plain")
    return JSONResponse(content=payload)

