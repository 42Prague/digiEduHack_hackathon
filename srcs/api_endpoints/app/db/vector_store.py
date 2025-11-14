import sqlite3
import json
import time
from typing import List, Dict

DB_PATH = "rag_demo.sqlite3"

class VectorStore:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def initialize(self):
        with self._conn() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_text TEXT NOT NULL,
                tokens_json TEXT NOT NULL,
                metadata_json TEXT,
                created_at REAL
            )
            """)
            conn.commit()

    def insert_chunks(self, chunks: List[str], tokens_list: List[Dict[str,int]], metadata: Dict = None):
        metadata_json = json.dumps(metadata or {})
        now = time.time()
        with self._conn() as conn:
            for chunk, tokens in zip(chunks, tokens_list):
                conn.execute(
                    "INSERT INTO chunks (chunk_text, tokens_json, metadata_json, created_at) VALUES (?, ?, ?, ?)",
                    (chunk, json.dumps(tokens), metadata_json, now)
                )
            conn.commit()

    def all_chunks(self):
        with self._conn() as conn:
            cur = conn.execute("SELECT id, chunk_text, tokens_json, metadata_json FROM chunks")
            rows = cur.fetchall()
        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "chunk": r[1],
                "tokens": json.loads(r[2]),
                "metadata": json.loads(r[3] or "{}")
            })
        return results

    def clear(self):
        with self._conn() as conn:
            conn.execute("DELETE FROM chunks")
            conn.commit()
