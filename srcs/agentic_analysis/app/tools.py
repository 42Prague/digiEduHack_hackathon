from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from .settings import settings

try:  # pragma: no cover - optional dependency at runtime
    import psycopg  # type: ignore
    from psycopg.rows import dict_row  # type: ignore
except Exception:  # pragma: no cover - handled gracefully later
    psycopg = None  # type: ignore
    dict_row = None  # type: ignore


logger = logging.getLogger(__name__)
TSVECTOR_TOKEN_RE = re.compile(r"'([^']+)'")
WORD_RE = re.compile(r"[A-Za-z0-9]+", re.UNICODE)

RAW_DOCUMENT_COLUMNS = """
    SELECT
        id,
        doc_type,
        teacher_id,
        workshop_id,
        uploaded_at,
        original_filename,
        mime_type,
        file_path,
        text_content,
        table_data,
        summary,
        embedding
    FROM raw_document
""".strip()


def _require_db() -> None:
    if psycopg is None:  # pragma: no cover - depends on system setup
        raise RuntimeError(
            "psycopg is required for database-backed tools. "
            "Install psycopg[binary] and ensure the DATABASE settings are configured."
        )


def _get_connection():
    _require_db()
    return psycopg.connect(  # type: ignore[attr-defined]
        host=settings.server_host,
        port=settings.server_port,
        dbname=settings.server_db,
        user=settings.server_user,
        password=settings.server_password,
        connect_timeout=5,
    )


def _coerce_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, memoryview):
        value = value.tobytes()
    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8")
        except Exception:
            return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _normalize_document(row: Dict[str, Any]) -> Dict[str, Any]:
    document = dict(row)
    if document.get("id") is not None:
        document["id"] = str(document["id"])
    uploaded_at = document.get("uploaded_at")
    if isinstance(uploaded_at, datetime):
        document["uploaded_at"] = uploaded_at.isoformat()
    document["table_data"] = _coerce_json(document.get("table_data"))
    embedding = document.get("embedding")
    if isinstance(embedding, memoryview):
        embedding = embedding.tobytes()
    if isinstance(embedding, bytes):
        try:
            embedding = embedding.decode("utf-8")
        except UnicodeDecodeError:
            embedding = None
    document["embedding"] = embedding
    return document


def _fetch_documents(
    *,
    limit: Optional[int] = None,
    where: Optional[str] = None,
    params: Optional[Sequence[Any]] = None,
    order_clause: str = "uploaded_at DESC",
) -> List[Dict[str, Any]]:
    sql = [RAW_DOCUMENT_COLUMNS]
    if where:
        sql.append(f"WHERE {where}")
    if order_clause:
        sql.append(f"ORDER BY {order_clause}")
    if limit is not None:
        sql.append("LIMIT %s")
    query = " \n".join(sql)

    exec_params: List[Any] = list(params or [])
    if limit is not None:
        exec_params.append(limit)

    with _get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:  # type: ignore[arg-type]
            cur.execute(query, tuple(exec_params))
            rows = cur.fetchall()
    return [_normalize_document(row) for row in rows]


def load_files(limit: int | None = None) -> Dict[str, Any]:
    """Fetch every raw_document (no filtering) for prompt bootstrapping."""
    try:
        documents = _fetch_documents(limit=limit)
        print(f"Loaded {len(documents)} raw_document entries in load_files.")
    except Exception as exc:
        logger.exception("Failed to load raw_document metadata: %s", exc)
        return {"files": [], "error": str(exc)}
    return {"files": documents, "count": len(documents)}


def _tsvector_counter(raw_value: Any) -> Optional[Counter]:
    if raw_value is None:
        return None
    if isinstance(raw_value, Counter):
        return raw_value
    if isinstance(raw_value, (list, tuple)):
        return Counter({f"d{i}": float(v) for i, v in enumerate(raw_value)})
    if isinstance(raw_value, memoryview):
        raw_value = raw_value.tobytes()
    if isinstance(raw_value, bytes):
        try:
            raw_value = raw_value.decode("utf-8")
        except UnicodeDecodeError:
            return None
    if isinstance(raw_value, str):
        value = raw_value.strip()
        if value.startswith("[") and value.endswith("]"):
            try:
                data = json.loads(value)
            except json.JSONDecodeError:
                data = None
            if isinstance(data, list):
                return Counter({f"d{i}": float(v) for i, v in enumerate(data)})
        tokens = TSVECTOR_TOKEN_RE.findall(value)
        if tokens:
            return Counter(tokens)
        return Counter({f"d{i}": float(v) for i, v in enumerate(value.split())}) if value else None
    return None


def _text_counter(text: str | None) -> Counter:
    if not text:
        return Counter()
    tokens = WORD_RE.findall(text.lower())
    return Counter(tokens)


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[token] * b[token] for token in a.keys() & b.keys())
    if dot == 0:
        return 0.0
    norm_a = math.sqrt(sum(value * value for value in a.values()))
    norm_b = math.sqrt(sum(value * value for value in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def find_relevant_files(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Perform a lightweight lexical embedding match between the query and stored embeddings.
    """
    try:
        documents = _fetch_documents()
    except Exception as exc:
        logger.exception("Failed to fetch documents for semantic search: %s", exc)
        return {"query": query, "files": [], "error": str(exc)}

    query_counter = _text_counter(query)
    ranked: List[Dict[str, Any]] = []

    for doc in documents:
        embedding_counter = _tsvector_counter(doc.get("embedding"))
        if embedding_counter is None:
            fallback_source = (
                doc.get("summary")
                or doc.get("text_content")
                or doc.get("original_filename")
                or doc.get("doc_type")
            )
            embedding_counter = _text_counter(fallback_source)
        score = _cosine(query_counter, embedding_counter)
        enriched = dict(doc)
        enriched["match_score"] = score
        ranked.append(enriched)

    ranked.sort(key=lambda item: item["match_score"], reverse=True)
    limit = max(1, top_k)
    return {
        "query": query,
        "files": ranked[:limit],
        "count": min(limit, len(ranked)),
    }


def temporal_search(start_date: str, end_date: str) -> Dict[str, Any]:
    """Return every document whose uploaded_at falls within the inclusive window."""
    where = "uploaded_at BETWEEN %s::timestamptz AND %s::timestamptz"
    try:
        documents = _fetch_documents(
            where=where,
            params=(start_date, end_date),
            order_clause="uploaded_at ASC",
        )
        print(f"Temporal search found {len(documents)} documents.")
    except Exception as exc:
        logger.exception("Temporal search failed: %s", exc)
        return {"start_date": start_date, "end_date": end_date, "files": [], "error": str(exc)}

    return {
        "start_date": start_date,
        "end_date": end_date,
        "files": documents,
        "count": len(documents),
    }
