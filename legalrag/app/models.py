from pydantic import BaseModel
from typing import List, Optional


class DocumentMetadata(BaseModel):
    """Metadata for a document chunk"""
    document_id: str
    filename: str
    page: int
    chunk_id: str
    total_chunks: int


class SearchResult(BaseModel):
    """Result from semantic search"""
    text: str
    metadata: DocumentMetadata
    similarity_score: float


class SearchRequest(BaseModel):
    """Request body for search endpoint"""
    query: str
    top_k: int = 5
    use_reranking: bool = True
    synthesize_answer: bool = False


class SearchResponse(BaseModel):
    """Response from search endpoint"""
    query: str
    results: List[SearchResult]
    total_results: int
    synthesized_answer: Optional[str] = None


class UploadResponse(BaseModel):
    """Response after document upload"""
    document_id: str
    filename: str
    total_chunks: int
    message: str
    ocr_used: bool = False
    ocr_pages: int = 0
    total_pages: int = 0


class DocumentInfo(BaseModel):
    """Information about an indexed document"""
    document_id: str
    filename: str
    total_chunks: int
    upload_date: str
    ocr_used: bool = False
    ocr_pages: int = 0
    total_pages: int = 0


class DocumentListResponse(BaseModel):
    """Response listing all documents"""
    documents: List[DocumentInfo]
    total_documents: int


# Document Generation Models

class LetterheadUploadResponse(BaseModel):
    """Response after letterhead upload"""
    letterhead_id: str
    original_filename: str
    file_size: int
    upload_date: str


class LetterheadInfo(BaseModel):
    """Information about a letterhead"""
    letterhead_id: str
    original_filename: str
    file_size: int
    upload_date: str


class LetterheadListResponse(BaseModel):
    """Response listing all letterheads"""
    letterheads: List[LetterheadInfo]
    total_letterheads: int


class DocumentGenerationRequest(BaseModel):
    """Request to generate a document"""
    letterhead_id: Optional[str] = None
    document_type: str = "letter"  # letter, envelope, report

    # Letter fields
    date: str
    recipient_name: str
    recipient_company: Optional[str] = None
    recipient_address: str
    subject: Optional[str] = None
    salutation: str
    body_text: Optional[str] = None  # Required if not using AI
    closing: str = "Very truly yours,"
    signature_name: str
    initials: str
    enclosures: Optional[str] = None

    # AI generation fields
    ai_generate_body: bool = False
    ai_prompt: Optional[str] = None


class GeneratedDocumentResponse(BaseModel):
    """Response after document generation"""
    document_id: str
    filename: str
    file_size: int
    generated_at: str
    download_url: str


class GeneratedDocumentInfo(BaseModel):
    """Information about a generated document"""
    document_id: str
    filename: str
    file_size: int
    generated_at: str


class GeneratedDocumentListResponse(BaseModel):
    """Response listing all generated documents"""
    documents: List[GeneratedDocumentInfo]
    total_documents: int


# ============================================================================
# Envelope Generation Models
# ============================================================================

class ReturnAddress(BaseModel):
    """Return address for envelopes"""
    name: str
    line1: str
    line2: Optional[str] = ""
    city_state_zip: str


class RecipientAddress(BaseModel):
    """Recipient address for envelopes"""
    name: str
    line1: str
    line2: Optional[str] = ""
    city_state_zip: str


class EnvelopeGenerationRequest(BaseModel):
    """Request to generate an envelope"""
    # Return address (from user settings)
    return_address: ReturnAddress

    # Recipient (either AI prompt OR structured data)
    ai_prompt: Optional[str] = None
    recipient: Optional[RecipientAddress] = None


class EnvelopeResponse(BaseModel):
    """Response after envelope generation"""
    envelope_id: str
    filename: str
    file_size: int
    generated_at: str
    download_url: str


class UserSettings(BaseModel):
    """User settings for envelopes and documents"""
    return_address_name: str = ""
    return_address_line1: str = ""
    return_address_line2: str = ""
    return_address_city_state_zip: str = ""
    signature_name: str = ""
    initials: str = ""
    closing: str = "Very truly yours,"


class UserSettingsResponse(BaseModel):
    """Response containing user settings"""
    settings: UserSettings
