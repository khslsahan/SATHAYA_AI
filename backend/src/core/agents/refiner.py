"""Refiner Agent for fact-checking and citation validation."""

from typing import Dict, Any, List
import structlog

from src.services.llm_service import get_llm_service
from src.core.prompts.refiner_prompt import REFINER_SYSTEM_PROMPT

logger = structlog.get_logger(__name__)

DISCLAIMER = """**DISCLAIMER:** *This is not professional legal advice. This information is for research and informational purposes only. Consult a qualified Sri Lankan legal professional for advice regarding your specific circumstances.*"""


class RefinerAgent:
    """Agent for refining and validating answers."""

    def __init__(self):
        """Initialize Refiner Agent."""
        self.llm_service = get_llm_service()
        self.system_prompt = REFINER_SYSTEM_PROMPT

    async def refine(
        self,
        draft_answer: str,
        sources: List[Dict[str, Any]],
        citations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Refine and validate draft answer.

        Args:
            draft_answer: Draft answer to refine
            sources: Source documents used
            citations: Extracted citations

        Returns:
            Refined answer with validation results
        """
        logger.info("Refining answer", answer_length=len(draft_answer))

        try:
            # Prepare source context for validation
            source_context = self._prepare_source_context(sources)

            # Create refinement prompt
            prompt = f"""Review and refine the following draft answer:

Draft Answer:
{draft_answer}

Source Documents Used:
{source_context}

Extracted Citations:
{self._format_citations(citations)}

Please:
1. Verify all claims are supported by the sources
2. Ensure all citations are correct
3. Remove any unsupported information
4. Add the mandatory disclaimer
5. Improve clarity and structure"""

            # Get refined answer
            refined_answer, provider = await self.llm_service.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.3,  # Low temperature for precision
            )

            # Ensure disclaimer is present
            if DISCLAIMER.lower() not in refined_answer.lower():
                refined_answer = f"{refined_answer}\n\n{DISCLAIMER}"

            # Re-extract citations from refined answer
            from src.services.citation_service import get_citation_service

            citation_service = get_citation_service()
            refined_citations = citation_service.extract_citations(refined_answer)

            # Validate citations
            validation_results = self._validate_citations(refined_citations, sources)

            logger.info(
                "Answer refined",
                original_length=len(draft_answer),
                refined_length=len(refined_answer),
                citations_validated=validation_results["valid_count"],
            )

            return {
                "answer": refined_answer,
                "citations": refined_citations,
                "validation": validation_results,
            }

        except Exception as e:
            logger.error("Refinement failed", error=str(e))
            # Return original with disclaimer if refinement fails
            answer_with_disclaimer = (
                f"{draft_answer}\n\n{DISCLAIMER}"
                if DISCLAIMER.lower() not in draft_answer.lower()
                else draft_answer
            )
            return {
                "answer": answer_with_disclaimer,
                "citations": citations,
                "validation": {
                    "valid_count": 0,
                    "invalid_count": 0,
                    "warnings": [f"Refinement error: {str(e)}"],
                },
            }

    def _prepare_source_context(self, sources: List[Dict[str, Any]]) -> str:
        """Prepare source context for validation."""
        context_parts = []
        for i, source in enumerate(sources, 1):
            metadata = source.get("metadata", {})
            text = metadata.get("text", "")[:500]  # Truncate for context
            doc_type = metadata.get("document_type", "unknown")

            context_parts.append(
                f"Source {i} ({doc_type}):\n{text}\n"
            )

        return "\n".join(context_parts)

    def _format_citations(self, citations: List[Dict[str, Any]]) -> str:
        """Format citations for prompt."""
        if not citations:
            return "No citations found."

        citation_strings = []
        for citation in citations:
            citation_strings.append(f"- {citation.get('full_text', 'Unknown citation')}")

        return "\n".join(citation_strings)

    def _validate_citations(
        self,
        citations: List[Dict[str, Any]],
        sources: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Validate citations against sources."""
        from src.services.citation_service import get_citation_service

        citation_service = get_citation_service()

        valid_count = 0
        invalid_count = 0
        warnings = []

        for citation in citations:
            if citation_service.validate_citation(citation):
                valid_count += 1
            else:
                invalid_count += 1
                warnings.append(f"Invalid citation format: {citation.get('full_text', 'Unknown')}")

        return {
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "warnings": warnings,
        }

