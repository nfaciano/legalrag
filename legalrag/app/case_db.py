"""
Case database management using SQLite.
Stores case information (parties, case numbers, courts) for reuse across filings.
"""

import sqlite3
import json
import uuid
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = Path("./data/uploads/cases.db")


def init_cases_db():
    """Initialize the cases database and create table if not exists."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                case_name TEXT NOT NULL,
                case_number TEXT NOT NULL,
                court_name TEXT NOT NULL,
                plaintiff_names TEXT NOT NULL,
                defendant_names TEXT NOT NULL,
                plaintiff_label TEXT DEFAULT 'VS.',
                file_reference TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cases_user_id ON cases(user_id)
        """)
        conn.commit()
        logger.info("Cases database initialized")


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a database row to a dict with JSON-parsed list fields."""
    d = dict(row)
    d["plaintiff_names"] = json.loads(d["plaintiff_names"])
    d["defendant_names"] = json.loads(d["defendant_names"])
    return d


def create_case(user_id: str, case_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new case."""
    case_id = f"case_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()

    with get_db_connection() as conn:
        conn.execute(
            """INSERT INTO cases
               (case_id, user_id, case_name, case_number, court_name,
                plaintiff_names, defendant_names, plaintiff_label, file_reference,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                case_id,
                user_id,
                case_data["case_name"],
                case_data["case_number"],
                case_data["court_name"],
                json.dumps(case_data["plaintiff_names"]),
                json.dumps(case_data["defendant_names"]),
                case_data.get("plaintiff_label", "VS."),
                case_data.get("file_reference", ""),
                now,
                now,
            ),
        )
        conn.commit()

    logger.info(f"Created case {case_id} for user {user_id}")
    return get_case(user_id, case_id)


def get_case(user_id: str, case_id: str) -> Optional[Dict[str, Any]]:
    """Get a single case by ID."""
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM cases WHERE case_id = ? AND user_id = ?",
            (case_id, user_id),
        ).fetchone()

    if row:
        return _row_to_dict(row)
    return None


def list_cases(user_id: str) -> List[Dict[str, Any]]:
    """List all cases for a user."""
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM cases WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()

    return [_row_to_dict(row) for row in rows]


def update_case(user_id: str, case_id: str, case_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing case."""
    existing = get_case(user_id, case_id)
    if not existing:
        return None

    now = datetime.utcnow().isoformat()

    with get_db_connection() as conn:
        conn.execute(
            """UPDATE cases SET
               case_name = ?, case_number = ?, court_name = ?,
               plaintiff_names = ?, defendant_names = ?,
               plaintiff_label = ?, file_reference = ?, updated_at = ?
               WHERE case_id = ? AND user_id = ?""",
            (
                case_data["case_name"],
                case_data["case_number"],
                case_data["court_name"],
                json.dumps(case_data["plaintiff_names"]),
                json.dumps(case_data["defendant_names"]),
                case_data.get("plaintiff_label", "VS."),
                case_data.get("file_reference", ""),
                now,
                case_id,
                user_id,
            ),
        )
        conn.commit()

    logger.info(f"Updated case {case_id} for user {user_id}")
    return get_case(user_id, case_id)


def delete_case(user_id: str, case_id: str) -> bool:
    """Delete a case."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM cases WHERE case_id = ? AND user_id = ?",
            (case_id, user_id),
        )
        conn.commit()

    deleted = cursor.rowcount > 0
    if deleted:
        logger.info(f"Deleted case {case_id} for user {user_id}")
    return deleted


# Initialize database on module import
init_cases_db()
