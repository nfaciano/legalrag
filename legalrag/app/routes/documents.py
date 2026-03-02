from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import logging
import re
from pathlib import Path

from app.models import (
    UploadResponse,
    DocumentListResponse,
    DocumentInfo,
)
from app.database import get_vector_db
from app.embeddings import get_embedding_model
from app.document_processor import get_document_processor
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = Path("./data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    """Upload and index a PDF document."""
    logger.info(f"Received upload request: {file.filename} from user: {user_id}")

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
    if not safe_filename or safe_filename.startswith('.'):
        safe_filename = f"document_{user_id[:8]}.pdf"

    MAX_FILE_SIZE = 100 * 1024 * 1024

    try:
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is 100MB, got {len(file_content) / 1024 / 1024:.1f}MB"
            )

        if not file_content.startswith(b'%PDF'):
            raise HTTPException(status_code=400, detail="Invalid PDF file")

        file_path = UPLOAD_DIR / safe_filename
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

        logger.info(f"Saved file to {file_path} ({len(file_content) / 1024 / 1024:.1f}MB)")

        processor = get_document_processor()
        chunks = processor.process_pdf(str(file_path), safe_filename, user_id)

        if not chunks:
            raise HTTPException(status_code=400, detail="No text extracted from PDF")

        embedder = get_embedding_model()
        texts = [chunk.text for chunk in chunks]
        embeddings = embedder.embed_batch(texts)

        db = get_vector_db()
        db.add_documents(
            texts=texts,
            embeddings=embeddings,
            metadatas=[chunk.to_metadata() for chunk in chunks],
            ids=[chunk.chunk_id for chunk in chunks]
        )

        document_id = chunks[0].document_id
        ocr_used = chunks[0].ocr_used
        ocr_pages = chunks[0].ocr_pages
        total_pages = chunks[0].total_pages

        logger.info(f"Successfully indexed document {document_id}")

        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            total_chunks=len(chunks),
            message=f"Successfully indexed {file.filename} into {len(chunks)} chunks",
            ocr_used=ocr_used,
            ocr_pages=ocr_pages,
            total_pages=total_pages
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(user_id: str = Depends(get_current_user)):
    """List all indexed documents for the authenticated user."""
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


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a document and all its chunks."""
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


@router.get("/documents/{document_id}/text")
async def get_document_text(
    document_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get all extracted text for a document."""
    logger.info(f"Text retrieval request for document: {document_id} from user: {user_id}")

    try:
        db = get_vector_db()

        results = db.collection.get(
            where={
                "$and": [
                    {"document_id": {"$eq": document_id}},
                    {"user_id": {"$eq": user_id}}
                ]
            }
        )

        if not results['ids']:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found or you don't have permission to view it"
            )

        chunks = []
        for i, (chunk_id, metadata) in enumerate(zip(results['ids'], results['metadatas'])):
            chunks.append({
                "chunk_id": chunk_id,
                "text": results['documents'][i] if results['documents'] else "",
                "page": metadata.get('page', 0),
                "chunk_index": int(chunk_id.split('_chunk_')[-1]) if '_chunk_' in chunk_id else i
            })

        chunks.sort(key=lambda x: x['chunk_index'])

        first_metadata = results['metadatas'][0]

        return {
            "document_id": document_id,
            "filename": first_metadata.get('filename', 'unknown'),
            "total_chunks": len(chunks),
            "ocr_used": first_metadata.get('ocr_used', False),
            "ocr_pages": first_metadata.get('ocr_pages', 0),
            "total_pages": first_metadata.get('total_pages', 0),
            "chunks": chunks,
            "full_text": "\n\n---\n\n".join([chunk['text'] for chunk in chunks])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document text: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving document text: {str(e)}")
