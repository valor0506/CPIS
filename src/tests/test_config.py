"""Unit tests for configuration validation."""

import pytest
from src.core.config.config import get_settings, reset_settings, Settings
from src.core.exceptions.exceptions import ConfigException


@pytest.fixture(autouse=True)
def cleanup_settings():
    """Reset the settings singleton before and after each test."""
    reset_settings()
    yield
    reset_settings()


def test_default_settings():
    """Test that default settings are loaded correctly when env is empty."""
    settings = get_settings()
    assert settings.APP_NAME == "Career Pipeline Intelligence System"
    assert settings.FILE_UPLOAD_MAX_SIZE_MB == 10
    assert settings.LOG_LEVEL == "INFO"


def test_settings_override(monkeypatch):
    """Test that environment variables override defaults correctly."""
    monkeypatch.setenv("APP_NAME", "Custom Pipeline")
    monkeypatch.setenv("FILE_UPLOAD_MAX_SIZE_MB", "25")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = get_settings()
    assert settings.APP_NAME == "Custom Pipeline"
    assert settings.FILE_UPLOAD_MAX_SIZE_MB == 25
    assert settings.LOG_LEVEL == "DEBUG"


def test_invalid_settings_type(monkeypatch):
    """Test that invalid types trigger a ConfigException."""
    monkeypatch.setenv("FILE_UPLOAD_MAX_SIZE_MB", "not-an-integer")

    with pytest.raises(ConfigException) as exc_info:
        get_settings()

    assert "Configuration validation failed" in str(exc_info.value) or "Invalid value type" in str(exc_info.value)
