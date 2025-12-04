"""Vector database service abstraction."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import structlog

from src.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class VectorService(ABC):
    """Abstract vector database service."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector database connection."""
        pass

    @abstractmethod
    async def upsert(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadata: List[Dict[str, Any]],
    ) -> None:
        """Upsert vectors with metadata."""
        pass

    @abstractmethod
    async def query(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query similar vectors."""
        pass

    @abstractmethod
    async def delete(self, ids: List[str]) -> None:
        """Delete vectors by IDs."""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        pass


class PineconeVectorService(VectorService):
    """Pinecone vector database implementation."""

    def __init__(self):
        """Initialize Pinecone service."""
        self.api_key = settings.PINECONE_API_KEY
        self.environment = settings.PINECONE_ENVIRONMENT
        self.index_name = settings.PINECONE_INDEX_NAME
        self.client = None
        self.index = None

    async def initialize(self) -> None:
        """Initialize Pinecone connection."""
        try:
            import pinecone

            pinecone.init(api_key=self.api_key, environment=self.environment)
            self.client = pinecone
            self.index = pinecone.Index(self.index_name)
            logger.info("Pinecone initialized", index=self.index_name)
        except ImportError:
            raise ImportError("pinecone-client is not installed")
        except Exception as e:
            logger.error("Failed to initialize Pinecone", error=str(e))
            raise

    async def upsert(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadata: List[Dict[str, Any]],
    ) -> None:
        """Upsert vectors to Pinecone."""
        if not self.index:
            await self.initialize()

        vectors_to_upsert = [
            (id, vector, meta) for id, vector, meta in zip(ids, vectors, metadata)
        ]
        self.index.upsert(vectors=vectors_to_upsert)
        logger.debug("Upserted vectors", count=len(ids))

    async def query(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query Pinecone index."""
        if not self.index:
            await self.initialize()

        query_response = self.index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter,
        )

        results = []
        for match in query_response.matches:
            results.append({
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata,
            })

        return results

    async def delete(self, ids: List[str]) -> None:
        """Delete vectors from Pinecone."""
        if not self.index:
            await self.initialize()

        self.index.delete(ids=ids)
        logger.debug("Deleted vectors", count=len(ids))

    async def get_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics."""
        if not self.index:
            await self.initialize()

        stats = self.index.describe_index_stats()
        return {
            "total_vectors": stats.total_vector_count,
            "dimension": stats.dimension,
            "index_fullness": stats.index_fullness,
        }


class ChromaVectorService(VectorService):
    """ChromaDB vector database implementation (for local development)."""

    def __init__(self):
        """Initialize ChromaDB service."""
        self.persist_directory = "./chroma_db"
        self.collection_name = "lla_legal_documents"
        self.client = None
        self.collection = None

    async def initialize(self) -> None:
        """Initialize ChromaDB connection."""
        try:
            import chromadb

            self.client = chromadb.PersistentClient(path=self.persist_directory)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name
            )
            logger.info("ChromaDB initialized", collection=self.collection_name)
        except ImportError:
            raise ImportError("chromadb is not installed")
        except Exception as e:
            logger.error("Failed to initialize ChromaDB", error=str(e))
            raise

    async def upsert(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadata: List[Dict[str, Any]],
    ) -> None:
        """Upsert vectors to ChromaDB."""
        if not self.collection:
            await self.initialize()

        # Extract documents from metadata
        documents = [meta.get("text", "") for meta in metadata]

        self.collection.add(
            embeddings=vectors,
            ids=ids,
            metadatas=metadata,
            documents=documents,
        )
        logger.debug("Upserted vectors", count=len(ids))

    async def query(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query ChromaDB collection."""
        if not self.collection:
            await self.initialize()

        query_results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=filter,
        )

        results = []
        if query_results["ids"] and len(query_results["ids"][0]) > 0:
            for i, id in enumerate(query_results["ids"][0]):
                results.append({
                    "id": id,
                    "score": 1.0 - query_results["distances"][0][i] if "distances" in query_results else 0.0,
                    "metadata": query_results["metadatas"][0][i] if "metadatas" in query_results else {},
                })

        return results

    async def delete(self, ids: List[str]) -> None:
        """Delete vectors from ChromaDB."""
        if not self.collection:
            await self.initialize()

        self.collection.delete(ids=ids)
        logger.debug("Deleted vectors", count=len(ids))

    async def get_stats(self) -> Dict[str, Any]:
        """Get ChromaDB collection statistics."""
        if not self.collection:
            await self.initialize()

        count = self.collection.count()
        return {
            "total_vectors": count,
            "collection_name": self.collection_name,
        }


def get_vector_service() -> VectorService:
    """Get vector service based on configuration."""
    vector_db_type = settings.VECTOR_DB_TYPE.lower()

    if vector_db_type == "pinecone":
        return PineconeVectorService()
    elif vector_db_type == "chroma":
        return ChromaVectorService()
    else:
        logger.warning(
            "Unknown vector DB type, defaulting to ChromaDB",
            type=vector_db_type,
        )
        return ChromaVectorService()

