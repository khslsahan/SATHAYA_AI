"""Metadata extractor for legal documents."""

import re
from typing import Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class MetadataExtractor:
    """Extract metadata from legal documents."""

    # Patterns for common legal document metadata
    ACT_NAME_PATTERN = re.compile(
        r"(?:^|\s)([A-Z][a-zA-Z\s]+(?:Act|Ordinance))", re.IGNORECASE
    )
    YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")
    CASE_CITATION_PATTERN = re.compile(r"\[(\d{4})\]\s*(\d+)\s*([A-Z]{2,4})\s*(\d+)")

    def extract(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from document.

        Args:
            document: Document with text

        Returns:
            Extracted metadata
        """
        text = document.get("text", "")
        existing_metadata = document.get("metadata", {})

        metadata = existing_metadata.copy()

        # Extract document type
        if not metadata.get("document_type"):
            metadata["document_type"] = self._detect_document_type(text)

        # Extract Act name if applicable
        if metadata["document_type"] == "act":
            act_match = self.ACT_NAME_PATTERN.search(text)
            if act_match:
                metadata["act_name"] = act_match.group(1)

        # Extract year
        year_match = self.YEAR_PATTERN.search(text)
        if year_match:
            metadata["year"] = int(year_match.group(0))

        # Extract case citation if applicable
        if metadata["document_type"] == "case":
            case_match = self.CASE_CITATION_PATTERN.search(text)
            if case_match:
                metadata["year"] = int(case_match.group(1))
                metadata["volume"] = int(case_match.group(2))
                metadata["reporter"] = case_match.group(3)
                metadata["page"] = int(case_match.group(4))

        # Extract section/article numbers
        section_match = re.search(r"Section\s+(\d+[A-Za-z]*)", text, re.IGNORECASE)
        if section_match:
            metadata["section"] = section_match.group(1)

        article_match = re.search(r"Article\s+(\d+[A-Za-z]*)", text, re.IGNORECASE)
        if article_match:
            metadata["article"] = article_match.group(1)

        return metadata

    def _detect_document_type(self, text: str) -> str:
        """Detect document type from text."""
        text_lower = text.lower()

        if "section" in text_lower and ("act" in text_lower or "ordinance" in text_lower):
            return "act"
        elif "article" in text_lower and "constitution" in text_lower:
            return "constitution"
        elif re.search(r"\[(\d{4})\]\s*\d+\s*[A-Z]{2,4}\s*\d+", text):
            return "case"
        else:
            return "unknown"

