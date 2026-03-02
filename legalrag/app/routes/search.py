from fastapi import APIRouter, HTTPException, Depends
import logging

from app.models import SearchRequest, SearchResponse
from app.search import get_search_engine
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    user_id: str = Depends(get_current_user)
):
    """Perform semantic search over indexed documents with optional answer synthesis."""
    logger.info(f"Search request from user {user_id}: '{request.query}' (top_k={request.top_k}, synthesis={request.synthesize_answer})")

    try:
        search_engine = get_search_engine()
        results = search_engine.search(
            request.query,
            top_k=request.top_k,
            use_reranking=request.use_reranking,
            user_id=user_id
        )

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
