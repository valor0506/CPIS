"""Document parser module for CPIS.

Defines the interfaces and concrete classes for cleaning and normalizing
extracted text before downstream chunking or embedding processing.
"""

from abc import ABC, abstractmethod
import re

from src.core.exceptions.exceptions import IngestionException
from src.core.logger.logger import setup_logger
from src.models.schemas.schemas import Document

logger = setup_logger("document_parser")


class BaseDocumentParser(ABC):
    """Abstract base class for document text parsers."""

    @abstractmethod
    def parse(self, document: Document) -> Document:
        """Parse, clean, and normalize the content of a document.

        Args:
            document: The input Document containing raw text.

        Returns:
            Document: The parsed Document with cleaned text.

        Raises:
            IngestionException: If parsing or cleaning fails.
        """
        pass


class StandardDocumentParser(BaseDocumentParser):
    """Cleans up whitespaces, control characters, and normalizes layout text."""

    def __init__(self, remove_non_printable: bool = True) -> None:
        """Initialize the document parser.

        Args:
            remove_non_printable: If True, filters out non-printable control characters.
        """
        self.remove_non_printable = remove_non_printable

    def _clean_text(self, text: str) -> str:
        """Apply clean-up regexes to normalise spacing and characters.

        Args:
            text: Raw input text.

        Returns:
            str: Cleaned text.
        """
        if not text:
            return ""

        # Step 1: Replace non-printable characters if enabled
        if self.remove_non_printable:
            # Matches control characters (ASCII 0-31 except \t, \n, \r, and ASCII 127)
            text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

        # Step 2: Normalize multiple consecutive whitespaces on a line to a single space
        text = re.sub(r"[ \t]+", " ", text)

        # Step 3: Normalize consecutive blank lines to at most two newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Step 4: Trim leading and trailing whitespaces
        return text.strip()

    def parse(self, document: Document) -> Document:
        """Normalise the text content of the given document.

        Args:
            document: Raw Document instance.

        Returns:
            Document: A new Document instance with cleaned text.

        Raises:
            IngestionException: If the resulting text is empty.
        """
        logger.info(f"Parsing and cleaning document from: {document.metadata.source_path}")

        cleaned_content = self._clean_text(document.content)

        if not cleaned_content:
            logger.error(f"Cleaning resulted in empty content for document: {document.metadata.source_path}")
            raise IngestionException("Document content is empty or contains only non-printable characters.")

        # Create a new document instance with updated content, maintaining metadata immutability
        cleaned_document = Document(content=cleaned_content, metadata=document.metadata)
        logger.info(f"Successfully cleaned document text. Length: {len(cleaned_content)} characters.")
        return cleaned_document
