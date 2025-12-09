"""
Letterhead manager for handling letterhead image uploads and storage.
"""

import os
import uuid
from pathlib import Path
from typing import Optional, List, Dict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {".png", ".jpg", ".jpeg"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


class LetterheadManager:
    """Manages letterhead image storage and retrieval."""

    def __init__(self, storage_dir: str = "./data/uploads/letterheads"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.storage_dir / "metadata.json"
        self._load_metadata()

    def _load_metadata(self):
        """Load letterhead metadata from JSON file."""
        import json

        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}

    def _save_metadata(self):
        """Save letterhead metadata to JSON file."""
        import json

        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=2)

    def save_letterhead(
        self, user_id: str, filename: str, file_content: bytes
    ) -> Dict[str, str]:
        """
        Save a letterhead image for a user.

        Args:
            user_id: User ID from Clerk authentication
            filename: Original filename
            file_content: Image file bytes

        Returns:
            Dict with letterhead_id, filename, and file path
        """
        # Validate file size
        if len(file_content) > MAX_IMAGE_SIZE:
            raise ValueError(f"File size exceeds maximum of {MAX_IMAGE_SIZE} bytes")

        # Validate file type
        file_ext = Path(filename).suffix.lower()
        if file_ext not in ALLOWED_IMAGE_TYPES:
            raise ValueError(
                f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )

        # Create user directory
        user_dir = self.storage_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique letterhead ID
        letterhead_id = f"lh_{uuid.uuid4().hex[:12]}"

        # Save file with letterhead ID as filename
        safe_filename = f"{letterhead_id}{file_ext}"
        file_path = user_dir / safe_filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        # Store metadata
        if user_id not in self.metadata:
            self.metadata[user_id] = {}

        self.metadata[user_id][letterhead_id] = {
            "letterhead_id": letterhead_id,
            "original_filename": filename,
            "file_path": str(file_path),
            "file_size": len(file_content),
            "upload_date": datetime.utcnow().isoformat(),
        }

        self._save_metadata()

        logger.info(f"Saved letterhead {letterhead_id} for user {user_id}")

        return self.metadata[user_id][letterhead_id]

    def get_letterhead(self, user_id: str, letterhead_id: str) -> Optional[Dict]:
        """Get letterhead metadata and file path."""
        if user_id not in self.metadata:
            return None

        return self.metadata[user_id].get(letterhead_id)

    def get_letterhead_path(self, user_id: str, letterhead_id: str) -> Optional[Path]:
        """Get the file path for a letterhead."""
        letterhead = self.get_letterhead(user_id, letterhead_id)
        if letterhead:
            return Path(letterhead["file_path"])
        return None

    def list_letterheads(self, user_id: str) -> List[Dict]:
        """List all letterheads for a user."""
        if user_id not in self.metadata:
            return []

        return list(self.metadata[user_id].values())

    def delete_letterhead(self, user_id: str, letterhead_id: str) -> bool:
        """Delete a letterhead."""
        if user_id not in self.metadata or letterhead_id not in self.metadata[user_id]:
            return False

        letterhead = self.metadata[user_id][letterhead_id]
        file_path = Path(letterhead["file_path"])

        # Delete file
        if file_path.exists():
            file_path.unlink()

        # Remove metadata
        del self.metadata[user_id][letterhead_id]
        self._save_metadata()

        logger.info(f"Deleted letterhead {letterhead_id} for user {user_id}")

        return True


# Singleton instance
_letterhead_manager: Optional[LetterheadManager] = None


def get_letterhead_manager() -> LetterheadManager:
    """Get or create the singleton LetterheadManager instance."""
    global _letterhead_manager
    if _letterhead_manager is None:
        _letterhead_manager = LetterheadManager()
    return _letterhead_manager
