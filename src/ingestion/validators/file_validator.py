"""File validation module for CPIS.

Defines the interfaces and concrete classes to validate document files
prior to loading and parsing.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from src.core.config.config import get_settings
from src.core.exceptions.exceptions import ValidationException
from src.core.logger.logger import setup_logger

logger = setup_logger("file_validator")


class BaseFileValidator(ABC):
    """Abstract base class for file validators."""

    @abstractmethod
    def validate(self, file_path: Path) -> None:
        """Validate a file path.

        Args:
            file_path: The Path of the file to validate.

        Raises:
            ValidationException: If validation fails.
        """
        pass


class PDFFileValidator(BaseFileValidator):
    """Validates PDF files for size, integrity, and safety constraints."""

    def __init__(self, max_size_mb: int = None) -> None:
        """Initialize the validator.

        Args:
            max_size_mb: Optional custom size limit. Defaults to settings value.
        """
        settings = get_settings()
        self.max_size_mb = max_size_mb if max_size_mb is not None else settings.FILE_UPLOAD_MAX_SIZE_MB
        self.max_size_bytes = self.max_size_mb * 1024 * 1024

    def validate(self, file_path: Path) -> None:
        """Validates that a file is a valid PDF within constraints.

        Args:
            file_path: The path of the file.

        Raises:
            ValidationException: If any validation rule is violated.
        """
        logger.info(f"Validating file: {file_path}")

        # Rule 1: Exists
        if not file_path.exists():
            raise ValidationException(f"File not found: {file_path}")

        # Rule 2: Is actual file
        if not file_path.is_file():
            raise ValidationException(f"Path is not a file: {file_path}")

        # Rule 3: File extension
        if file_path.suffix.lower() != ".pdf":
            raise ValidationException(f"Invalid file extension: {file_path.suffix}. Only .pdf is supported.")

        # Rule 4: File size limit
        file_size = file_path.stat().st_size
        if file_size == 0:
            raise ValidationException("File is empty.")

        if file_size > self.max_size_bytes:
            raise ValidationException(
                f"File size ({file_size / (1024*1024):.2f} MB) exceeds maximum allowed limit ({self.max_size_mb} MB)."
            )

        # Rule 5: Magic bytes verification (%PDF- signature)
        try:
            with open(file_path, "rb") as f:
                header = f.read(4)
                if header != b"%PDF":
                    raise ValidationException("File header is invalid. Not a valid PDF file.")
        except IOError as e:
            raise ValidationException(f"Failed to read file signature: {str(e)}", original_exception=e)

        logger.info(f"File validation succeeded for: {file_path}")
