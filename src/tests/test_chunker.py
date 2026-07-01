"""Unit tests for DocumentChunker."""

import pytest
from src.models.schemas.schemas import Document, DocumentMetadata
from src.ingestion.parsers.chunker import DocumentChunker


def test_chunker_invalid_initialization():
    """Verify that chunker raises ValueError for invalid size/overlap."""
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        DocumentChunker(chunk_size=0)

    with pytest.raises(ValueError, match="chunk_size must be positive"):
        DocumentChunker(chunk_size=-10)

    with pytest.raises(ValueError, match="chunk_overlap must be non-negative and less than chunk_size"):
        DocumentChunker(chunk_size=100, chunk_overlap=-5)

    with pytest.raises(ValueError, match="chunk_overlap must be non-negative and less than chunk_size"):
        DocumentChunker(chunk_size=100, chunk_overlap=100)

    with pytest.raises(ValueError, match="chunk_overlap must be non-negative and less than chunk_size"):
        DocumentChunker(chunk_size=100, chunk_overlap=120)


def test_chunker_empty_document():
    """Verify that chunker returns empty list for blank content."""
    metadata = DocumentMetadata(
        source_path="test.pdf",
        file_size_bytes=100,
        page_count=1,
        sha256="test_hash",
    )
    doc = Document(content="   \n   ", metadata=metadata)
    chunker = DocumentChunker()
    chunks = chunker.split_document(doc)
    assert len(chunks) == 0


def test_chunker_smart_splitting():
    """Verify that chunker splits at natural boundaries within the overlap window."""
    metadata = DocumentMetadata(
        source_path="test.pdf",
        file_size_bytes=100,
        page_count=1,
        sha256="test_hash",
    )
    # The text has clean newline and space boundaries
    content = "Hello world.\n\nThis is paragraph two.\nThis is a newline. End of content."
    doc = Document(content=content, metadata=metadata)

    # Let's chunk with size=30 and overlap=15
    chunker = DocumentChunker(chunk_size=30, chunk_overlap=15)
    chunks = chunker.split_document(doc)

    assert len(chunks) > 0
    # Every chunk should be well-formed
    for i, chunk in enumerate(chunks):
        assert chunk.id == f"test_hash_chunk_{i}"
        assert chunk.text != ""
        assert chunk.metadata["sha256"] == "test_hash"
        assert chunk.metadata["chunk_index"] == i
        assert "start_char" in chunk.metadata
        assert "end_char" in chunk.metadata
