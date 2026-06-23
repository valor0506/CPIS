"""Document loader module for CPIS.

Defines the interfaces and concrete classes for loading documents from files
and converting them into raw Document schemas.
"""

from abc import ABC, abstractmethod
import hashlib
from pathlib import Path
from pypdf import PdfReader

from src.core.exceptions.exceptions import IngestionException
from src.core.logger.logger import setup_logger
from src.models.schemas.schemas import Document, DocumentMetadata
from src.ingestion.validators.file_validator import BaseFileValidator, PDFFileValidator

logger = setup_logger("pdf_loader")


class BaseDocumentLoader(ABC):
    """Abstract base class for document loaders."""

    @abstractmethod
    def load(self, file_path: Path) -> Document:
        """Load and extract a document from a file path.

        Args:
            file_path: The Path of the file to load.

        Returns:
            Document: The parsed document with content and metadata.

        Raises:
            IngestionException: If loading or parsing fails.
        """
        pass


class PDFDocumentLoader(BaseDocumentLoader):
    """Loads PDF documents, extracts text contents, and computes metadata."""

    def __init__(self, validator: BaseFileValidator = None) -> None:
        """Initialize the PDF document loader.

        Args:
            validator: File validator instance. Defaults to PDFFileValidator.
        """
        self.validator = validator or PDFFileValidator()

    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate the SHA-256 hash of a file.

        Args:
            file_path: The Path of the file.

        Returns:
            str: Hex digest of the hash.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def load(self, file_path: Path) -> Document:
        """Validates and loads a PDF file, extracting text and metadata.

        Args:
            file_path: The Path to the PDF file.

        Returns:
            Document: Ingested document object.

        Raises:
            IngestionException: If validation or loading fails.
        """
        # Proactively validate the file before reading it
        try:
            self.validator.validate(file_path)
        except Exception as e:
            logger.error(f"Validation failed during load for {file_path}: {str(e)}")
            raise IngestionException(f"File validation failed: {str(e)}", original_exception=e)

        try:
            logger.info(f"Opening PDF file: {file_path}")
            reader = PdfReader(file_path)

            if reader.is_encrypted:
                logger.error(f"PDF is encrypted: {file_path}")
                raise IngestionException("Encrypted PDFs are not supported.")

            page_count = len(reader.pages)
            extracted_text_parts = []

            for idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    extracted_text_parts.append(text)
                else:
                    logger.debug(f"Empty text or image-only page at page {idx + 1} of {file_path}")

            raw_content = "\n".join(extracted_text_parts)
            file_size_bytes = file_path.stat().st_size
            sha256 = self._calculate_sha256(file_path)

            metadata = DocumentMetadata(
                source_path=str(file_path.resolve()),
                file_size_bytes=file_size_bytes,
                page_count=page_count,
                sha256=sha256,
            )

            logger.info(f"Successfully loaded PDF with {page_count} pages, size: {file_size_bytes} bytes")
            return Document(content=raw_content, metadata=metadata)

        except IngestionException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading PDF {file_path}: {str(e)}")
            raise IngestionException(f"Failed to load PDF document: {str(e)}", original_exception=e)
