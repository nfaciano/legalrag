"""
Template manager for handling Word document template uploads and storage.
Uses SQLite for metadata persistence (atomic, concurrent-safe).
"""

import os
import uuid
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict
from contextlib import contextmanager
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

ALLOWED_TEMPLATE_TYPES = {".docx"}
MAX_TEMPLATE_SIZE = 10 * 1024 * 1024  # 10MB

# Database file location (same directory as user_settings.db)
DB_PATH = Path("./data/uploads/template_metadata.db")


@contextmanager
def _get_db_connection():
    """Context manager for database connections."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _init_template_db():
    """Initialize the template metadata database."""
    with _get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                template_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                upload_date TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_templates_user_id ON templates(user_id)
        """)
        conn.commit()


# Initialize on module load
_init_template_db()


class TemplateManager:
    """Manages Word document template storage and retrieval."""

    def __init__(self, storage_dir: str = "./data/uploads/templates"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._migrate_json_metadata()

    def _migrate_json_metadata(self):
        """One-time migration from legacy metadata.json to SQLite."""
        import json

        legacy_file = self.storage_dir / "metadata.json"
        if not legacy_file.exists():
            return

        try:
            with open(legacy_file, "r") as f:
                legacy_data = json.load(f)

            with _get_db_connection() as conn:
                for user_id, templates in legacy_data.items():
                    for template_id, tpl in templates.items():
                        conn.execute(
                            """INSERT OR IGNORE INTO templates
                               (template_id, user_id, original_filename, file_path, file_size, upload_date)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (
                                tpl["template_id"],
                                user_id,
                                tpl["original_filename"],
                                tpl["file_path"],
                                tpl["file_size"],
                                tpl["upload_date"],
                            ),
                        )
                conn.commit()

            # Rename legacy file so migration doesn't run again
            legacy_file.rename(legacy_file.with_suffix(".json.bak"))
            logger.info("Migrated template metadata from JSON to SQLite")
        except Exception as e:
            logger.error(f"Failed to migrate template metadata: {e}")

    def save_template(
        self, user_id: str, filename: str, file_content: bytes
    ) -> Dict[str, str]:
        """
        Save a Word document template for a user.

        Args:
            user_id: User ID from Clerk authentication
            filename: Original filename
            file_content: Word doc file bytes

        Returns:
            Dict with template_id, filename, and file path
        """
        # Validate file size
        if len(file_content) > MAX_TEMPLATE_SIZE:
            raise ValueError(f"File size exceeds maximum of {MAX_TEMPLATE_SIZE} bytes")

        # Validate file type
        file_ext = Path(filename).suffix.lower()
        if file_ext not in ALLOWED_TEMPLATE_TYPES:
            raise ValueError(
                f"Invalid file type. Allowed types: {', '.join(ALLOWED_TEMPLATE_TYPES)}"
            )

        # Create user directory
        user_dir = self.storage_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique template ID
        template_id = f"tpl_{uuid.uuid4().hex[:12]}"

        # Save file with template ID as filename
        safe_filename = f"{template_id}.docx"
        file_path = user_dir / safe_filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        # Store metadata in SQLite
        upload_date = datetime.utcnow().isoformat()
        with _get_db_connection() as conn:
            conn.execute(
                """INSERT INTO templates
                   (template_id, user_id, original_filename, file_path, file_size, upload_date)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (template_id, user_id, filename, str(file_path), len(file_content), upload_date),
            )
            conn.commit()

        logger.info(f"Saved template {template_id} for user {user_id}")

        return {
            "template_id": template_id,
            "original_filename": filename,
            "file_path": str(file_path),
            "file_size": len(file_content),
            "upload_date": upload_date,
        }

    def get_template(self, user_id: str, template_id: str) -> Optional[Dict]:
        """Get template metadata and file path."""
        with _get_db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM templates WHERE template_id = ? AND user_id = ?",
                (template_id, user_id),
            ).fetchone()

        if row:
            return dict(row)
        return None

    def get_template_path(self, user_id: str, template_id: str) -> Optional[Path]:
        """Get the file path for a template."""
        template = self.get_template(user_id, template_id)
        if template:
            return Path(template["file_path"])
        return None

    def list_templates(self, user_id: str) -> List[Dict]:
        """List all templates for a user."""
        with _get_db_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM templates WHERE user_id = ? ORDER BY upload_date DESC",
                (user_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def delete_template(self, user_id: str, template_id: str) -> bool:
        """Delete a template."""
        template = self.get_template(user_id, template_id)
        if not template:
            return False

        # Delete file
        file_path = Path(template["file_path"])
        if file_path.exists():
            file_path.unlink()

        # Remove metadata
        with _get_db_connection() as conn:
            conn.execute(
                "DELETE FROM templates WHERE template_id = ? AND user_id = ?",
                (template_id, user_id),
            )
            conn.commit()

        logger.info(f"Deleted template {template_id} for user {user_id}")
        return True


# Singleton instance
_template_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """Get or create the singleton TemplateManager instance."""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager
