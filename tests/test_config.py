"""Tests for application configuration."""
import pytest
import os
from app.config import Settings


def test_parse_file_size_integer():
    """Test file size parsing with integer value."""
    settings = Settings(max_file_size=1048576)
    assert settings.max_file_size == 1048576


def test_parse_file_size_mb():
    """Test file size parsing with MB unit."""
    settings = Settings(max_file_size="100MB")
    assert settings.max_file_size == 100 * 1024 * 1024


def test_parse_file_size_gb():
    """Test file size parsing with GB unit."""
    settings = Settings(max_file_size="1GB")
    assert settings.max_file_size == 1 * 1024 * 1024 * 1024


def test_parse_file_size_kb():
    """Test file size parsing with KB unit."""
    settings = Settings(max_file_size="500KB")
    assert settings.max_file_size == 500 * 1024


def test_parse_file_size_bytes():
    """Test file size parsing with B unit."""
    settings = Settings(max_file_size="1024B")
    assert settings.max_file_size == 1024


def test_parse_file_size_no_unit():
    """Test file size parsing with numeric string (defaults to bytes)."""
    settings = Settings(max_file_size="2048")
    assert settings.max_file_size == 2048


def test_parse_file_size_decimal():
    """Test file size parsing with decimal values."""
    settings = Settings(max_file_size="1.5GB")
    assert settings.max_file_size == int(1.5 * 1024 * 1024 * 1024)


def test_parse_file_size_invalid_format():
    """Test file size parsing with invalid format."""
    with pytest.raises(ValueError) as exc_info:
        Settings(max_file_size="invalid_size")
    assert "Invalid file size format" in str(exc_info.value)


def test_default_settings():
    """Test default configuration values."""
    settings = Settings()
    assert settings.upload_dir == "./uploads"
    assert settings.database_url == "sqlite+aiosqlite:///./filepulse.db"
    assert settings.enable_docs is False
    assert settings.debug is False
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.file_expiry_days == 7
