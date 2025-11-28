"""Utility functions for file operations."""
import hashlib
from pathlib import Path


def calculate_md5(file_path: Path) -> str:
    """
    Calculate MD5 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MD5 hash as hexadecimal string
    """
    md5_hash = hashlib.md5()
    
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(8192), b""):
            md5_hash.update(chunk)
    
    return md5_hash.hexdigest()


def calculate_md5_from_bytes(data: bytes) -> str:
    """
    Calculate MD5 hash from byte data.
    
    Args:
        data: Byte data
        
    Returns:
        MD5 hash as hexadecimal string
    """
    return hashlib.md5(data).hexdigest()
