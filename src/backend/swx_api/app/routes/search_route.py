from __future__ import annotations

from fastapi import APIRouter, Query

from swx_api.app.services import response_utils, search_service

router = APIRouter(prefix="/search")


@router.get("/")
async def full_text_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    format: str = Query("json"),
):
    """
    Full-text search across all ingested datasets.
    
    Searches in:
    - Text columns of CSV/Excel files
    - Markdown files
    - Normalized text files
    
    Returns matching snippets with dataset context.
    """
    results = search_service.search_all_datasets(q, limit)
    payload = {
        "query": q,
        "results": results,
        "count": len(results),
    }
    return response_utils.tone_or_json(payload, format)

