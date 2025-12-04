"""Citation formatting service for legal documents."""

import re
from typing import Dict, Any, List
import structlog

logger = structlog.get_logger(__name__)


class CitationService:
    """Service for formatting and validating legal citations."""

    # Patterns for different citation types
    ACT_PATTERN = re.compile(
        r"(?:^|\s)([A-Z][a-zA-Z\s]+(?:Act|Ordinance))\s*,\s*Section\s+(\d+[A-Za-z]*)",
        re.IGNORECASE,
    )
    CASE_PATTERN = re.compile(
        r"\[(\d{4})\]\s*(\d+)\s*([A-Z]{2,4})\s*(\d+)", re.IGNORECASE
    )
    CONSTITUTION_PATTERN = re.compile(
        r"Constitution\s+of\s+Sri\s+Lanka\s*,\s*Article\s+(\d+[A-Za-z]*)",
        re.IGNORECASE,
    )

    @staticmethod
    def format_act_citation(act_name: str, section: str) -> str:
        """
        Format an Act citation.

        Args:
            act_name: Name of the Act
            section: Section number

        Returns:
            Formatted citation string
        """
        return f"{act_name}, Section {section}"

    @staticmethod
    def format_case_citation(year: int, volume: int, reporter: str, page: int) -> str:
        """
        Format a case law citation.

        Args:
            year: Year of the case
            volume: Volume number
            reporter: Reporter abbreviation (e.g., SLR)
            page: Page number

        Returns:
            Formatted citation string
        """
        return f"[{year}] {volume} {reporter.upper()} {page}"

    @staticmethod
    def format_constitution_citation(article: str) -> str:
        """
        Format a Constitution citation.

        Args:
            article: Article number

        Returns:
            Formatted citation string
        """
        return f"Constitution of Sri Lanka, Article {article}"

    def extract_citations(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract citations from text.

        Args:
            text: Text to extract citations from

        Returns:
            List of extracted citations with metadata
        """
        citations = []

        # Extract Act citations
        for match in self.ACT_PATTERN.finditer(text):
            citations.append({
                "type": "act",
                "act_name": match.group(1),
                "section": match.group(2),
                "full_text": match.group(0).strip(),
            })

        # Extract case citations
        for match in self.CASE_PATTERN.finditer(text):
            citations.append({
                "type": "case",
                "year": int(match.group(1)),
                "volume": int(match.group(2)),
                "reporter": match.group(3),
                "page": int(match.group(4)),
                "full_text": match.group(0).strip(),
            })

        # Extract Constitution citations
        for match in self.CONSTITUTION_PATTERN.finditer(text):
            citations.append({
                "type": "constitution",
                "article": match.group(1),
                "full_text": match.group(0).strip(),
            })

        return citations

    def validate_citation(self, citation: Dict[str, Any]) -> bool:
        """
        Validate a citation structure.

        Args:
            citation: Citation dictionary

        Returns:
            True if valid, False otherwise
        """
        citation_type = citation.get("type")

        if citation_type == "act":
            return "act_name" in citation and "section" in citation
        elif citation_type == "case":
            return all(
                key in citation
                for key in ["year", "volume", "reporter", "page"]
            )
        elif citation_type == "constitution":
            return "article" in citation
        else:
            return False

    def format_citation_from_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Format citation from document metadata.

        Args:
            metadata: Document metadata

        Returns:
            Formatted citation string
        """
        doc_type = metadata.get("document_type", "").lower()

        if doc_type == "act":
            return self.format_act_citation(
                metadata.get("act_name", "Unknown Act"),
                metadata.get("section", ""),
            )
        elif doc_type == "case":
            return self.format_case_citation(
                metadata.get("year", 0),
                metadata.get("volume", 0),
                metadata.get("reporter", ""),
                metadata.get("page", 0),
            )
        elif doc_type == "constitution":
            return self.format_constitution_citation(metadata.get("article", ""))
        else:
            # Fallback to generic citation
            return metadata.get("source", "Unknown source")


# Singleton instance
_citation_service: CitationService | None = None


def get_citation_service() -> CitationService:
    """Get citation service singleton."""
    global _citation_service
    if _citation_service is None:
        _citation_service = CitationService()
    return _citation_service

