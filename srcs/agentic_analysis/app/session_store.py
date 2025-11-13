from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .settings import settings

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent / "tmp_db.json"
DB_TABLE = "fancy_session"

try:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb
except ImportError:  # pragma: no cover - optional dependency
    psycopg = None  # type: ignore[assignment]
    dict_row = None  # type: ignore[assignment]
    Jsonb = None  # type: ignore[assignment]


def _is_db_configured() -> bool:
    return bool(
        settings.server_host
        and settings.server_db
        and settings.server_user
        and settings.server_port is not None
    )


USE_DB = _is_db_configured() and psycopg is not None

if _is_db_configured() and psycopg is None:
    logger.warning(
        "PostgreSQL settings detected but psycopg is not installed; falling back to JSON session store."
    )


def _json_param(data: Dict[str, Any]):
    if Jsonb is not None:
        return Jsonb(data)
    return json.dumps(data)


def _normalize_history(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        history = raw
    elif isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            history = parsed if isinstance(parsed, dict) else {"messages": []}
        except json.JSONDecodeError:
            history = {"messages": []}
    else:
        history = {"messages": []}

    messages = history.get("messages")
    if not isinstance(messages, list):
        history["messages"] = []
    return history


def _with_timestamp(message: Dict[str, Any]) -> Dict[str, Any]:
    message.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    return message


def _get_connection():
    if not USE_DB or psycopg is None:
        raise RuntimeError("PostgreSQL session storage is not available")
    return psycopg.connect(
        host=settings.server_host,
        port=settings.server_port,
        dbname=settings.server_db,
        user=settings.server_user,
        password=settings.server_password,
        connect_timeout=5,
    )


def _ensure_table() -> None:
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {DB_TABLE} (
                    id TEXT PRIMARY KEY,
                    message_history JSONB NOT NULL DEFAULT '{{"messages": []}}'::jsonb,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )


if USE_DB:
    try:
        _ensure_table()
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.error("Failed to initialize PostgreSQL session store: %s", exc)
        USE_DB = False
        logger.warning("Falling back to JSON file-based session store.")


def _load_all() -> Dict[str, Dict[str, Any]]:
    if USE_DB:
        data: Dict[str, Dict[str, Any]] = {}
        with _get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(f"SELECT id, message_history FROM {DB_TABLE}")
                for row in cur.fetchall():
                    data[row["id"]] = _normalize_history(row["message_history"])
        return data

    if not DB_PATH.exists():
        return {}
    try:
        with DB_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data  # type: ignore[return-value]
    except json.JSONDecodeError:
        pass
    return {}


def _save_all(data: Dict[str, Dict[str, Any]]) -> None:
    if USE_DB:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                for session_id, payload in data.items():
                    cur.execute(
                        f"""
                        INSERT INTO {DB_TABLE} (id, message_history, updated_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT (id) DO UPDATE
                        SET message_history = EXCLUDED.message_history,
                            updated_at = NOW()
                        """,
                        (session_id, _json_param(payload)),
                    )
        return

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DB_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ensure_session(session_id: str) -> None:
    if USE_DB:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {DB_TABLE} (id, message_history)
                    VALUES (%s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (session_id, _json_param({"messages": []})),
                )
        return

    data = _load_all()
    data.setdefault(session_id, {"messages": []})
    _save_all(data)


def get_session(session_id: str) -> Dict[str, Any]:
    if USE_DB:
        with _get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"SELECT message_history FROM {DB_TABLE} WHERE id = %s", (session_id,)
                )
                row = cur.fetchone()
        if row:
            return _normalize_history(row["message_history"])
        return {"messages": []}

    data = _load_all()
    return data.get(session_id, {"messages": []})


def list_sessions() -> Dict[str, Dict[str, Any]]:
    return _load_all()


def append_message(session_id: str, message: Dict[str, Any]) -> None:
    if USE_DB:
        with _get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"SELECT message_history FROM {DB_TABLE} WHERE id = %s", (session_id,)
                )
                row = cur.fetchone()
                if not row:
                    raise KeyError(f"Session '{session_id}' not found in {DB_TABLE}.")

                history = _normalize_history(row["message_history"])
                messages: List[Dict[str, Any]] = history.setdefault("messages", [])
                messages.append(_with_timestamp(message))

                cur.execute(
                    f"""
                    UPDATE {DB_TABLE}
                    SET message_history = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (_json_param(history), session_id),
                )
        return

    data = _load_all()
    session = data.setdefault(session_id, {"messages": []})
    messages: List[Dict[str, Any]] = session.setdefault("messages", [])
    messages.append(_with_timestamp(message))
    _save_all(data)


def overwrite_session(session_id: str, messages: List[Dict[str, Any]]) -> None:
    payload = {"messages": messages}
    if USE_DB:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {DB_TABLE} (id, message_history, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (id) DO UPDATE
                    SET message_history = EXCLUDED.message_history,
                        updated_at = NOW()
                    """,
                    (session_id, _json_param(payload)),
                )
        return

    data = _load_all()
    data[session_id] = payload
    _save_all(data)
