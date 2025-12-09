"""
PDF generator using ReportLab for creating formatted legal documents.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.pdfgen import canvas
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Generates formatted PDF documents with letterheads."""

    def __init__(self):
        self.page_width, self.page_height = letter
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for legal documents."""
        # Date style (right-aligned)
        self.styles.add(
            ParagraphStyle(
                name="DateStyle",
                parent=self.styles["Normal"],
                fontSize=12,
                alignment=TA_RIGHT,
                spaceAfter=24,
            )
        )

        # Recipient address style
        self.styles.add(
            ParagraphStyle(
                name="RecipientAddress",
                parent=self.styles["Normal"],
                fontSize=12,
                alignment=TA_LEFT,
                spaceAfter=12,
                leading=14,
            )
        )

        # Subject line style
        self.styles.add(
            ParagraphStyle(
                name="SubjectLine",
                parent=self.styles["Normal"],
                fontSize=12,
                alignment=TA_LEFT,
                spaceAfter=12,
                fontName="Helvetica-Bold",
            )
        )

        # Salutation style
        self.styles.add(
            ParagraphStyle(
                name="Salutation",
                parent=self.styles["Normal"],
                fontSize=12,
                alignment=TA_LEFT,
                spaceAfter=12,
            )
        )

        # Body text style
        self.styles.add(
            ParagraphStyle(
                name="BodyText",
                parent=self.styles["Normal"],
                fontSize=12,
                alignment=TA_LEFT,
                spaceAfter=12,
                leading=18,
                firstLineIndent=0.5 * inch,
            )
        )

        # Closing style
        self.styles.add(
            ParagraphStyle(
                name="Closing",
                parent=self.styles["Normal"],
                fontSize=12,
                alignment=TA_RIGHT,
                spaceAfter=48,
            )
        )

        # Signature style
        self.styles.add(
            ParagraphStyle(
                name="Signature",
                parent=self.styles["Normal"],
                fontSize=12,
                alignment=TA_RIGHT,
                spaceAfter=12,
            )
        )

        # Initials style
        self.styles.add(
            ParagraphStyle(
                name="Initials",
                parent=self.styles["Normal"],
                fontSize=10,
                alignment=TA_LEFT,
                spaceAfter=6,
            )
        )

    def generate_letterhead_letter(
        self,
        output_path: Path,
        letterhead_image_path: Optional[Path],
        date: str,
        recipient_name: str,
        recipient_company: Optional[str],
        recipient_address: str,
        subject: Optional[str],
        salutation: str,
        body_text: str,
        closing: str,
        signature_name: str,
        initials: str,
        enclosures: Optional[str] = None,
    ) -> Path:
        """
        Generate a professional letterhead letter PDF.

        Args:
            output_path: Where to save the PDF
            letterhead_image_path: Path to letterhead image (optional)
            date: Date string
            recipient_name: Recipient's name
            recipient_company: Recipient's company (optional)
            recipient_address: Full address (can be multi-line)
            subject: Subject line (e.g., "Re: Case Name")
            salutation: Greeting (e.g., "Dear Mr. Smith:")
            body_text: Main letter body
            closing: Closing phrase (e.g., "Very truly yours,")
            signature_name: Name for signature line
            initials: Attorney/paralegal initials (e.g., "JPH/NF")
            enclosures: Enclosure notation (e.g., "Enc:" or "Enc: (2)")

        Returns:
            Path to generated PDF
        """
        # Create PDF
        c = canvas.Canvas(str(output_path), pagesize=letter)
        width, height = letter

        y_position = height - (0.75 * inch)  # Start position

        # Add letterhead image if provided
        if letterhead_image_path and letterhead_image_path.exists():
            try:
                # Add letterhead at top (adjust size as needed)
                letterhead_height = 1.2 * inch
                c.drawImage(
                    str(letterhead_image_path),
                    0.75 * inch,
                    height - letterhead_height - (0.5 * inch),
                    width=(width - 1.5 * inch),
                    height=letterhead_height,
                    preserveAspectRatio=True,
                    anchor="nw",
                )
                y_position -= letterhead_height + (0.3 * inch)
            except Exception as e:
                logger.error(f"Error adding letterhead image: {e}")

        # Date (right-aligned)
        c.setFont("Helvetica", 12)
        date_x = width - (1.5 * inch)
        c.drawRightString(date_x, y_position, date)
        y_position -= 0.5 * inch

        # Recipient address (left-aligned)
        c.setFont("Helvetica", 12)
        x_margin = 0.75 * inch
        c.drawString(x_margin, y_position, recipient_name)
        y_position -= 0.18 * inch

        if recipient_company:
            c.drawString(x_margin, y_position, recipient_company)
            y_position -= 0.18 * inch

        # Handle multi-line address
        address_lines = recipient_address.split("\n")
        for line in address_lines:
            c.drawString(x_margin, y_position, line.strip())
            y_position -= 0.18 * inch

        y_position -= 0.2 * inch

        # Subject line
        if subject:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x_margin, y_position, subject)
            y_position -= 0.3 * inch

        # Salutation
        c.setFont("Helvetica", 12)
        c.drawString(x_margin, y_position, salutation)
        y_position -= 0.3 * inch

        # Body text (with word wrapping)
        body_lines = self._wrap_text(body_text, width - (1.5 * inch) - (0.5 * inch))
        for line in body_lines:
            if y_position < (1 * inch):  # Check for page break
                c.showPage()
                y_position = height - (1 * inch)
                c.setFont("Helvetica", 12)

            # Add indent for first line of paragraphs
            line_x = x_margin + (0.5 * inch) if line.startswith("\t") else x_margin
            c.drawString(line_x, y_position, line.lstrip("\t"))
            y_position -= 0.18 * inch

        y_position -= 0.3 * inch

        # Closing (right-aligned)
        c.drawRightString(date_x, y_position, closing)
        y_position -= 0.8 * inch  # Space for signature

        # Signature name (right-aligned)
        c.drawRightString(date_x, y_position, signature_name)
        y_position -= 0.5 * inch

        # Initials (left-aligned)
        c.drawString(x_margin, y_position, initials)
        y_position -= 0.2 * inch

        # Enclosures
        if enclosures:
            c.drawString(x_margin, y_position, enclosures)

        c.save()

        logger.info(f"Generated PDF: {output_path}")
        return output_path

    def _wrap_text(self, text: str, max_width_points: float) -> list:
        """
        Wrap text to fit within max width.

        Args:
            text: Text to wrap
            max_width_points: Maximum width in points

        Returns:
            List of wrapped lines
        """
        from reportlab.pdfbase.pdfmetrics import stringWidth

        lines = []
        paragraphs = text.split("\n")

        for para in paragraphs:
            if not para.strip():
                lines.append("")
                continue

            # Add tab for paragraph indent
            words = para.strip().split()
            current_line = "\t"  # Start with tab for indent
            line_width = stringWidth("\t", "Helvetica", 12)

            for word in words:
                word_width = stringWidth(word + " ", "Helvetica", 12)

                if line_width + word_width <= max_width_points:
                    current_line += word + " "
                    line_width += word_width
                else:
                    lines.append(current_line.rstrip())
                    current_line = word + " "
                    line_width = stringWidth(current_line, "Helvetica", 12)

            if current_line.strip():
                lines.append(current_line.rstrip())

            lines.append("")  # Add space between paragraphs

        return lines


# Singleton instance
_pdf_generator: Optional[PDFGenerator] = None


def get_pdf_generator() -> PDFGenerator:
    """Get or create the singleton PDFGenerator instance."""
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = PDFGenerator()
    return _pdf_generator
