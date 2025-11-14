import sqlite3
import os

DB_PATH = os.getenv("SQLITE_DB_PATH", "/app/data/metadata.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- Drop all user tables first (ignore SQLite internal tables) ---
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()
    for (table_name,) in tables:
        cursor.execute(f"DROP TABLE IF EXISTS \"{table_name}\";")
    
    # --- Admin users table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # --- Schema metadata table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schema_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        schema_name TEXT UNIQUE NOT NULL,
        columns TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()
    print(f"✅ SQLite DB initialized at: {DB_PATH}")

if __name__ == "__main__":
    init_db()
