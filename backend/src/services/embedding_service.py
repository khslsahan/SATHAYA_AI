"""Embedding service for generating text embeddings."""

import structlog
from sentence_transformers import SentenceTransformer
from typing import List

from src.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class EmbeddingService:
    """Service for generating embeddings using sentence transformers."""

    def __init__(self):
        """Initialize embedding model."""
        self.model_name = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self.model: SentenceTransformer | None = None
        logger.info("Initializing embedding service", model=self.model_name)

    def _load_model(self):
        """Lazy load the embedding model."""
        if self.model is None:
            logger.info("Loading embedding model", model=self.model_name)
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")

    def encode(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Encode texts into embeddings.

        Args:
            texts: List of texts to encode
            batch_size: Batch size for encoding

        Returns:
            List of embedding vectors
        """
        self._load_model()
        if not texts:
            return []

        logger.debug("Encoding texts", count=len(texts), batch_size=batch_size)
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    def encode_single(self, text: str) -> List[float]:
        """
        Encode a single text into an embedding.

        Args:
            text: Text to encode

        Returns:
            Embedding vector
        """
        return self.encode([text])[0]

    @property
    def embedding_dimension(self) -> int:
        """Get the embedding dimension."""
        return self.dimension


# Singleton instance
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

