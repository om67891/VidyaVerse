"""
SQLite Database Connection Provider for VidyaVerse.
Ensures thread-safe connections, foreign key enforcement, WAL mode, and directory creation.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from backend.config import settings


def get_db_path() -> Path:
    """Return verified path to local SQLite database, ensuring parent directory exists."""
    db_path = settings.database_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def init_connection(db_path: Path) -> sqlite3.Connection:
    """Create a new SQLite connection with WAL journal mode and foreign keys enabled."""
    conn = sqlite3.connect(
        str(db_path),
        timeout=30.0,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for acquiring a transactional database connection."""
    db_path = get_db_path()
    conn = init_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
