"""
User settings database management using SQLite.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database file location
DB_PATH = Path("./uploads/user_settings.db")


def init_user_settings_db():
    """Initialize the user settings database and create table if not exists."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT PRIMARY KEY,
                return_address_name TEXT,
                return_address_line1 TEXT,
                return_address_line2 TEXT,
                return_address_city_state_zip TEXT,
                signature_name TEXT,
                initials TEXT,
                closing TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        logger.info("User settings database initialized")


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_user_settings(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user settings from database.

    Args:
        user_id: User ID from authentication

    Returns:
        Dict with settings or None if not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM user_settings WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        if row:
            return {
                "return_address_name": row["return_address_name"] or "",
                "return_address_line1": row["return_address_line1"] or "",
                "return_address_line2": row["return_address_line2"] or "",
                "return_address_city_state_zip": row["return_address_city_state_zip"] or "",
                "signature_name": row["signature_name"] or "",
                "initials": row["initials"] or "",
                "closing": row["closing"] or "Very truly yours,"
            }
        return None


def save_user_settings(user_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save user settings to database (insert or update).

    Args:
        user_id: User ID from authentication
        settings: Dict with settings to save

    Returns:
        The saved settings
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Upsert (insert or replace)
        cursor.execute("""
            INSERT OR REPLACE INTO user_settings (
                user_id,
                return_address_name,
                return_address_line1,
                return_address_line2,
                return_address_city_state_zip,
                signature_name,
                initials,
                closing,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            user_id,
            settings.get("return_address_name", ""),
            settings.get("return_address_line1", ""),
            settings.get("return_address_line2", ""),
            settings.get("return_address_city_state_zip", ""),
            settings.get("signature_name", ""),
            settings.get("initials", ""),
            settings.get("closing", "Very truly yours,")
        ))

        conn.commit()
        logger.info(f"Saved settings for user {user_id}")

        return settings


# Initialize database on module import
init_user_settings_db()
