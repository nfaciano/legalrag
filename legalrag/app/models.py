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
