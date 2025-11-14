import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class VectorDatabase:
    """ChromaDB vector database manager"""

    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize ChromaDB client

        Args:
            persist_directory: Directory to persist the database
        """
        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing ChromaDB at {persist_directory}")
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="legal_documents",
            metadata={"description": "Legal document chunks with embeddings"}
        )
        logger.info(f"Collection 'legal_documents' ready. Total documents: {self.collection.count()}")

    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """
        Add documents to the vector database

        Args:
            texts: List of text chunks
            embeddings: List of embedding vectors
            metadatas: List of metadata dicts for each chunk
            ids: List of unique IDs for each chunk
        """
        logger.info(f"Adding {len(texts)} documents to database")
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Documents added. Total count: {self.collection.count()}")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        where: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Search for similar documents

        Args:
            query_embedding: Embedding vector of the query
            top_k: Number of results to return
            where: Optional filter conditions (e.g., {"user_id": "user_123"})

        Returns:
            Dictionary with results including documents, metadatas, and distances
        """
        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": top_k
        }

        if where:
            query_params["where"] = where

        results = self.collection.query(**query_params)
        return results

    def get_all_documents(self, where: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Get information about all indexed documents

        Args:
            where: Optional filter conditions (e.g., {"user_id": "user_123"})

        Returns:
            List of document metadata
        """
        # Get all items from collection
        if where:
            results = self.collection.get(where=where)
        else:
            results = self.collection.get()

        # Group by document_id to get unique documents
        documents = {}
        for metadata in results['metadatas']:
            doc_id = metadata['document_id']
            if doc_id not in documents:
                documents[doc_id] = {
                    'document_id': doc_id,
                    'filename': metadata['filename'],
                    'total_chunks': metadata['total_chunks'],
                    'upload_date': metadata.get('upload_date', 'unknown')
                }

        return list(documents.values())

    def delete_document(self, document_id: str, user_id: str = None) -> int:
        """
        Delete all chunks of a document

        Args:
            document_id: ID of document to delete
            user_id: Optional user ID to ensure only owner can delete

        Returns:
            Number of chunks deleted
        """
        # Get all IDs for this document with proper ChromaDB where syntax
        if user_id:
            where_filter = {
                "$and": [
                    {"document_id": document_id},
                    {"user_id": user_id}
                ]
            }
        else:
            where_filter = {"document_id": document_id}

        results = self.collection.get(where=where_filter)

        if not results['ids']:
            return 0

        # Delete all chunks
        self.collection.delete(ids=results['ids'])
        logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
        return len(results['ids'])

    def count(self) -> int:
        """Get total number of chunks in database"""
        return self.collection.count()


# Global instance
vector_db: VectorDatabase = None


def get_vector_db() -> VectorDatabase:
    """Get the global vector database instance"""
    global vector_db
    if vector_db is None:
        vector_db = VectorDatabase()
    return vector_db
