from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import logging
import os
import shutil
import re
from pathlib import Path
from typing import List
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.models import (
    SearchRequest,
    SearchResponse,
    UploadResponse,
    DocumentListResponse,
    DocumentInfo,
    SearchResult,
    LetterheadUploadResponse,
    LetterheadInfo,
    LetterheadListResponse,
    DocumentGenerationRequest,
    GeneratedDocumentResponse,
    GeneratedDocumentInfo,
    GeneratedDocumentListResponse,
    EnvelopeGenerationRequest,
    EnvelopeResponse,
    UserSettings,
    UserSettingsResponse
)
from app.database import get_vector_db
from app.embeddings import get_embedding_model
from app.document_processor import get_document_processor
from app.search import get_search_engine
from app.auth import get_current_user
from app.document_generation import (
    get_template_manager,
    get_document_builder,
    get_envelope_builder
)
from app.user_settings_db import get_user_settings, save_user_settings

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
            "delete_document": "DELETE /documents/{document_id}",
            "upload_template": "POST /templates",
            "list_templates": "GET /templates",
            "generate_document": "POST /generate-document"
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

    # Sanitize filename to prevent path traversal attacks
    safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
    if not safe_filename or safe_filename.startswith('.'):
        safe_filename = f"document_{user_id[:8]}.pdf"

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

        # Save uploaded file with sanitized name
        file_path = UPLOAD_DIR / safe_filename
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

        logger.info(f"Saved file to {file_path} ({len(file_content) / 1024 / 1024:.1f}MB)")

        # Process document
        processor = get_document_processor()
        chunks = processor.process_pdf(str(file_path), safe_filename, user_id)

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


@app.get("/documents/{document_id}/text")
async def get_document_text(
    document_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get all extracted text for a document (useful for verifying OCR quality)

    Args:
        document_id: ID of document to retrieve text for
        user_id: Authenticated user ID (injected by dependency)

    Returns:
        Document text organized by chunks with metadata
    """
    logger.info(f"Text retrieval request for document: {document_id} from user: {user_id}")

    try:
        db = get_vector_db()

        # Get all chunks for this document (filtered by user_id for security)
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

        # Organize chunks
        chunks = []
        for i, (chunk_id, metadata) in enumerate(zip(results['ids'], results['metadatas'])):
            chunks.append({
                "chunk_id": chunk_id,
                "text": results['documents'][i] if results['documents'] else "",
                "page": metadata.get('page', 0),
                "chunk_index": int(chunk_id.split('_chunk_')[-1]) if '_chunk_' in chunk_id else i
            })

        # Sort by chunk index to maintain order
        chunks.sort(key=lambda x: x['chunk_index'])

        # Get document metadata from first chunk
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


# Document Generation Endpoints

@app.post("/templates", response_model=LetterheadUploadResponse)
async def upload_template(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    """
    Upload a Word document template for document generation

    Args:
        file: Word document file (.docx)
        user_id: Authenticated user ID (injected by dependency)

    Returns:
        LetterheadUploadResponse with template ID and metadata (reusing model for now)
    """
    logger.info(f"Template upload request: {file.filename} from user: {user_id}")

    # Validate file type
    if not file.filename.endswith('.docx'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .docx files are supported"
        )

    try:
        # Read file content
        file_content = await file.read()

        # Save template
        template_manager = get_template_manager()
        template_data = template_manager.save_template(
            user_id=user_id,
            filename=file.filename,
            file_content=file_content
        )

        logger.info(f"Saved template {template_data['template_id']} for user {user_id}")

        # Return using letterhead response model (compatible structure)
        return LetterheadUploadResponse(
            letterhead_id=template_data['template_id'],
            original_filename=template_data['original_filename'],
            file_size=template_data['file_size'],
            upload_date=template_data['upload_date']
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading template: {str(e)}")


@app.get("/templates", response_model=LetterheadListResponse)
async def list_templates(user_id: str = Depends(get_current_user)):
    """
    List all templates for the authenticated user

    Args:
        user_id: Authenticated user ID (injected by dependency)

    Returns:
        LetterheadListResponse with all template metadata (reusing model)
    """
    try:
        template_manager = get_template_manager()
        templates_data = template_manager.list_templates(user_id)

        # Convert to letterhead info format (compatible)
        letterheads = [LetterheadInfo(
            letterhead_id=tpl['template_id'],
            original_filename=tpl['original_filename'],
            file_size=tpl['file_size'],
            upload_date=tpl['upload_date']
        ) for tpl in templates_data]

        logger.info(f"User {user_id} has {len(letterheads)} templates")

        return LetterheadListResponse(
            letterheads=letterheads,
            total_letterheads=len(letterheads)
        )

    except Exception as e:
        logger.error(f"Error listing templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing templates: {str(e)}")


@app.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Delete a template

    Args:
        template_id: ID of template to delete
        user_id: Authenticated user ID (injected by dependency)

    Returns:
        Success message
    """
    logger.info(f"Delete template request: {template_id} from user: {user_id}")

    try:
        template_manager = get_template_manager()
        success = template_manager.delete_template(user_id, template_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Template {template_id} not found"
            )

        return {"message": f"Successfully deleted template {template_id}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting template: {str(e)}")


@app.post("/generate-document", response_model=GeneratedDocumentResponse)
async def generate_document(
    request: DocumentGenerationRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Generate a formatted document from template

    Args:
        request: DocumentGenerationRequest with all document details
        user_id: Authenticated user ID (injected by dependency)

    Returns:
        GeneratedDocumentResponse with download URL
    """
    logger.info(f"Document generation request from user {user_id}: {request.document_type}")

    # Validate that body_text or ai_prompt is provided
    if not request.ai_generate_body and not request.body_text:
        raise HTTPException(
            status_code=400,
            detail="Either body_text or ai_generate_body with ai_prompt must be provided"
        )

    if request.ai_generate_body and not request.ai_prompt:
        raise HTTPException(
            status_code=400,
            detail="ai_prompt is required when ai_generate_body is True"
        )

    try:
        document_builder = get_document_builder()

        # Build fields dict for template placeholders
        fields = {
            'date': request.date,
            'recipient_name': request.recipient_name,
            'recipient_company': request.recipient_company or '',
            'recipient_address': request.recipient_address,
            'subject': request.subject or '',
            'salutation': request.salutation,
            'body': request.body_text or '',  # Will be replaced by AI if requested
            'closing': request.closing,
            'signature_name': request.signature_name,
            'initials': request.initials,
            'enclosures': request.enclosures or ''
        }

        # Generate document
        doc_data = await document_builder.generate_from_template(
            user_id=user_id,
            template_id=request.letterhead_id,  # letterhead_id is now template_id
            fields=fields,
            ai_generate_body=request.ai_generate_body,
            ai_prompt=request.ai_prompt,
            output_format="docx"  # Can be made configurable later
        )

        # Create download URL
        download_url = f"/generated-documents/{doc_data['document_id']}"

        logger.info(f"Generated document {doc_data['document_id']} for user {user_id}")

        return GeneratedDocumentResponse(
            document_id=doc_data['document_id'],
            filename=doc_data['filename'],
            file_size=doc_data['file_size'],
            generated_at=doc_data['generated_at'],
            download_url=download_url
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating document: {str(e)}")


@app.post("/generate-envelope", response_model=EnvelopeResponse)
async def generate_envelope(
    request: EnvelopeGenerationRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Generate a print-ready envelope document

    Args:
        request: EnvelopeGenerationRequest with return address and recipient
        user_id: Authenticated user ID (injected by dependency)

    Returns:
        EnvelopeResponse with download URL
    """
    logger.info(f"Envelope generation request from user {user_id}")

    # Validate that either ai_prompt or recipient is provided
    if not request.ai_prompt and not request.recipient:
        raise HTTPException(
            status_code=400,
            detail="Either ai_prompt or recipient address must be provided"
        )

    try:
        envelope_builder = get_envelope_builder()

        # Convert Pydantic models to dicts
        return_addr = {
            'name': request.return_address.name,
            'line1': request.return_address.line1,
            'line2': request.return_address.line2 or '',
            'city_state_zip': request.return_address.city_state_zip
        }

        recipient_data = None
        if request.recipient:
            recipient_data = {
                'name': request.recipient.name,
                'line1': request.recipient.line1,
                'line2': request.recipient.line2 or '',
                'city_state_zip': request.recipient.city_state_zip
            }

        # Generate envelope
        envelope_data = await envelope_builder.generate_envelope(
            user_id=user_id,
            return_address=return_addr,
            recipient_data=recipient_data,
            ai_prompt=request.ai_prompt
        )

        # Create download URL
        download_url = f"/generated-documents/{envelope_data['envelope_id']}"

        logger.info(f"Generated envelope {envelope_data['envelope_id']} for user {user_id}")

        return EnvelopeResponse(
            envelope_id=envelope_data['envelope_id'],
            filename=envelope_data['filename'],
            file_size=envelope_data['file_size'],
            generated_at=envelope_data['generated_at'],
            download_url=download_url
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating envelope: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating envelope: {str(e)}")


@app.get("/generated-documents")
async def list_generated_documents(user_id: str = Depends(get_current_user)):
    """
    List all generated documents for the authenticated user

    Args:
        user_id: Authenticated user ID (injected by dependency)

    Returns:
        List of generated document metadata
    """
    try:
        # List files in user's generated documents directory
        user_output_dir = Path("./uploads/generated") / user_id

        if not user_output_dir.exists():
            return GeneratedDocumentListResponse(documents=[], total_documents=0)

        documents = []
        # Look for both .docx and .pdf files
        for file_path in list(user_output_dir.glob("*.pdf")) + list(user_output_dir.glob("*.docx")):
            stat = file_path.stat()
            doc_id = file_path.stem.split('_')[0]  # Extract doc_id from filename

            documents.append(GeneratedDocumentInfo(
                document_id=doc_id,
                filename=file_path.name,
                file_size=stat.st_size,
                generated_at=datetime.fromtimestamp(stat.st_mtime).isoformat()
            ))

        # Sort by generated date (newest first)
        documents.sort(key=lambda x: x.generated_at, reverse=True)

        logger.info(f"User {user_id} has {len(documents)} generated documents")

        return GeneratedDocumentListResponse(
            documents=documents,
            total_documents=len(documents)
        )

    except Exception as e:
        logger.error(f"Error listing generated documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing generated documents: {str(e)}")


@app.get("/generated-documents/{document_id}")
async def download_generated_document(
    document_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Download a generated document

    Args:
        document_id: ID of document to download
        user_id: Authenticated user ID (injected by dependency)

    Returns:
        PDF file download
    """
    logger.info(f"Download request for document {document_id} from user {user_id}")

    try:
        # Find file in user's directory
        user_output_dir = Path("./uploads/generated") / user_id

        # Find file that contains document_id (could be .pdf or .docx)
        matching_files = list(user_output_dir.glob(f"*{document_id}*.pdf")) + \
                        list(user_output_dir.glob(f"*{document_id}*.docx"))

        if not matching_files:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )

        file_path = matching_files[0]

        # Determine media type based on extension
        media_type = "application/pdf" if file_path.suffix == ".pdf" else \
                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=file_path.name,
            headers={
                "Content-Disposition": f'attachment; filename="{file_path.name}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error downloading document: {str(e)}")


@app.delete("/generated-documents/{document_id}")
async def delete_generated_document(
    document_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a generated document for the authenticated user"""
    try:
        # Find and delete the file
        output_dir = Path("uploads/generated") / user_id
        if not output_dir.exists():
            raise HTTPException(status_code=404, detail="No documents found")

        # Find file matching the document_id prefix
        files = list(output_dir.glob(f"{document_id}_*"))

        if not files:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete the file
        file_path = files[0]
        file_path.unlink()

        logger.info(f"Deleted document {document_id} for user {user_id}: {file_path.name}")
        return {"message": "Document deleted successfully", "document_id": document_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


@app.delete("/generated-documents")
async def delete_all_generated_documents(
    user_id: str = Depends(get_current_user)
):
    """Delete all generated documents for the authenticated user"""
    try:
        # Find user's output directory
        output_dir = Path("uploads/generated") / user_id
        if not output_dir.exists():
            return {"message": "No documents to delete", "deleted_count": 0}

        # Get all files in the directory
        files = list(output_dir.glob("*"))
        deleted_count = 0

        # Delete all files
        for file_path in files:
            if file_path.is_file():
                file_path.unlink()
                deleted_count += 1

        logger.info(f"Bulk deleted {deleted_count} documents for user {user_id}")
        return {"message": f"Successfully deleted {deleted_count} document(s)", "deleted_count": deleted_count}

    except Exception as e:
        logger.error(f"Error bulk deleting documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting documents: {str(e)}")


@app.get("/user-settings", response_model=UserSettingsResponse)
async def get_user_settings_endpoint(
    user_id: str = Depends(get_current_user)
):
    """
    Get user settings (return address, signature, etc.)

    Args:
        user_id: Authenticated user ID (injected by dependency)

    Returns:
        User settings or default values
    """
    logger.info(f"Getting settings for user {user_id}")

    try:
        settings = get_user_settings(user_id)

        # If no settings found, return defaults
        if not settings:
            settings = {
                "return_address_name": "",
                "return_address_line1": "",
                "return_address_line2": "",
                "return_address_city_state_zip": "",
                "signature_name": "",
                "initials": "",
                "closing": "Very truly yours,"
            }

        return UserSettingsResponse(settings=UserSettings(**settings))

    except Exception as e:
        logger.error(f"Error getting user settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting settings: {str(e)}")


@app.put("/user-settings", response_model=UserSettingsResponse)
async def update_user_settings_endpoint(
    settings: UserSettings,
    user_id: str = Depends(get_current_user)
):
    """
    Update user settings

    Args:
        settings: New settings to save
        user_id: Authenticated user ID (injected by dependency)

    Returns:
        Updated settings
    """
    logger.info(f"Updating settings for user {user_id}")

    try:
        # Convert Pydantic model to dict
        settings_dict = settings.model_dump()

        # Save to database
        saved_settings = save_user_settings(user_id, settings_dict)

        return UserSettingsResponse(settings=UserSettings(**saved_settings))

    except Exception as e:
        logger.error(f"Error updating user settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating settings: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
