"""Vector indexer for legal documents."""

import uuid
from typing import List, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class VectorIndexer:
    """Index documents into vector database."""

    def __init__(self, vector_service, embedding_service):
        """
        Initialize vector indexer.

        Args:
            vector_service: Vector database service
            embedding_service: Embedding generation service
        """
        self.vector_service = vector_service
        self.embedding_service = embedding_service

    async def index_documents(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Index document chunks into vector database.

        Args:
            chunks: List of document chunks with text and metadata

        Returns:
            Number of documents indexed
        """
        logger.info("Indexing documents", chunks_count=len(chunks))

        if not chunks:
            return 0

        # Initialize vector service
        await self.vector_service.initialize()

        # Extract texts for embedding
        texts = [chunk["text"] for chunk in chunks]

        # Generate embeddings
        embeddings = self.embedding_service.encode(texts)

        # Prepare vectors for indexing
        ids = []
        vectors = []
        metadata_list = []

        for i, chunk in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            ids.append(chunk_id)
            vectors.append(embeddings[i])
            metadata = chunk.get("metadata", {}).copy()
            metadata["text"] = chunk["text"]  # Include text in metadata for retrieval
            metadata_list.append(metadata)

        # Upsert to vector database
        await self.vector_service.upsert(
            vectors=vectors,
            ids=ids,
            metadata=metadata_list,
        )

        logger.info("Documents indexed", count=len(ids))
        return len(ids)

    async def index_document(self, document: Dict[str, Any]) -> int:
        """
        Index a single document.

        Args:
            document: Document with text and metadata

        Returns:
            Number of chunks indexed
        """
        # Treat single document as list
        return await self.index_documents([document])

