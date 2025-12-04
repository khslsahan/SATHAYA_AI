"""PDF parser for legal documents."""

from typing import Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class PDFParser:
    """Parser for PDF legal documents."""

    def __init__(self):
        """Initialize PDF parser."""

    def parse(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Parsed document with text and metadata
        """
        logger.info("Parsing PDF", path=pdf_path)

        try:
            import pdfplumber

            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

            full_text = "\n".join(text_parts)

            return {
                "text": full_text,
                "page_count": len(pdf.pages),
                "source": pdf_path,
            }

        except ImportError:
            logger.error("pdfplumber not installed")
            raise
        except Exception as e:
            logger.error("PDF parsing failed", error=str(e))
            raise

