"""
Template manager for handling Word document template uploads and storage.
"""

import os
import uuid
from pathlib import Path
from typing import Optional, List, Dict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

ALLOWED_TEMPLATE_TYPES = {".docx"}
MAX_TEMPLATE_SIZE = 10 * 1024 * 1024  # 10MB


class TemplateManager:
    """Manages Word document template storage and retrieval."""

    def __init__(self, storage_dir: str = "./data/uploads/templates"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.storage_dir / "metadata.json"
        self._load_metadata()

    def _load_metadata(self):
        """Load template metadata from JSON file."""
        import json

        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}

    def _save_metadata(self):
        """Save template metadata to JSON file."""
        import json

        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=2)

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

        # Store metadata
        if user_id not in self.metadata:
            self.metadata[user_id] = {}

        self.metadata[user_id][template_id] = {
            "template_id": template_id,
            "original_filename": filename,
            "file_path": str(file_path),
            "file_size": len(file_content),
            "upload_date": datetime.utcnow().isoformat(),
        }

        self._save_metadata()

        logger.info(f"Saved template {template_id} for user {user_id}")

        return self.metadata[user_id][template_id]

    def get_template(self, user_id: str, template_id: str) -> Optional[Dict]:
        """Get template metadata and file path."""
        if user_id not in self.metadata:
            return None

        return self.metadata[user_id].get(template_id)

    def get_template_path(self, user_id: str, template_id: str) -> Optional[Path]:
        """Get the file path for a template."""
        template = self.get_template(user_id, template_id)
        if template:
            return Path(template["file_path"])
        return None

    def list_templates(self, user_id: str) -> List[Dict]:
        """List all templates for a user."""
        if user_id not in self.metadata:
            return []

        return list(self.metadata[user_id].values())

    def delete_template(self, user_id: str, template_id: str) -> bool:
        """Delete a template."""
        if user_id not in self.metadata or template_id not in self.metadata[user_id]:
            return False

        template = self.metadata[user_id][template_id]
        file_path = Path(template["file_path"])

        # Delete file
        if file_path.exists():
            file_path.unlink()

        # Remove metadata
        del self.metadata[user_id][template_id]
        self._save_metadata()

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
