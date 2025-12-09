"""
Envelope generator for creating print-ready envelope documents.
"""

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class EnvelopeGenerator:
    """Generates print-ready envelope documents in #10 business envelope format."""

    # Standard #10 envelope dimensions: 9.5" x 4.125"
    ENVELOPE_WIDTH = Inches(9.5)
    ENVELOPE_HEIGHT = Inches(4.125)

    def generate_envelope(
        self,
        output_path: Path,
        return_address: Dict[str, str],
        recipient_address: Dict[str, str]
    ) -> Path:
        """
        Generate a print-ready envelope document.

        Args:
            output_path: Where to save the envelope document
            return_address: Dict with keys: name, line1, line2, city_state_zip
            recipient_address: Dict with keys: name, line1, line2, city_state_zip

        Returns:
            Path to generated envelope document
        """
        try:
            # Create new document
            doc = Document()

            # Set page size to envelope dimensions (landscape)
            section = doc.sections[0]
            section.page_width = self.ENVELOPE_WIDTH
            section.page_height = self.ENVELOPE_HEIGHT

            # Set margins
            section.top_margin = Inches(0.5)
            section.bottom_margin = Inches(0.5)
            section.left_margin = Inches(0.5)
            section.right_margin = Inches(0.5)

            # Add return address (top-left)
            self._add_return_address(doc, return_address)

            # Add spacing before recipient address
            for _ in range(4):
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(0)

            # Add recipient address (centered)
            self._add_recipient_address(doc, recipient_address)

            # Save document
            doc.save(str(output_path))
            logger.info(f"Generated envelope: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Error generating envelope: {e}", exc_info=True)
            raise ValueError(f"Failed to generate envelope: {str(e)}")

    def _add_return_address(self, doc: Document, address: Dict[str, str]):
        """Add return address to top-left of envelope."""
        lines = [
            address.get('name', ''),
            address.get('line1', ''),
            address.get('line2', ''),
            address.get('city_state_zip', '')
        ]

        for line in lines:
            if line.strip():
                p = doc.add_paragraph(line)
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT

                # Reduce spacing between lines for compact return address
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.0

                # Set font
                for run in p.runs:
                    run.font.name = 'Arial'
                    run.font.size = Pt(10)

    def _add_recipient_address(self, doc: Document, address: Dict[str, str]):
        """Add recipient address centered on envelope."""
        lines = [
            address.get('name', ''),
            address.get('line1', ''),
            address.get('line2', ''),
            address.get('city_state_zip', '')
        ]

        for line in lines:
            if line.strip():
                p = doc.add_paragraph(line)
                # Center the recipient address
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER

                # Compact spacing
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.0

                # Set font - slightly larger for recipient
                for run in p.runs:
                    run.font.name = 'Arial'
                    run.font.size = Pt(12)


# Singleton instance
_envelope_generator: Optional[EnvelopeGenerator] = None


def get_envelope_generator() -> EnvelopeGenerator:
    """Get or create the singleton EnvelopeGenerator instance."""
    global _envelope_generator
    if _envelope_generator is None:
        _envelope_generator = EnvelopeGenerator()
    return _envelope_generator
