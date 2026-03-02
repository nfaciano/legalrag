from fastapi import APIRouter, HTTPException, Depends
import logging

from app.models import (
    CaseCreateRequest,
    CaseInfo,
    CaseListResponse,
    PleadingGenerationRequest,
    PleadingResponse,
)
from app.auth import get_current_user
from app.case_db import create_case, get_case, list_cases, update_case, delete_case

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/cases", response_model=CaseInfo)
async def create_case_endpoint(
    request: CaseCreateRequest,
    user_id: str = Depends(get_current_user)
):
    """Create a new saved case."""
    logger.info(f"Creating case '{request.case_name}' for user {user_id}")

    try:
        case = create_case(user_id, request.model_dump())
        return CaseInfo(**case)
    except Exception as e:
        logger.error(f"Error creating case: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating case: {str(e)}")


@router.get("/cases", response_model=CaseListResponse)
async def list_cases_endpoint(user_id: str = Depends(get_current_user)):
    """List all saved cases for the authenticated user."""
    try:
        cases = list_cases(user_id)
        return CaseListResponse(
            cases=[CaseInfo(**c) for c in cases],
            total_cases=len(cases)
        )
    except Exception as e:
        logger.error(f"Error listing cases: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing cases: {str(e)}")


@router.get("/cases/{case_id}", response_model=CaseInfo)
async def get_case_endpoint(
    case_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get a specific case."""
    case = get_case(user_id, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return CaseInfo(**case)


@router.put("/cases/{case_id}", response_model=CaseInfo)
async def update_case_endpoint(
    case_id: str,
    request: CaseCreateRequest,
    user_id: str = Depends(get_current_user)
):
    """Update a saved case."""
    logger.info(f"Updating case {case_id} for user {user_id}")

    case = update_case(user_id, case_id, request.model_dump())
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return CaseInfo(**case)


@router.delete("/cases/{case_id}")
async def delete_case_endpoint(
    case_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a saved case."""
    logger.info(f"Deleting case {case_id} for user {user_id}")

    if not delete_case(user_id, case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return {"message": f"Case {case_id} deleted successfully"}


@router.post("/generate-pleading", response_model=PleadingResponse)
async def generate_pleading_endpoint(
    request: PleadingGenerationRequest,
    user_id: str = Depends(get_current_user)
):
    """Generate a court pleading document."""
    logger.info(f"Pleading generation request from user {user_id}: {request.document_title}")

    # Validate
    if not request.ai_generate_body and not request.body_paragraphs and not request.body_text:
        raise HTTPException(
            status_code=400,
            detail="Either body_text, body_paragraphs, or ai_generate_body with ai_prompt must be provided"
        )
    if request.ai_generate_body and not request.ai_prompt:
        raise HTTPException(
            status_code=400,
            detail="ai_prompt is required when ai_generate_body is True"
        )

    # Get case data
    case_data = get_case(user_id, request.case_id)
    if not case_data:
        raise HTTPException(status_code=404, detail="Case not found")

    # Get attorney info from settings
    from app.user_settings_db import get_user_settings
    settings = get_user_settings(user_id) or {}

    try:
        from app.document_generation import get_pleading_builder
        builder = get_pleading_builder()

        result = await builder.generate_pleading(
            user_id=user_id,
            case_data=case_data,
            attorney_info=settings,
            document_title=request.document_title,
            body_paragraphs=request.body_paragraphs,
            representing_party=request.representing_party,
            attorney_capacity=request.attorney_capacity,
            include_certification=request.include_certification,
            certification_date=request.certification_date,
            service_list=request.service_list,
            ai_generate_body=request.ai_generate_body,
            ai_prompt=request.ai_prompt,
            body_text=request.body_text,
            filing_method=request.filing_method,
            service_method=request.service_method,
        )

        download_url = f"/generated-documents/{result['document_id']}"

        return PleadingResponse(
            document_id=result["document_id"],
            filename=result["filename"],
            file_size=result["file_size"],
            generated_at=result["generated_at"],
            download_url=download_url,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating pleading: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating pleading: {str(e)}")
