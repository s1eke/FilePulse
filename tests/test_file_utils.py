"""Tests for file utility functions."""
import pytest
from pathlib import Path
from app.utils.file_utils import calculate_md5, calculate_md5_from_bytes


def test_calculate_md5(tmp_path):
    """Test MD5 calculation for a file."""
    # Create a test file
    test_file = tmp_path / "test.txt"
    content = b"Hello, this is test content for MD5 calculation."
    test_file.write_bytes(content)
    
    # Calculate MD5
    md5_hash = calculate_md5(test_file)
    
    # Verify it's a valid MD5 hash (32 hex characters)
    assert len(md5_hash) == 32
    assert all(c in '0123456789abcdef' for c in md5_hash)
    
    # Verify consistency
    md5_hash2 = calculate_md5(test_file)
    assert md5_hash == md5_hash2


def test_calculate_md5_large_file(tmp_path):
    """Test MD5 calculation for a large file (chunked reading)."""
    # Create a large test file (> 8KB to test chunking)
    test_file = tmp_path / "large_test.bin"
    content = b"x" * (10 * 1024)  # 10KB
    test_file.write_bytes(content)
    
    # Calculate MD5
    md5_hash = calculate_md5(test_file)
    
    # Verify result
    assert len(md5_hash) == 32
    
    # Compare with byte-based calculation
    md5_from_bytes = calculate_md5_from_bytes(content)
    assert md5_hash == md5_from_bytes


def test_calculate_md5_from_bytes():
    """Test MD5 calculation from byte data."""
    data = b"Test data for MD5 hashing"
    
    md5_hash = calculate_md5_from_bytes(data)
    
    # Verify it's a valid MD5 hash
    assert len(md5_hash) == 32
    assert all(c in '0123456789abcdef' for c in md5_hash)
    
    # Verify consistency
    md5_hash2 = calculate_md5_from_bytes(data)
    assert md5_hash == md5_hash2


def test_calculate_md5_from_bytes_empty():
    """Test MD5 calculation from empty byte data."""
    data = b""
    
    md5_hash = calculate_md5_from_bytes(data)
    
    # MD5 of empty string is d41d8cd98f00b204e9800998ecf8427e
    assert md5_hash == "d41d8cd98f00b204e9800998ecf8427e"


def test_calculate_md5_different_content():
    """Test that different content produces different hashes."""
    data1 = b"Content A"
    data2 = b"Content B"
    
    hash1 = calculate_md5_from_bytes(data1)
    hash2 = calculate_md5_from_bytes(data2)
    
    assert hash1 != hash2
