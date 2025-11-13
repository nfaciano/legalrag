from sentence_transformers import CrossEncoder
from typing import List
import logging

logger = logging.getLogger(__name__)


class Reranker:
    """Reranks search results using a cross-encoder model"""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize the reranker

        Args:
            model_name: HuggingFace cross-encoder model name
        """
        logger.info(f"Loading reranker model: {model_name}")
        self.model = CrossEncoder(model_name)
        logger.info("Reranker model loaded successfully")

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = None
    ) -> List[tuple]:
        """
        Rerank documents based on query relevance

        Args:
            query: Search query
            documents: List of document texts to rerank
            top_k: Number of top results to return (None = return all)

        Returns:
            List of tuples (index, score) sorted by relevance score
        """
        if not documents:
            return []

        # Create query-document pairs
        pairs = [[query, doc] for doc in documents]

        # Get relevance scores from cross-encoder
        scores = self.model.predict(pairs)

        # Create list of (original_index, score) tuples
        results = [(idx, float(score)) for idx, score in enumerate(scores)]

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)

        # Return top_k if specified
        if top_k is not None:
            results = results[:top_k]

        logger.info(f"Reranked {len(documents)} documents, returning top {len(results)}")
        return results


# Global instance
reranker: Reranker = None


def get_reranker() -> Reranker:
    """Get the global reranker instance"""
    global reranker
    if reranker is None:
        reranker = Reranker()
    return reranker
