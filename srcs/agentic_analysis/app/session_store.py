from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DB_PATH = Path(__file__).resolve().parent / "tmp_db.json"


def _load_all() -> Dict[str, Dict[str, Any]]:
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
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DB_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ensure_session(session_id: str) -> None:
    data = _load_all()
    data.setdefault(session_id, {"messages": []})
    _save_all(data)


def get_session(session_id: str) -> Dict[str, Any]:
    data = _load_all()
    return data.get(session_id, {"messages": []})


def list_sessions() -> Dict[str, Dict[str, Any]]:
    return _load_all()


def append_message(session_id: str, message: Dict[str, Any]) -> None:
    data = _load_all()
    session = data.setdefault(session_id, {"messages": []})
    messages: List[Dict[str, Any]] = session.setdefault("messages", [])
    message.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    messages.append(message)
    _save_all(data)


def overwrite_session(session_id: str, messages: List[Dict[str, Any]]) -> None:
    data = _load_all()
    data[session_id] = {"messages": messages}
    _save_all(data)
