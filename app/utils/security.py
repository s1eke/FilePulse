"""Security utilities for filename sanitization and share code generation."""
import re
import secrets
import string
from pathlib import Path
import bleach


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent XSS and path traversal attacks.
    
    Args:
        filename: Original filename from user
        
    Returns:
        Sanitized filename safe for storage and display
    """
    # Remove any HTML tags using bleach
    filename = bleach.clean(filename, tags=[], strip=True)
    
    # Remove path components
    filename = Path(filename).name
    
    # Remove or replace dangerous characters
    # Keep only alphanumeric, dots, hyphens, underscores, and spaces
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Replace multiple spaces/underscores with single one
    filename = re.sub(r'[\s_]+', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        name_part = filename[:200]
        ext_part = filename[200:255] if '.' in filename[200:] else ''
        filename = name_part + ext_part
    
    # Fallback if filename becomes empty
    if not filename:
        filename = "unnamed_file"
    
    return filename


def generate_share_code(length: int = 8) -> str:
    """
    Generate a random share code for file access.
    
    Args:
        length: Length of the share code (default: 8)
        
    Returns:
        Random alphanumeric share code
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def get_client_ip(request) -> str:
    """
    Extract client IP address from request, considering proxies.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address
    """
    # Check for X-Forwarded-For header (proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check for X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client
    return request.client.host if request.client else "unknown"
