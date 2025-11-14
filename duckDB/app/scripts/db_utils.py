import sqlite3
import os
from typing import Optional
import json
DB_PATH = os.getenv("SQLITE_DB_PATH", "/app/data/metadata.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def create_logs_table():
    """Ensure pipeline_logs table exists in the metadata sqlite DB."""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS pipeline_logs (
                    ts TEXT,
                    level TEXT,
                    component TEXT,
                    message TEXT,
                    meta TEXT
                )
                """
            )
            conn.commit()
        return True
    except Exception:
        return False

def insert_log_to_sqlite(ts: str, level: str, component: str, message: str, meta: Optional[dict] = None) -> bool:
    """Insert one log row into the metadata sqlite DB (meta stored as JSON)."""
    try:
        meta_json = json.dumps(meta or {}, ensure_ascii=False)
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO pipeline_logs (ts, level, component, message, meta) VALUES (?, ?, ?, ?, ?)",
                (ts, level, component, message, meta_json),
            )
            conn.commit()
        return True
    except Exception:
        return False