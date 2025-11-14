from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import shutil
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.models import (
    SearchRequest,
    SearchResponse,
    UploadResponse,
    DocumentListResponse,
    DocumentInfo,
    SearchResult
)
from app.database import get_vector_db
from app.embeddings import get_embedding_model
from app.document_processor import get_document_processor
from app.search import get_search_engine
from app.auth import get_current_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LegalRAG API",
    description="Semantic search over legal documents using RAG",
    version="1.0.0"
)

# Configure CORS
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

# Add production frontend URL from environment
frontend_url = os.environ.get("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)
    # Also add without trailing slash
    allowed_origins.append(frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory exists
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """Initialize models and database on startup"""
    logger.info("Starting up LegalRAG API...")

    # Initialize singletons
    logger.info("Loading embedding model...")
    get_embedding_model()

    logger.info("Initializing vector database...")
    get_vector_db()

    logger.info("Initializing document processor...")
    get_document_processor()

    logger.info("Startup complete!")


@app.get("/")
async def root():
    """Health check and API info"""
    db = get_vector_db()
    return {
        "message": "LegalRAG API is running",
        "version": "1.0.0",
        "total_chunks": db.count(),
        "endpoints": {
            "upload": "POST /upload",
            "search": "POST /search",
            "list_documents": "GET /documents",
            "delete_document": "DELETE /documents/{document_id}"
        }
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    """
    Upload and index a PDF document

    Args:
        file: PDF file to upload
        user_id: Authenticated user ID (injected by dependency)

    Returns:
        UploadResponse with document ID and metadata
    """
    logger.info(f"Received upload request: {file.filename} from user: {user_id}")

    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Validate file size (100MB limit)
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB in bytes

    try:
        # Read file content to check size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is 100MB, got {len(file_content) / 1024 / 1024:.1f}MB"
            )

        # Validate it's actually a PDF (check magic bytes)
        if not file_content.startswith(b'%PDF'):
            raise HTTPException(status_code=400, detail="Invalid PDF file")

        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

        logger.info(f"Saved file to {file_path} ({len(file_content) / 1024 / 1024:.1f}MB)")

        # Process document
        processor = get_document_processor()
        chunks = processor.process_pdf(str(file_path), file.filename, user_id)

        if not chunks:
            raise HTTPException(status_code=400, detail="No text extracted from PDF")

        # Generate embeddings
        embedder = get_embedding_model()
        texts = [chunk.text for chunk in chunks]
        embeddings = embedder.embed_batch(texts)

        # Store in vector database
        db = get_vector_db()
        db.add_documents(
            texts=texts,
            embeddings=embeddings,
            metadatas=[chunk.to_metadata() for chunk in chunks],
            ids=[chunk.chunk_id for chunk in chunks]
        )

        # Clean up uploaded file (optional - keep for debugging)
        # os.remove(file_path)

        document_id = chunks[0].document_id

        logger.info(f"Successfully indexed document {document_id}")

        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            total_chunks=len(chunks),
            message=f"Successfully indexed {file.filename} into {len(chunks)} chunks"
        )

    except Exception as e:
        logger.error(f"Error processing upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Perform semantic search over indexed documents with optional reranking and answer synthesis

    Args:
        request: SearchRequest with query, top_k, use_reranking, and synthesize_answer flags
        user_id: Authenticated user ID (injected by dependency)

    Returns:
        SearchResponse with ranked results and optional synthesized answer
    """
    logger.info(f"Search request from user {user_id}: '{request.query}' (top_k={request.top_k}, reranking={request.use_reranking}, synthesis={request.synthesize_answer})")

    try:
        # Perform search with optional reranking
        search_engine = get_search_engine()
        results = search_engine.search(
            request.query,
            top_k=request.top_k,
            use_reranking=request.use_reranking,
            user_id=user_id
        )

        # Optionally synthesize answer
        synthesized_answer = None
        if request.synthesize_answer and results:
            from app.synthesis import get_synthesizer
            synthesizer = get_synthesizer()
            synthesized_answer = synthesizer.synthesize(request.query, results)

        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            synthesized_answer=synthesized_answer
        )

    except Exception as e:
        logger.error(f"Error during search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error performing search: {str(e)}")


@app.get("/documents", response_model=DocumentListResponse)
async def list_documents(user_id: str = Depends(get_current_user)):
    """
    List all indexed documents for the authenticated user

    Args:
        user_id: Authenticated user ID (injected by dependency)

    Returns:
        DocumentListResponse with all document metadata for this user
    """
    try:
        db = get_vector_db()
        documents_data = db.get_all_documents(where={"user_id": user_id})

        documents = [DocumentInfo(**doc) for doc in documents_data]

        logger.info(f"User {user_id} has {len(documents)} documents")

        return DocumentListResponse(
            documents=documents,
            total_documents=len(documents)
        )

    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Delete a document and all its chunks (user can only delete their own documents)

    Args:
        document_id: ID of document to delete
        user_id: Authenticated user ID (injected by dependency)

    Returns:
        Success message with number of chunks deleted
    """
    logger.info(f"Delete request for document: {document_id} from user: {user_id}")

    try:
        db = get_vector_db()
        chunks_deleted = db.delete_document(document_id, user_id=user_id)

        if chunks_deleted == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found or you don't have permission to delete it"
            )

        return {
            "message": f"Successfully deleted document {document_id}",
            "chunks_deleted": chunks_deleted
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
