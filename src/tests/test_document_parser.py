"""Unit tests for document parsing and text cleaning."""

import pytest

from src.core.exceptions.exceptions import IngestionException
from src.models.schemas.schemas import Document, DocumentMetadata
from src.ingestion.parsers.document_parser import StandardDocumentParser


@pytest.fixture
def base_metadata() -> DocumentMetadata:
    """Fixture for standard document metadata."""
    return DocumentMetadata(
        source_path="mock.pdf",
        file_size_bytes=100,
        page_count=1,
        sha256="abc123sha",
    )


def test_parser_normalizes_whitespace(base_metadata):
    """Test that multiple spaces and tabs are compressed into a single space."""
    parser = StandardDocumentParser()
    raw_text = "This   is a\t\tline  with spaces."
    doc = Document(content=raw_text, metadata=base_metadata)

    parsed_doc = parser.parse(doc)
    assert parsed_doc.content == "This is a line with spaces."


def test_parser_normalizes_newlines(base_metadata):
    """Test that 3 or more newlines are normalized to at most 2 newlines."""
    parser = StandardDocumentParser()
    raw_text = "Paragraph 1\n\n\n\n\nParagraph 2\n\nParagraph 3"
    doc = Document(content=raw_text, metadata=base_metadata)

    parsed_doc = parser.parse(doc)
    assert parsed_doc.content == "Paragraph 1\n\nParagraph 2\n\nParagraph 3"


def test_parser_removes_control_characters(base_metadata):
    """Test that non-printable ASCII control characters are stripped."""
    parser = StandardDocumentParser(remove_non_printable=True)
    # \x02 and \x1f are ASCII control chars
    raw_text = "Clean\x02 text\x1f here"
    doc = Document(content=raw_text, metadata=base_metadata)

    parsed_doc = parser.parse(doc)
    assert parsed_doc.content == "Clean text here"


def test_parser_trims_flanking_whitespace(base_metadata):
    """Test that leading and trailing whitespace is stripped."""
    parser = StandardDocumentParser()
    raw_text = "  \n  Trim me   \n  "
    doc = Document(content=raw_text, metadata=base_metadata)

    parsed_doc = parser.parse(doc)
    assert parsed_doc.content == "Trim me"


def test_parser_raises_for_empty_cleaned_content(base_metadata):
    """Test that a document with empty content after cleaning raises IngestionException."""
    parser = StandardDocumentParser()
    raw_text = "   \n\n   "
    doc = Document(content=raw_text, metadata=base_metadata)

    with pytest.raises(IngestionException) as exc_info:
        parser.parse(doc)
    assert "Document content is empty" in str(exc_info.value)
