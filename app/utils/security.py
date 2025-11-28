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
    
    # Remove dangerous characters but keep safe ones
    # Remove: <, >, :, ", /, \, |, ?, *, and other control characters
    # Keep: letters, numbers, spaces, dots, hyphens, underscores, parentheses
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
    
    # Replace multiple spaces with single space
    filename = re.sub(r'\s+', ' ', filename)
    
    # Remove leading/trailing dots, spaces, and hyphens
    filename = filename.strip('. -')
    
    # Limit length while preserving extension
    if len(filename) > 255:
        parts = filename.rsplit('.', 1)
        if len(parts) == 2:
            name, ext = parts
            max_name_len = 255 - len(ext) - 1
            filename = name[:max_name_len] + '.' + ext
        else:
            filename = filename[:255]
    
    # Fallback if filename becomes empty
    if not filename or filename.isspace():
        filename = "unnamed_file"
    
    return filename


def generate_share_code(length: int = 6) -> str:
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
