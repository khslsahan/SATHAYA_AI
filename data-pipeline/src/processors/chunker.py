"""Legal structure-aware chunker for documents."""

import re
from typing import List, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class LegalChunker:
    """Chunker that preserves legal document structure."""

    # Patterns for legal structure
    SECTION_PATTERN = re.compile(r"^Section\s+(\d+[A-Za-z]*)", re.IGNORECASE | re.MULTILINE)
    ARTICLE_PATTERN = re.compile(r"^Article\s+(\d+[A-Za-z]*)", re.IGNORECASE | re.MULTILINE)
    CHAPTER_PATTERN = re.compile(r"^Chapter\s+(\d+[A-Za-z]*)", re.IGNORECASE | re.MULTILINE)
    PART_PATTERN = re.compile(r"^Part\s+(\d+[A-Za-z]*)", re.IGNORECASE | re.MULTILINE)

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize chunker.

        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk a legal document preserving structure.

        Args:
            document: Document with text and metadata

        Returns:
            List of chunks with preserved metadata
        """
        text = document.get("text", "")
        metadata = document.get("metadata", {})

        logger.info("Chunking document", text_length=len(text))

        # Try to chunk by legal structure first
        chunks = self._chunk_by_structure(text, metadata)

        # If structure-based chunking didn't work, use sliding window
        if not chunks:
            chunks = self._chunk_sliding_window(text, metadata)

        logger.info("Document chunked", chunks_count=len(chunks))
        return chunks

    def _chunk_by_structure(
        self, text: str, base_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Chunk by legal structure (sections, articles, etc.)."""
        chunks = []

        # Find all section/article boundaries
        boundaries = []
        for match in self.SECTION_PATTERN.finditer(text):
            boundaries.append(("section", match.start(), match.group(1)))

        for match in self.ARTICLE_PATTERN.finditer(text):
            boundaries.append(("article", match.start(), match.group(1)))

        if not boundaries:
            return []

        # Sort by position
        boundaries.sort(key=lambda x: x[1])

        # Create chunks at boundaries
        for i, (boundary_type, start, identifier) in enumerate(boundaries):
            end = boundaries[i + 1][1] if i + 1 < len(boundaries) else len(text)
            chunk_text = text[start:end].strip()

            if len(chunk_text) > self.chunk_size:
                # Further split large chunks
                sub_chunks = self._split_large_chunk(chunk_text, base_metadata)
                chunks.extend(sub_chunks)
            else:
                chunk_metadata = base_metadata.copy()
                chunk_metadata[boundary_type] = identifier
                chunk_metadata["chunk_type"] = boundary_type
                chunks.append({
                    "text": chunk_text,
                    "metadata": chunk_metadata,
                })

        return chunks

    def _chunk_sliding_window(
        self, text: str, base_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Chunk using sliding window approach."""
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending near chunk boundary
                for i in range(end, max(start, end - 100), -1):
                    if text[i] in ".!?\n":
                        end = i + 1
                        break

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunk_metadata = base_metadata.copy()
                chunk_metadata["chunk_index"] = len(chunks)
                chunks.append({
                    "text": chunk_text,
                    "metadata": chunk_metadata,
                })

            start = end - self.chunk_overlap

        return chunks

    def _split_large_chunk(
        self, text: str, base_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Split a chunk that's too large."""
        # Split by paragraphs first
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []

        for para in paragraphs:
            if sum(len(p) for p in current_chunk) + len(para) > self.chunk_size:
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunk_metadata = base_metadata.copy()
                    chunk_metadata["chunk_index"] = len(chunks)
                    chunks.append({
                        "text": chunk_text,
                        "metadata": chunk_metadata,
                    })
                current_chunk = [para]
            else:
                current_chunk.append(para)

        # Add remaining chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunk_metadata = base_metadata.copy()
            chunk_metadata["chunk_index"] = len(chunks)
            chunks.append({
                "text": chunk_text,
                "metadata": chunk_metadata,
            })

        return chunks

