"""Custom exceptions for the Career Pipeline Intelligence System (CPIS).

This module defines the base and specialized exceptions used across the codebase
to enforce clean error handling and separation of concerns.
"""

from typing import Optional


class CPISException(Exception):
    """Base exception for all CPIS-related errors."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.message = message
        self.original_exception = original_exception

    def __str__(self) -> str:
        if self.original_exception:
            return f"{self.message} (Caused by: {repr(self.original_exception)})"
        return self.message


class ConfigException(CPISException):
    """Raised when configuration loading or validation fails."""
    pass


class IngestionException(CPISException):
    """Raised when document loading, parsing, or extraction fails."""
    pass


class ValidationException(CPISException):
    """Raised when file validation (e.g. format, size, security checks) fails."""
    pass
