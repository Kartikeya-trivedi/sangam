"""SQLite connection management (thread-local) + schema init.

FastAPI runs sync routes in a threadpool, so we keep one connection per thread. WAL mode +
a busy timeout give us safe concurrent reads with the occasional write. Reliable and fast at
demo scale; no external service to fall over.
"""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from config import settings

_SCHEMA = Path(__file__).resolve().parent / "schema.sql"
_local = threading.local()
_initialized: set[str] = set()
_init_lock = threading.Lock()


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def get_conn() -> sqlite3.Connection:
    """Return this thread's connection, creating + initializing the DB on first use."""
    db_path = settings.db_path
    conn = getattr(_local, "conn", None)
    if conn is not None and getattr(_local, "db_path", None) == db_path:
        return conn
    conn = _connect(db_path)
    _local.conn = conn
    _local.db_path = db_path
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection | None = None) -> None:
    """Create tables/indexes if absent (idempotent). Safe to call repeatedly."""
    db_path = settings.db_path
    if conn is None:
        conn = get_conn()
    with _init_lock:
        if db_path in _initialized:
            return
        conn.executescript(_SCHEMA.read_text())
        conn.commit()
        _initialized.add(db_path)


def reset_db() -> None:
    """Drop all rows (used by tests + reseed). Keeps schema."""
    conn = get_conn()
    for tbl in ("persons", "persons_fts", "audit_log", "notifications", "announcements"):
        conn.execute(f"DELETE FROM {tbl}")
    conn.commit()
