from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
import logging
from pathlib import Path
from datetime import datetime

from app.models import (
    LetterheadUploadResponse,
    LetterheadInfo,
    LetterheadListResponse,
    DocumentGenerationRequest,
    GeneratedDocumentResponse,
    GeneratedDocumentInfo,
    GeneratedDocumentListResponse,
    EnvelopeGenerationRequest,
    EnvelopeResponse,
)
from app.auth import get_current_user
from app.document_generation import (
    get_template_manager,
    get_document_builder,
    get_envelope_builder,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Template endpoints ---

@router.post("/templates", response_model=LetterheadUploadResponse)
async def upload_template(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    """Upload a Word document template for document generation."""
    logger.info(f"Template upload request: {file.filename} from user: {user_id}")

    if not file.filename.endswith('.docx'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .docx files are supported"
        )

    try:
        file_content = await file.read()

        template_manager = get_template_manager()
        template_data = template_manager.save_template(
            user_id=user_id,
            filename=file.filename,
            file_content=file_content
        )

        logger.info(f"Saved template {template_data['template_id']} for user {user_id}")

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


@router.get("/templates", response_model=LetterheadListResponse)
async def list_templates(user_id: str = Depends(get_current_user)):
    """List all templates for the authenticated user."""
    try:
        template_manager = get_template_manager()
        templates_data = template_manager.list_templates(user_id)

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


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a template."""
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


# --- Document generation endpoints ---

@router.post("/generate-document", response_model=GeneratedDocumentResponse)
async def generate_document(
    request: DocumentGenerationRequest,
    user_id: str = Depends(get_current_user)
):
    """Generate a formatted document from template."""
    logger.info(f"Document generation request from user {user_id}: {request.document_type}")

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

        fields = {
            'date': request.date,
            'recipient_name': request.recipient_name,
            'recipient_company': request.recipient_company or '',
            'recipient_address': request.recipient_address,
            'subject': request.subject or '',
            'salutation': request.salutation,
            'body': request.body_text or '',
            'closing': request.closing,
            'signature_name': request.signature_name,
            'initials': request.initials,
            'enclosures': request.enclosures or ''
        }

        doc_data = await document_builder.generate_from_template(
            user_id=user_id,
            template_id=request.letterhead_id,
            fields=fields,
            ai_generate_body=request.ai_generate_body,
            ai_prompt=request.ai_prompt,
            output_format="docx"
        )

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


@router.post("/generate-envelope", response_model=EnvelopeResponse)
async def generate_envelope(
    request: EnvelopeGenerationRequest,
    user_id: str = Depends(get_current_user)
):
    """Generate a print-ready envelope document."""
    logger.info(f"Envelope generation request from user {user_id}")

    if not request.ai_prompt and not request.recipient:
        raise HTTPException(
            status_code=400,
            detail="Either ai_prompt or recipient address must be provided"
        )

    try:
        envelope_builder = get_envelope_builder()

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

        envelope_data = await envelope_builder.generate_envelope(
            user_id=user_id,
            return_address=return_addr,
            recipient_data=recipient_data,
            ai_prompt=request.ai_prompt
        )

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


# --- Generated document management endpoints ---

@router.get("/generated-documents")
async def list_generated_documents(user_id: str = Depends(get_current_user)):
    """List all generated documents for the authenticated user."""
    try:
        user_output_dir = Path("./data/uploads/generated") / user_id

        if not user_output_dir.exists():
            return GeneratedDocumentListResponse(documents=[], total_documents=0)

        documents = []
        for file_path in list(user_output_dir.glob("*.pdf")) + list(user_output_dir.glob("*.docx")):
            stat = file_path.stat()
            doc_id = file_path.stem.split('_')[0]

            documents.append(GeneratedDocumentInfo(
                document_id=doc_id,
                filename=file_path.name,
                file_size=stat.st_size,
                generated_at=datetime.fromtimestamp(stat.st_mtime).isoformat()
            ))

        documents.sort(key=lambda x: x.generated_at, reverse=True)

        logger.info(f"User {user_id} has {len(documents)} generated documents")

        return GeneratedDocumentListResponse(
            documents=documents,
            total_documents=len(documents)
        )

    except Exception as e:
        logger.error(f"Error listing generated documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing generated documents: {str(e)}")


@router.get("/generated-documents/{document_id}")
async def download_generated_document(
    document_id: str,
    user_id: str = Depends(get_current_user)
):
    """Download a generated document."""
    logger.info(f"Download request for document {document_id} from user {user_id}")

    try:
        user_output_dir = Path("./data/uploads/generated") / user_id

        matching_files = list(user_output_dir.glob(f"*{document_id}*.pdf")) + \
                        list(user_output_dir.glob(f"*{document_id}*.docx"))

        if not matching_files:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )

        file_path = matching_files[0]

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


@router.delete("/generated-documents/{document_id}")
async def delete_generated_document(
    document_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a generated document."""
    try:
        output_dir = Path("./data/uploads/generated") / user_id
        if not output_dir.exists():
            raise HTTPException(status_code=404, detail="No documents found")

        files = list(output_dir.glob(f"{document_id}_*"))

        if not files:
            raise HTTPException(status_code=404, detail="Document not found")

        file_path = files[0]
        file_path.unlink()

        logger.info(f"Deleted document {document_id} for user {user_id}: {file_path.name}")
        return {"message": "Document deleted successfully", "document_id": document_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


@router.delete("/generated-documents")
async def delete_all_generated_documents(
    user_id: str = Depends(get_current_user)
):
    """Delete all generated documents for the authenticated user."""
    try:
        output_dir = Path("./data/uploads/generated") / user_id
        if not output_dir.exists():
            return {"message": "No documents to delete", "deleted_count": 0}

        files = list(output_dir.glob("*"))
        deleted_count = 0

        for file_path in files:
            if file_path.is_file():
                file_path.unlink()
                deleted_count += 1

        logger.info(f"Bulk deleted {deleted_count} documents for user {user_id}")
        return {"message": f"Successfully deleted {deleted_count} document(s)", "deleted_count": deleted_count}

    except Exception as e:
        logger.error(f"Error bulk deleting documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting documents: {str(e)}")
