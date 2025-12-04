"""Base scraper class for legal documents."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class BaseScraper(ABC):
    """Base class for legal document scrapers."""

    @abstractmethod
    async def scrape(self, source_url: str) -> List[Dict[str, Any]]:
        """
        Scrape legal documents from a source.

        Args:
            source_url: URL or identifier for the source

        Returns:
            List of scraped documents with metadata
        """
        pass

    def _extract_metadata(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from a document.

        Args:
            document: Raw document data

        Returns:
            Extracted metadata
        """
        return {
            "source": document.get("source", "unknown"),
            "document_type": document.get("type", "unknown"),
            "title": document.get("title", ""),
            "date": document.get("date", ""),
        }

