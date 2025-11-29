"""Tests for security utilities."""
import pytest
from unittest.mock import MagicMock
from app.utils.security import sanitize_filename, generate_share_code, get_client_ip


def test_sanitize_filename_removes_html():
    """Test that HTML tags are removed from filenames."""
    dangerous_name = "<script>alert('xss')</script>test.txt"
    safe_name = sanitize_filename(dangerous_name)
    
    assert "<script>" not in safe_name
    assert  "<" not in safe_name
    assert ">" not in safe_name


def test_sanitize_filename_removes_path_traversal():
    """Test that path traversal attempts are blocked."""
    dangerous_name = "../../etc/passwd"
    safe_name = sanitize_filename(dangerous_name)
    
    assert ".." not in safe_name
    assert "/" not in safe_name or safe_name == "passwd"  # Slashes removed
    assert "passwd" in safe_name


def test_sanitize_filename_preserves_safe_chars():
    """Test that safe characters are preserved."""
    safe_input = "my_document-v2.1.pdf"
    result = sanitize_filename(safe_input)
    
    assert result == "my_document-v2.1.pdf"


def test_sanitize_filename_handles_special_chars():
    """Test special character handling."""
    # Only < > : " / \ | ? * and control chars are removed
    # @#$ and other chars are kept
    inputs_and_expected = [
        ("document (copy).pdf", "document (copy).pdf"),  # Parentheses kept
        ("file   name.txt", "file name.txt"),  # Multiple spaces to single
        ("test<file>.txt", "test.txt"),  # Angle brackets and content between removed
    ]
    
    for input_name,expected in inputs_and_expected:
        result = sanitize_filename(input_name)
        assert result == expected, f"Expected {expected}, got {result}"


def test_sanitize_filename_handles_empty():
    """Test that empty filenames get a default value."""
    result = sanitize_filename("")
    assert result == "unnamed_file"
    
    result = sanitize_filename("   ")
    assert result == "unnamed_file"


def test_sanitize_filename_truncates_long_names():
    """Test that very long filenames are truncated."""
    long_name = "a" * 300 + ".txt"
    result = sanitize_filename(long_name)
    
    assert len(result) <= 255
    assert result.endswith(".txt")  # Extension preserved


def test_generate_share_code_length():
    """Test that share codes have correct length."""
    code = generate_share_code()
    assert len(code) == 6
    
    code = generate_share_code(12)
    assert len(code) == 12


def test_generate_share_code_alphanumeric():
    """Test that share codes contain only alphanumeric characters."""
    code = generate_share_code()
    assert code.isalnum()


def test_generate_share_code_uniqueness():
    """Test that generated codes are unique."""
    codes = set()
    for _ in range(100):
        code = generate_share_code()
        codes.add(code)
    
    # Should have 100 unique codes
    assert len(codes) == 100


def test_sanitize_filename_xss_variants():
    """Test various XSS attack vectors."""
    xss_vectors = [
        "<img src=x onerror=alert('XSS')>",
        "<svg/onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(\"XSS\")'></iframe>",
        "&#60;script&#62;alert('XSS')&#60;/script&#62;",
    ]
    
    for vector in xss_vectors:
        safe_name = sanitize_filename(f"{vector}file.txt")
        
        # Should not contain dangerous patterns
        assert "<" not in safe_name
        assert ">" not in safe_name


def test_sanitize_filename_sql_injection():
    """Test SQL injection patterns in filenames."""
    sql_patterns = [
        "'; DROP TABLE files; --",
        "1' OR '1'='1",
        "admin'--",
    ]
    
    for pattern in sql_patterns:
        safe_name = sanitize_filename(f"{pattern}.txt")
        
        # Dangerous chars may be removed, just ensure no crashes
        # and result is safe
        assert safe_name
        assert len(safe_name) > 0


def test_get_client_ip_with_x_forwarded_for():
    """Test get_client_ip with X-Forwarded-For header."""
    request = MagicMock()
    request.headers.get = lambda key: "203.0.113.1, 198.51.100.1" if key == "X-Forwarded-For" else None
    
    ip = get_client_ip(request)
    assert ip == "203.0.113.1"


def test_get_client_ip_with_x_real_ip():
    """Test get_client_ip with X-Real-IP header."""
    request = MagicMock()
    request.headers.get = lambda key: "203.0.113.5" if key == "X-Real-IP" else None
    
    ip = get_client_ip(request)
    assert ip == "203.0.113.5"


def test_get_client_ip_fallback_to_client():
    """Test get_client_ip fallback to direct client."""
    request = MagicMock()
    request.headers.get = lambda key: None
    request.client.host = "192.168.1.100"
    
    ip = get_client_ip(request)
    assert ip == "192.168.1.100"


def test_get_client_ip_no_client():
    """Test get_client_ip when client is None."""
    request = MagicMock()
    request.headers.get = lambda key: None
    request.client = None
    
    ip = get_client_ip(request)
    assert ip == "unknown"
