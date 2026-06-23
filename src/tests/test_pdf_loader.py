"""Unit tests for PDF Document Loader."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from src.core.exceptions.exceptions import IngestionException
from src.ingestion.loaders.pdf_loader import PDFDocumentLoader
from src.ingestion.validators.file_validator import BaseFileValidator


class MockSuccessValidator(BaseFileValidator):
    """Mock validator that always succeeds."""

    def validate(self, file_path: Path) -> None:
        pass


class MockFailValidator(BaseFileValidator):
    """Mock validator that always fails."""

    def validate(self, file_path: Path) -> None:
        from src.core.exceptions.exceptions import ValidationException
        raise ValidationException("Validation failed intentionally.")


@pytest.fixture
def dummy_pdf_file(tmp_path):
    """Creates a physical file with PDF magic bytes for the loader."""
    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\nsome text contents")
    return pdf_file


def test_loader_validation_failure(dummy_pdf_file):
    """Test that the loader stops and raises IngestionException if validation fails."""
    loader = PDFDocumentLoader(validator=MockFailValidator())
    with pytest.raises(IngestionException) as exc_info:
        loader.load(dummy_pdf_file)
    assert "File validation failed" in str(exc_info.value)


@patch("src.ingestion.loaders.pdf_loader.PdfReader")
def test_loader_encrypted_pdf(mock_pdf_reader_cls, dummy_pdf_file):
    """Test that the loader rejects encrypted PDF files."""
    # Set up the mock reader
    mock_reader = MagicMock()
    mock_reader.is_encrypted = True
    mock_pdf_reader_cls.return_value = mock_reader

    loader = PDFDocumentLoader(validator=MockSuccessValidator())
    with pytest.raises(IngestionException) as exc_info:
        loader.load(dummy_pdf_file)
    assert "Encrypted PDFs are not supported" in str(exc_info.value)


@patch("src.ingestion.loaders.pdf_loader.PdfReader")
def test_loader_successful_parsing(mock_pdf_reader_cls, dummy_pdf_file):
    """Test that the loader correctly parses contents and metadata from a valid PDF."""
    # Configure mock pages
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page 1 Content."
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Page 2 Content."

    mock_reader = MagicMock()
    mock_reader.is_encrypted = False
    mock_reader.pages = [mock_page1, mock_page2]
    mock_pdf_reader_cls.return_value = mock_reader

    loader = PDFDocumentLoader(validator=MockSuccessValidator())
    doc = loader.load(dummy_pdf_file)

    # Assert content
    assert doc.content == "Page 1 Content.\nPage 2 Content."
    # Assert metadata
    assert doc.metadata.page_count == 2
    assert doc.metadata.file_size_bytes == dummy_pdf_file.stat().st_size
    assert doc.metadata.source_path == str(dummy_pdf_file.resolve())
    assert len(doc.metadata.sha256) == 64  # Hex SHA-256 is 64 chars
