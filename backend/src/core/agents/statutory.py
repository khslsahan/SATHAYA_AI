"""Statutory Agent for retrieving Acts and Ordinances."""

from typing import List, Dict, Any
import structlog

from src.services.llm_service import get_llm_service
from src.services.vector_service import get_vector_service
from src.services.embedding_service import get_embedding_service
from src.core.prompts.statutory_prompt import STATUTORY_SYSTEM_PROMPT

logger = structlog.get_logger(__name__)


class StatutoryAgent:
    """Agent specialized for retrieving exact sections from Acts and Ordinances."""

    def __init__(self):
        """Initialize Statutory Agent."""
        self.llm_service = get_llm_service()
        self.vector_service = get_vector_service()
        self.embedding_service = get_embedding_service()
        self.system_prompt = STATUTORY_SYSTEM_PROMPT

    async def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Search for relevant statutory provisions.

        Args:
            query: Search query
            top_k: Number of results to retrieve

        Returns:
            Answer with citations and sources
        """
        logger.info("Statutory agent searching", query=query[:100])

        try:
            # Initialize vector service if needed
            await self.vector_service.initialize()

            # Generate query embedding
            query_embedding = self.embedding_service.encode_single(query)

            # Search vector database with filter for statutory documents
            filter_dict = {"document_type": "act"}  # Filter for Acts/Ordinances
            results = await self.vector_service.query(
                query_vector=query_embedding,
                top_k=top_k,
                filter=filter_dict,
            )

            if not results:
                logger.warning("No statutory documents found")
                return {
                    "answer": "The requested information is not available in the retrieved legal documents.",
                    "citations": [],
                    "sources": [],
                }

            # Prepare context from retrieved documents
            context = self._prepare_context(results)

            # Generate answer using LLM
            prompt = f"""Based on the following statutory provisions, answer the query: {query}

Retrieved Provisions:
{context}

Provide a precise answer with proper citations."""

            answer, provider = await self.llm_service.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.3,  # Low temperature for accuracy
            )

            # Extract citations
            from src.services.citation_service import get_citation_service

            citation_service = get_citation_service()
            citations = citation_service.extract_citations(answer)

            # Prepare sources
            sources = [
                {
                    "id": result["id"],
                    "metadata": result["metadata"],
                    "score": result["score"],
                }
                for result in results
            ]

            logger.info(
                "Statutory search completed",
                citations_count=len(citations),
                sources_count=len(sources),
            )

            return {
                "answer": answer,
                "citations": citations,
                "sources": sources,
            }

        except Exception as e:
            logger.error("Statutory search failed", error=str(e))
            return {
                "answer": f"An error occurred while searching statutory provisions: {str(e)}",
                "citations": [],
                "sources": [],
            }

    def _prepare_context(self, results: List[Dict[str, Any]]) -> str:
        """
        Prepare context string from retrieved results.

        Args:
            results: Retrieved document results

        Returns:
            Formatted context string
        """
        context_parts = []
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            text = metadata.get("text", "")
            act_name = metadata.get("act_name", "Unknown Act")
            section = metadata.get("section", "")

            context_parts.append(
                f"[{i}] {act_name}, Section {section}\n{text}\n"
            )

        return "\n".join(context_parts)

