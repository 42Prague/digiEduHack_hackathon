"""
Full-text search service for searching across all ingested datasets.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from swx_api.app.services import ingestion_service


def search_all_datasets(query: str, limit: int = 20) -> List[Dict[str, object]]:
    """
    Search across all normalized datasets for matching content.
    
    Searches in:
    - Text columns of CSV/Excel files
    - Markdown files
    - DOCX text content
    
    Args:
        query: Search query (case-insensitive)
        limit: Maximum number of results to return
        
    Returns:
        List of matches with dataset name, snippet, and context
    """
    query_lower = query.lower()
    results: List[Dict[str, object]] = []
    
    for dataset in ingestion_service.list_datasets():
        dataset_path = Path(dataset["normalized_path"])
        dataset_name = dataset["name"]
        
        if not dataset_path.exists():
            continue
        
        # Search in CSV/Excel files
        if dataset_path.suffix.lower() in {".csv"}:
            try:
                df = pd.read_csv(dataset_path)
                matches = _search_dataframe(df, query_lower, dataset_name)
                results.extend(matches)
            except Exception:
                continue
        
        # Search in text files (markdown, normalized text)
        elif dataset_path.suffix.lower() in {".txt", ".md"}:
            try:
                text = dataset_path.read_text(encoding="utf-8")
                matches = _search_text_file(text, query_lower, dataset_name)
                results.extend(matches)
            except Exception:
                continue
    
    # Sort by relevance (simple: more matches = more relevant)
    results.sort(key=lambda x: x.get("match_count", 0), reverse=True)
    
    return results[:limit]


def _search_dataframe(df: pd.DataFrame, query: str, dataset_name: str) -> List[Dict[str, object]]:
    """Search within a DataFrame's text columns."""
    matches: List[Dict[str, object]] = []
    
    for column in df.columns:
        if not pd.api.types.is_numeric_dtype(df[column]):
            # Search in text columns
            series = df[column].astype(str).fillna("")
            matching_rows = series[series.str.lower().str.contains(query, na=False, regex=False)]
            
            for idx, value in matching_rows.items():
                snippet = _extract_snippet(str(value), query, max_length=150)
                matches.append(
                    {
                        "dataset": dataset_name,
                        "column": str(column),
                        "row_index": int(idx),
                        "snippet": snippet,
                        "match_count": str(value).lower().count(query),
                        "type": "tabular",
                    }
                )
    
    return matches


def _search_text_file(text: str, query: str, dataset_name: str) -> List[Dict[str, object]]:
    """Search within a text file."""
    matches: List[Dict[str, object]] = []
    text_lower = text.lower()
    
    if query not in text_lower:
        return matches
    
    # Find all occurrences
    occurrences = []
    start = 0
    while True:
        pos = text_lower.find(query, start)
        if pos == -1:
            break
        occurrences.append(pos)
        start = pos + 1
    
    # Extract snippets around each occurrence
    for pos in occurrences[:5]:  # Limit to first 5 matches per file
        snippet = _extract_snippet(text, query, context_start=pos, max_length=200)
        matches.append(
            {
                "dataset": dataset_name,
                "snippet": snippet,
                "match_count": text_lower.count(query),
                "type": "text",
            }
        )
    
    return matches


def _extract_snippet(text: str, query: str, context_start: Optional[int] = None, max_length: int = 150) -> str:
    """Extract a snippet around the query match."""
    text_lower = text.lower()
    query_lower = query.lower()
    
    if context_start is None:
        # Find first occurrence
        context_start = text_lower.find(query_lower)
        if context_start == -1:
            return text[:max_length] + "..." if len(text) > max_length else text
    
    # Extract context around match
    context_window = max_length // 2
    start = max(0, context_start - context_window)
    end = min(len(text), context_start + len(query) + context_window)
    
    snippet = text[start:end]
    
    # Highlight query (simple: just return snippet)
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    
    return snippet.strip()

