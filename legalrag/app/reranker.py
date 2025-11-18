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
            List of tuples (index, normalized_score) sorted by relevance score
            Scores are normalized to 0-1 range using min-max normalization
        """
        if not documents:
            return []

        # Create query-document pairs
        pairs = [[query, doc] for doc in documents]

        # Get relevance scores from cross-encoder (can be negative, typically -10 to +10)
        scores = self.model.predict(pairs)

        # Normalize scores to 0-1 range using min-max normalization
        min_score = float(min(scores))
        max_score = float(max(scores))

        if max_score == min_score:
            # All scores are the same, assign 0.5 to all
            normalized_scores = [0.5] * len(scores)
        else:
            normalized_scores = [(float(score) - min_score) / (max_score - min_score)
                                 for score in scores]

        # Create list of (original_index, normalized_score) tuples
        results = [(idx, normalized_scores[idx]) for idx in range(len(scores))]

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
