"""Case Law Agent for searching legal precedents."""

from typing import List, Dict, Any
import structlog

from src.services.llm_service import get_llm_service
from src.services.vector_service import get_vector_service
from src.services.embedding_service import get_embedding_service
from src.core.prompts.case_law_prompt import CASE_LAW_SYSTEM_PROMPT

logger = structlog.get_logger(__name__)


class CaseLawAgent:
    """Agent for searching and summarizing legal precedents."""

    def __init__(self):
        """Initialize Case Law Agent."""
        self.llm_service = get_llm_service()
        self.vector_service = get_vector_service()
        self.embedding_service = get_embedding_service()
        self.system_prompt = CASE_LAW_SYSTEM_PROMPT

    async def search(
        self, query: str, top_k: int = 5, year_filter: int | None = None
    ) -> Dict[str, Any]:
        """
        Search for relevant case law precedents.

        Args:
            query: Search query
            top_k: Number of results to retrieve
            year_filter: Optional year filter for temporal awareness

        Returns:
            Answer with case citations and sources
        """
        logger.info(
            "Case law agent searching",
            query=query[:100],
            year_filter=year_filter,
        )

        try:
            # Initialize vector service if needed
            await self.vector_service.initialize()

            # Generate query embedding
            query_embedding = self.embedding_service.encode_single(query)

            # Build filter for case law documents
            filter_dict = {"document_type": "case"}
            if year_filter:
                filter_dict["year"] = year_filter

            # Search vector database
            results = await self.vector_service.query(
                query_vector=query_embedding,
                top_k=top_k,
                filter=filter_dict,
            )

            if not results:
                logger.warning("No case law documents found")
                return {
                    "answer": "No relevant case law was found in the retrieved documents.",
                    "citations": [],
                    "sources": [],
                }

            # Sort by year (most recent first) for temporal awareness
            results = sorted(
                results,
                key=lambda x: x.get("metadata", {}).get("year", 0),
                reverse=True,
            )

            # Prepare context from retrieved cases
            context = self._prepare_context(results)

            # Generate answer using LLM
            prompt = f"""Based on the following case law precedents, answer the query: {query}

Retrieved Cases:
{context}

Provide a summary of relevant cases with proper citations, ordered by relevance and recency."""

            answer, provider = await self.llm_service.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.4,
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
                "Case law search completed",
                citations_count=len(citations),
                sources_count=len(sources),
            )

            return {
                "answer": answer,
                "citations": citations,
                "sources": sources,
            }

        except Exception as e:
            logger.error("Case law search failed", error=str(e))
            return {
                "answer": f"An error occurred while searching case law: {str(e)}",
                "citations": [],
                "sources": [],
            }

    def _prepare_context(self, results: List[Dict[str, Any]]) -> str:
        """
        Prepare context string from retrieved case results.

        Args:
            results: Retrieved case law results

        Returns:
            Formatted context string
        """
        context_parts = []
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            text = metadata.get("text", "")
            year = metadata.get("year", "Unknown")
            volume = metadata.get("volume", "")
            reporter = metadata.get("reporter", "SLR")
            page = metadata.get("page", "")
            court = metadata.get("court", "Unknown Court")

            citation = f"[{year}] {volume} {reporter} {page}"
            context_parts.append(
                f"[{i}] {citation} ({court}, {year})\n{text}\n"
            )

        return "\n".join(context_parts)

