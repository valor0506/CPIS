"""Document chunking utility for CPIS.

Splits normalized text from ingested documents into smaller chunks
with overlapping ranges to preserve context and optimize vector searches.
"""

import re
from typing import List

from src.models.schemas.schemas import Document, DocumentChunk


class DocumentChunker:
    """Splits a Document's content into overlapping chunks of semi-uniform size."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100) -> None:
        """Initialize the chunker.

        Args:
            chunk_size: Maximum characters per chunk.
            chunk_overlap: Overlap in characters between consecutive chunks.

        Raises:
            ValueError: If chunk_size is not positive or chunk_overlap is invalid.
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be non-negative and less than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_document(self, document: Document) -> List[DocumentChunk]:
        """Split a document's clean text into a list of DocumentChunks.

        Args:
            document: The input parsed Document DTO.

        Returns:
            List[DocumentChunk]: List of generated text chunks with metadata.
        """
        text = document.content
        sha256 = document.metadata.sha256
        chunks: List[DocumentChunk] = []

        if not text.strip():
            return chunks

        start = 0
        index = 0
        text_len = len(text)

        while start < text_len:
            # Determine maximum end boundary
            end = min(start + self.chunk_size, text_len)

            # If we are not at the end of the text, look for smart splits within overlap
            if end < text_len:
                search_start = max(start, end - self.chunk_overlap)
                subtext = text[search_start:end]
                boundary = -1

                # Look for double newline (paragraphs) first
                double_newlines = [m.start() for m in re.finditer(r"\n\n", subtext)]
                if double_newlines:
                    boundary = search_start + double_newlines[-1] + 2
                else:
                    # Look for single newline
                    newlines = [m.start() for m in re.finditer(r"\n", subtext)]
                    if newlines:
                        boundary = search_start + newlines[-1] + 1
                    else:
                        # Look for spaces (word breaks)
                        spaces = [m.start() for m in re.finditer(r" ", subtext)]
                        if spaces:
                            boundary = search_start + spaces[-1] + 1

                # Adjust end pointer if a smart boundary is found
                if boundary != -1 and boundary > start:
                    end = boundary

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunk_id = f"{sha256}_chunk_{index}"
                chunk_metadata = {
                    "source_path": document.metadata.source_path,
                    "sha256": sha256,
                    "chunk_index": index,
                    "start_char": start,
                    "end_char": end,
                }
                chunks.append(
                    DocumentChunk(
                        id=chunk_id,
                        text=chunk_text,
                        metadata=chunk_metadata,
                    )
                )
                index += 1

            # Shift start pointer
            new_start = end - self.chunk_overlap
            # Ensure start pointer moves forward to avoid infinite loop
            if new_start <= start:
                start = end
            else:
                start = new_start

        return chunks
