"""Configuration management for CPIS.

This module loads environment variables, validates them using Pydantic,
and provides a unified configuration settings object.
"""

import os
from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

from src.core.exceptions.exceptions import ConfigException

# Load environment variables from .env file if it exists
load_dotenv()


class Settings(BaseModel):
    """Application settings and configuration validation model."""

    APP_NAME: str = Field(default="Career Pipeline Intelligence System")
    APP_ENV: str = Field(default="development")

    # Logging config
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE_PATH: Optional[str] = Field(default="logs/cpis.log")

    # Storage and Vector DB configuration
    VECTOR_DB_PATH: str = Field(default="data/chroma")
    
    # Ingestion constraints
    FILE_UPLOAD_MAX_SIZE_MB: int = Field(default=10)

    # API Keys & Third-party integrations
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    GOOGLE_SHEETS_SPREADSHEET_ID: Optional[str] = Field(default=None)
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(default=None)

    class Config:
        """Pydantic model config."""
        frozen = True
        extra = "ignore"


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Initialize and return the cached application settings.

    Raises:
        ConfigException: If environment validation fails.
    """
    global _settings
    if _settings is None:
        try:
            # Re-read environment variables to ensure any runtime additions are captured
            settings_data = {
                "APP_NAME": os.getenv("APP_NAME", "Career Pipeline Intelligence System"),
                "APP_ENV": os.getenv("APP_ENV", "development"),
                "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
                "LOG_FILE_PATH": os.getenv("LOG_FILE_PATH", "logs/cpis.log"),
                "VECTOR_DB_PATH": os.getenv("VECTOR_DB_PATH", "data/chroma"),
                "FILE_UPLOAD_MAX_SIZE_MB": int(os.getenv("FILE_UPLOAD_MAX_SIZE_MB", "10")),
                "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
                "GOOGLE_SHEETS_SPREADSHEET_ID": os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID"),
                "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            }
            _settings = Settings(**settings_data)
        except ValidationError as e:
            raise ConfigException(f"Configuration validation failed: {str(e)}", original_exception=e)
        except ValueError as e:
            raise ConfigException(f"Invalid value type in environment variables: {str(e)}", original_exception=e)
    return _settings


def reset_settings() -> None:
    """Reset the configuration singleton cache. Useful for unit testing."""
    global _settings
    _settings = None
