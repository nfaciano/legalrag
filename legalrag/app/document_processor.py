import fitz  # PyMuPDF
from typing import List, Dict, Any
import hashlib
import logging
import os
import io
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

logger = logging.getLogger(__name__)

# Configure Tesseract for OCR support
if os.name == 'nt':  # Windows
    tesseract_path = Path(r"C:\Program Files\Tesseract-OCR")
    if tesseract_path.exists():
        pytesseract.pytesseract.tesseract_cmd = str(tesseract_path / 'tesseract.exe')
        if 'TESSDATA_PREFIX' not in os.environ:
            os.environ['TESSDATA_PREFIX'] = str(tesseract_path / 'tessdata')
        logger.info(f"Set Tesseract path to {pytesseract.pytesseract.tesseract_cmd}")
else:  # Linux (Railway production)
    # Tesseract is in standard location after apt-get install
    if Path('/usr/bin/tesseract').exists():
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    # Set tessdata if not already set
    if 'TESSDATA_PREFIX' not in os.environ:
        if Path('/usr/share/tesseract-ocr/4.00/tessdata').exists():
            os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/4.00/tessdata'
        elif Path('/usr/share/tesseract-ocr/tessdata').exists():
            os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/tessdata'


def preprocess_image_for_ocr(pix: fitz.Pixmap) -> Image.Image:
    """
    Preprocess image to improve OCR quality

    Args:
        pix: PyMuPDF Pixmap object

    Returns:
        Preprocessed PIL Image
    """
    # Convert pixmap to PIL Image
    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))

    # Convert to grayscale
    img = img.convert('L')

    # Upscale for better OCR (2x)
    new_size = (img.width * 2, img.height * 2)
    img = img.resize(new_size, Image.Resampling.LANCZOS)

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.5)

    # Denoise
    img = img.filter(ImageFilter.MedianFilter(size=3))

    # Convert to black and white with threshold (binarization)
    # This often helps OCR by removing gray areas
    threshold = 128
    img = img.point(lambda p: 255 if p > threshold else 0)

    return img


class DocumentChunk:
    """Represents a chunk of text from a document"""

    def __init__(
        self,
        text: str,
        document_id: str,
        filename: str,
        page: int,
        chunk_id: str,
        total_chunks: int,
        user_id: str = None,
        ocr_used: bool = False,
        ocr_pages: int = 0,
        total_pages: int = 0
    ):
        self.text = text
        self.document_id = document_id
        self.filename = filename
        self.page = page
        self.chunk_id = chunk_id
        self.total_chunks = total_chunks
        self.user_id = user_id
        self.ocr_used = ocr_used
        self.ocr_pages = ocr_pages
        self.total_pages = total_pages

    def to_metadata(self) -> Dict[str, Any]:
        """Convert to metadata dict for storage"""
        metadata = {
            "document_id": self.document_id,
            "filename": self.filename,
            "page": self.page,
            "chunk_id": self.chunk_id,
            "total_chunks": self.total_chunks,
            "upload_date": datetime.now().isoformat(),
            "ocr_used": self.ocr_used,
            "ocr_pages": self.ocr_pages,
            "total_pages": self.total_pages
        }
        if self.user_id:
            metadata["user_id"] = self.user_id
        return metadata


class DocumentProcessor:
    """Processes PDF documents into searchable chunks"""

    def __init__(
        self,
        chunk_size: int = 250,
        chunk_overlap: int = 25
    ):
        """
        Initialize document processor

        Args:
            chunk_size: Target number of words per chunk (reduced to 250 for better precision)
            chunk_overlap: Number of words to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_pdf(self, pdf_path: str, filename: str, user_id: str = None) -> List[DocumentChunk]:
        """
        Process a PDF file into chunks

        Args:
            pdf_path: Path to the PDF file
            filename: Original filename
            user_id: ID of the user who uploaded the document

        Returns:
            List of DocumentChunk objects
        """
        logger.info(f"Processing PDF: {filename} for user: {user_id}")

        # Generate document ID from filename and content
        document_id = self._generate_document_id(filename)

        # Extract text from PDF (returns OCR stats too)
        text_by_page, ocr_used, ocr_pages, total_pages = self._extract_text_from_pdf(pdf_path)

        # Combine all text
        full_text = " ".join([text for text in text_by_page.values()])

        # Create chunks
        chunks = self._create_chunks(
            full_text, document_id, filename, text_by_page, user_id,
            ocr_used, ocr_pages, total_pages
        )

        logger.info(f"Created {len(chunks)} chunks from {filename}")
        return chunks

    def _extract_text_from_pdf(self, pdf_path: str) -> tuple[Dict[int, str], bool, int, int]:
        """
        Extract text from PDF, organized by page
        Uses OCR fallback for scanned documents without embedded text

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (text_by_page dict, ocr_used bool, ocr_pages count, total_pages count)
        """
        text_by_page = {}
        ocr_pages = 0

        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)

            for page_num in range(total_pages):
                page = doc[page_num]

                # Try standard text extraction first (fast)
                text = page.get_text()

                # If no text found, use OCR (slower but handles scanned docs)
                if not text.strip():
                    logger.info(f"No embedded text on page {page_num + 1}, using OCR with preprocessing")
                    try:
                        # Convert page to high-resolution image
                        pix = page.get_pixmap(dpi=300)

                        # Preprocess image for better OCR quality
                        preprocessed_img = preprocess_image_for_ocr(pix)

                        # Use pytesseract with page segmentation mode 1 (automatic with OSD)
                        # Try PSM 3 first (fully automatic), then PSM 1 if that fails
                        try:
                            text = pytesseract.image_to_string(preprocessed_img, config='--psm 3')
                        except Exception:
                            text = pytesseract.image_to_string(preprocessed_img, config='--psm 1')

                        ocr_pages += 1
                        logger.info(f"OCR extracted {len(text)} characters from page {page_num + 1}")
                    except Exception as ocr_error:
                        logger.warning(f"OCR failed on page {page_num + 1}: {ocr_error}")
                        text = ""  # Empty text if OCR fails

                text_by_page[page_num + 1] = text  # 1-indexed pages

            doc.close()

            if ocr_pages > 0:
                logger.info(f"Used OCR on {ocr_pages}/{total_pages} pages")

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

        ocr_used = ocr_pages > 0
        return text_by_page, ocr_used, ocr_pages, total_pages

    def _create_chunks(
        self,
        text: str,
        document_id: str,
        filename: str,
        text_by_page: Dict[int, str],
        user_id: str = None,
        ocr_used: bool = False,
        ocr_pages: int = 0,
        total_pages: int = 0
    ) -> List[DocumentChunk]:
        """
        Split text into overlapping chunks

        Args:
            text: Full document text
            document_id: Unique document identifier
            filename: Original filename
            text_by_page: Text organized by page (for page attribution)
            user_id: ID of the user who uploaded the document
            ocr_used: Whether OCR was used on this document
            ocr_pages: Number of pages that required OCR
            total_pages: Total number of pages in document

        Returns:
            List of DocumentChunk objects
        """
        words = text.split()
        chunks = []

        # Calculate chunk positions
        chunk_num = 0
        pos = 0

        while pos < len(words):
            # Get chunk text
            chunk_end = min(pos + self.chunk_size, len(words))
            chunk_words = words[pos:chunk_end]
            chunk_text = " ".join(chunk_words)

            # Estimate page number (rough heuristic)
            page = self._estimate_page(pos, len(words), len(text_by_page))

            # Create chunk
            chunk_id = f"{document_id}_chunk_{chunk_num}"
            chunk = DocumentChunk(
                text=chunk_text,
                document_id=document_id,
                filename=filename,
                page=page,
                chunk_id=chunk_id,
                total_chunks=0,  # Will be updated later
                user_id=user_id,
                ocr_used=ocr_used,
                ocr_pages=ocr_pages,
                total_pages=total_pages
            )
            chunks.append(chunk)

            # Move to next chunk with overlap
            pos += self.chunk_size - self.chunk_overlap
            chunk_num += 1

        # Update total_chunks for all chunks
        total = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total

        return chunks

    def _estimate_page(self, word_position: int, total_words: int, total_pages: int) -> int:
        """
        Estimate which page a word position corresponds to

        Args:
            word_position: Position of word in document
            total_words: Total words in document
            total_pages: Total pages in document

        Returns:
            Estimated page number (1-indexed)
        """
        if total_words == 0:
            return 1

        # Simple linear estimation
        progress = word_position / total_words
        page = int(progress * total_pages) + 1
        return min(page, total_pages)

    def _generate_document_id(self, filename: str) -> str:
        """
        Generate unique document ID

        Args:
            filename: Original filename

        Returns:
            Hash-based document ID
        """
        # Use filename + timestamp for uniqueness
        unique_string = f"{filename}_{datetime.now().isoformat()}"
        doc_id = hashlib.md5(unique_string.encode()).hexdigest()[:12]
        return doc_id


# Global instance
document_processor: DocumentProcessor = None


def get_document_processor() -> DocumentProcessor:
    """Get the global document processor instance"""
    global document_processor
    if document_processor is None:
        document_processor = DocumentProcessor()
    return document_processor
