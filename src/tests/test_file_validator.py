"""Unit tests for PDF file validation."""

from pathlib import Path
import pytest

from src.core.exceptions.exceptions import ValidationException
from src.ingestion.validators.file_validator import PDFFileValidator


def test_validator_file_not_found():
    """Test that a non-existent file path raises a ValidationException."""
    validator = PDFFileValidator()
    non_existent = Path("non_existent_file.pdf")
    with pytest.raises(ValidationException) as exc_info:
        validator.validate(non_existent)
    assert "File not found" in str(exc_info.value)


def test_validator_path_is_directory(tmp_path):
    """Test that a directory path instead of a file raises a ValidationException."""
    validator = PDFFileValidator()
    with pytest.raises(ValidationException) as exc_info:
        validator.validate(tmp_path)
    assert "Path is not a file" in str(exc_info.value)


def test_validator_invalid_extension(tmp_path):
    """Test that a non-PDF file extension raises a ValidationException."""
    validator = PDFFileValidator()
    text_file = tmp_path / "test.txt"
    text_file.write_text("dummy text")

    with pytest.raises(ValidationException) as exc_info:
        validator.validate(text_file)
    assert "Invalid file extension" in str(exc_info.value)


def test_validator_empty_file(tmp_path):
    """Test that an empty file raises a ValidationException."""
    validator = PDFFileValidator()
    empty_file = tmp_path / "empty.pdf"
    empty_file.touch()

    with pytest.raises(ValidationException) as exc_info:
        validator.validate(empty_file)
    assert "File is empty" in str(exc_info.value)


def test_validator_oversized_file(tmp_path):
    """Test that a file exceeding max size limit raises a ValidationException."""
    # Instantiating validator with 1 KB limit to keep test execution fast
    validator = PDFFileValidator(max_size_mb=0)  # Effectively 0 MB max size
    file_path = tmp_path / "too_large.pdf"
    file_path.write_bytes(b"%PDF-1.4 header contents")

    with pytest.raises(ValidationException) as exc_info:
        validator.validate(file_path)
    assert "exceeds maximum allowed limit" in str(exc_info.value)


def test_validator_invalid_magic_bytes(tmp_path):
    """Test that a file missing '%PDF' header raises a ValidationException."""
    validator = PDFFileValidator()
    bad_pdf = tmp_path / "bad.pdf"
    bad_pdf.write_bytes(b"NOT_A_PDF header contents")

    with pytest.raises(ValidationException) as exc_info:
        validator.validate(bad_pdf)
    assert "File header is invalid" in str(exc_info.value)


def test_validator_valid_pdf(tmp_path):
    """Test that a valid PDF with correct magic bytes passes validation."""
    validator = PDFFileValidator(max_size_mb=1)
    valid_pdf = tmp_path / "valid.pdf"
    valid_pdf.write_bytes(b"%PDF-1.4\n%metadata...")

    # Should run without raising any exceptions
    validator.validate(valid_pdf)
