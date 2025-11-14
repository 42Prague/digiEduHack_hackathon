import sqlite3
import os
from typing import Optional, Dict, Union
import bcrypt
import json

DB_PATH = os.getenv("SQLITE_DB_PATH", "/app/data/metadata.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def create_admin_user(username: str, password: str):
    """Create an admin user with bcrypt hash."""
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO admin_users (username, password_hash) VALUES (?, ?)",
                    (username, hashed.decode()))
        conn.commit()

def get_user(username: str) -> Optional[dict]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, password_hash FROM admin_users WHERE username = ?", (username,))
        row = cur.fetchone()
        if row:
            return {"id": row[0], "username": row[1], "password_hash": row[2]}
    return None

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def insert_schema_metadata(schema_name: str, columns: dict, description: str = "") -> bool:
    """
    Insert a schema metadata entry. 
    `columns` can be either:
    - Old format: dict mapping column name -> type (string)
    - New format: dict mapping column name -> {type: str, description: str}
    Returns True if inserted (or already exists), False on error.
    Normalizes columns to the new format before storing.
    """
    try:
        # Normalize columns to new format
        normalized_columns = {}
        for col_name, col_info in columns.items():
            if isinstance(col_info, dict) and "type" in col_info:
                # Already in new format
                normalized_columns[col_name] = col_info.copy()
            else:
                # Old format: just a string type
                normalized_columns[col_name] = {
                    "type": str(col_info) if col_info else "string",
                    "description": ""
                }
        
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO schema_metadata (schema_name, columns, description) VALUES (?, ?, ?)",
                (schema_name, json.dumps(normalized_columns, ensure_ascii=False), description),
            )
            conn.commit()
        return True
    except Exception:
        return False

def get_schema_metadata(schema_name: str) -> dict | None:
    """Return schema metadata as a dict or None if not found."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, schema_name, columns, description FROM schema_metadata WHERE schema_name = ?", (schema_name,))
        row = cur.fetchone()
        if not row:
            return None
        raw_cols = row[2]
        if raw_cols is None or raw_cols == "":
            columns = {}
        elif isinstance(raw_cols, (dict, list)):
            columns = raw_cols
        else:
            try:
                columns = json.loads(raw_cols)
            except (json.JSONDecodeError, TypeError):
                columns = {}
        return {"id": row[0], "schema_name": row[1], "columns": columns, "description": row[3]}

def add_column_to_schema(
    schema_name: str,
    column_or_columns: Union[str, Dict[str, Union[str, Dict[str, str]]]],
    column_type: Optional[str] = None,
    overwrite: bool = False
) -> bool:
    """
    Add one or many columns to an existing schema metadata entry.
    Supports both old format (column_name -> type) and new format (column_name -> {type, description}).

    Parameters:
    - schema_name: name of the schema to update
    - column_or_columns: either:
        - a single column name (str), or
        - a dict mapping column_name -> column_type (str), or
        - a dict mapping column_name -> {type: str, description: str}
    - column_type: required when column_or_columns is a str
    - overwrite: if True, existing column types will be replaced

    Behavior:
    - If the schema does not exist, returns False.
    - If adding multiple columns and any column already exists and overwrite is False, the operation is aborted and returns False.
    - Returns True on success, False on error or no-op.
    - Normalizes all columns to the new format: {type: str, description: str}
    """
    try:
        meta = get_schema_metadata(schema_name)
        if meta is None:
            return False

        current_cols = meta.get("columns", {}) or {}
        
        # Normalize existing columns to new format (for backward compatibility)
        normalized_current = {}
        for col_name, col_info in current_cols.items():
            if isinstance(col_info, dict) and "type" in col_info:
                # Already in new format
                normalized_current[col_name] = col_info.copy()
            else:
                # Old format: just a string type
                normalized_current[col_name] = {
                    "type": str(col_info) if col_info else "string",
                    "description": ""
                }

        # Process new columns
        if isinstance(column_or_columns, dict):
            new_cols = column_or_columns
        else:
            if column_type is None:
                return False
            new_cols = {column_or_columns: column_type}

        # Normalize new columns to new format
        normalized_new = {}
        for col_name, col_info in new_cols.items():
            if isinstance(col_info, dict) and "type" in col_info:
                # Already in new format
                normalized_new[col_name] = col_info.copy()
            else:
                # Old format: just a string type
                normalized_new[col_name] = {
                    "type": str(col_info) if col_info else "string",
                    "description": ""
                }

        if not overwrite:
            for k in normalized_new:
                if k in normalized_current:
                    return False

        # Merge columns
        merged = normalized_current.copy()
        merged.update(normalized_new)

        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE schema_metadata SET columns = ? WHERE schema_name = ?",
                (json.dumps(merged, ensure_ascii=False), schema_name),
            )
            conn.commit()
        return True
    except Exception:
        return False

def get_logs(from_date: str, limit: Optional[int] = None) -> list[dict]:
    """Retrieve logs from the metadata sqlite DB since `from_date` (ISO format)."""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            query = "SELECT ts, level, component, message, meta FROM pipeline_logs WHERE ts >= ? ORDER BY ts DESC"
            params = [from_date]
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
            cur.execute(query, params)
            rows = cur.fetchall()
            logs = []
            for row in rows:
                meta_json = row[4]
                try:
                    meta = json.loads(meta_json) if meta_json else {}
                except (json.JSONDecodeError, TypeError):
                    meta = {}
                logs.append({
                    "ts": row[0],
                    "level": row[1],
                    "component": row[2],
                    "message": row[3],
                    "meta": meta
                })
        return logs
    except Exception:
        return []