from typing import List
import logging
from app.database import get_vector_db
from app.embeddings import get_embedding_model
from app.models import SearchResult, DocumentMetadata

logger = logging.getLogger(__name__)


class SearchEngine:
    """Semantic search engine for legal documents"""

    def __init__(self, use_reranking: bool = True):  # Enabled for Railway 8GB RAM
        self.db = get_vector_db()
        self.embedder = get_embedding_model()
        self.use_reranking = use_reranking
        self.reranker = None

        if use_reranking:
            try:
                from app.reranker import get_reranker
                self.reranker = get_reranker()
                logger.info("Reranking enabled")
            except Exception as e:
                logger.warning(f"Could not load reranker: {e}. Reranking disabled.")
                self.use_reranking = False

    def search(self, query: str, top_k: int = 5, use_reranking: bool = None, user_id: str = None) -> List[SearchResult]:
        """
        Perform semantic search with optional reranking

        Args:
            query: Natural language query
            top_k: Number of results to return
            use_reranking: Override instance reranking setting (optional)
            user_id: Optional user ID to filter results

        Returns:
            List of SearchResult objects, ranked by similarity (and reranked if enabled)
        """
        # Determine if we should use reranking
        should_rerank = use_reranking if use_reranking is not None else self.use_reranking

        # Fetch more results for reranking (retrieve 2-3x, then rerank to top_k)
        retrieval_k = top_k * 3 if should_rerank and self.reranker else top_k

        logger.info(f"Searching for: '{query}' (top_k={top_k}, retrieval_k={retrieval_k}, reranking={should_rerank}, user_id={user_id})")

        # Generate query embedding
        query_embedding = self.embedder.embed_text(query)

        # Prepare filter
        where_filter = {"user_id": user_id} if user_id else None

        # Search vector database
        results = self.db.search(query_embedding, top_k=retrieval_k, where=where_filter)

        # Format initial results
        search_results = []

        if results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                text = results['documents'][0][i]
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i]

                # Convert cosine distance to similarity score
                # ChromaDB returns cosine distance where: distance = 1 - cosine_similarity
                # So: cosine_similarity = 1 - distance
                # Result range: -1 (opposite) to 1 (identical), typically 0-1 for relevant docs
                similarity = 1.0 - distance

                search_result = SearchResult(
                    text=text,
                    metadata=DocumentMetadata(**metadata),
                    similarity_score=round(similarity, 4)
                )
                search_results.append(search_result)

        # Apply reranking if enabled
        if should_rerank and self.reranker and len(search_results) > 0:
            logger.info(f"Reranking {len(search_results)} results...")

            # Extract texts for reranking
            texts = [result.text for result in search_results]

            # Get reranked indices and scores
            reranked = self.reranker.rerank(query, texts, top_k=top_k)

            # Reorder results based on reranking scores
            reranked_results = []
            for idx, rerank_score in reranked:
                result = search_results[idx]
                # Update similarity score with reranking score (normalized to 0-1)
                result.similarity_score = round(rerank_score, 4)
                reranked_results.append(result)

            search_results = reranked_results
            logger.info(f"Reranking complete, returning top {len(search_results)} results")
        else:
            # Just return top_k if no reranking
            search_results = search_results[:top_k]

        logger.info(f"Returning {len(search_results)} results")
        return search_results


# Global instance
search_engine: SearchEngine = None


def get_search_engine() -> SearchEngine:
    """Get the global search engine instance"""
    global search_engine
    if search_engine is None:
        search_engine = SearchEngine()
    return search_engine
