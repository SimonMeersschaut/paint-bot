"""Minimal SQLite helpers for execution package.

Provides: init_db, log_progress, close_db
"""
import sqlite3
from datetime import datetime
from typing import Optional

DEFAULT_DB_PATH = 'data/progress.db'

def init_db(path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create or open the progress DB and ensure schema exists."""
    conn = sqlite3.connect(path)
    conn.execute(
        '''CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stroke_index INTEGER NOT NULL,
            ts TEXT NOT NULL
        )'''
    )
    conn.commit()
    return conn


def log_progress(conn: sqlite3.Connection, stroke_index: int, ts: Optional[str] = None) -> None:
    """Insert a progress row with UTC ISO timestamp (auto-generated if not given)."""
    if ts is None:
        ts = datetime.utcnow().isoformat()
    conn.execute("INSERT INTO progress (stroke_index, ts) VALUES (?, ?)", (stroke_index, ts))
    conn.commit()


def close_db(conn: sqlite3.Connection) -> None:
    """Close the DB connection."""
    try:
        conn.close()
    except Exception:
        pass
