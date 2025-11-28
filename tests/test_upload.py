"""Tests for file upload functionality."""
import io
import pytest
from pathlib import Path
from sqlalchemy import select

from app.models import FileRecord


@pytest.mark.asyncio
async def test_upload_file_success(client, test_db, test_upload_dir, sample_file):
    """Test successful file upload."""
    # Read sample file
    with open(sample_file, "rb") as f:
        file_content = f.read()
    
    # Upload file
    files = {"file": ("test_file.txt", io.BytesIO(file_content), "text/plain")}
    response = await client.post("/api/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "share_code" in data
    assert len(data["share_code"]) == 6
    assert data["filename"] == "test_file.txt"
    assert data["file_size"] == len(file_content)
    assert "upload_time" in data
    assert "expiry_time" in data
    
    # Verify database record
    stmt = select(FileRecord).where(FileRecord.share_code == data["share_code"])
    result = await test_db.execute(stmt)
    record = result.scalar_one_or_none()
    
    assert record is not None
    assert record.original_filename == "test_file.txt"
    assert record.file_size == len(file_content)
    
    # Verify file exists on disk
    file_path = Path(record.file_path)
    assert file_path.exists()
    assert file_path.read_bytes() == file_content


@pytest.mark.asyncio
async def test_upload_file_too_large(client, test_upload_dir):
    """Test upload rejection for oversized files."""
    # Create large file content (> 100MB)
    # Force a small limit for this test to avoid memory issues and ensure failure
    from app.config import settings
    original_limit = settings.max_file_size
    settings.max_file_size = 1024 * 1024  # 1MB
    
    try:
        large_content = b"x" * (2 * 1024 * 1024)  # 2MB
        
        files = {"file": ("large_file.bin", io.BytesIO(large_content), "application/octet-stream")}
        response = await client.post("/api/upload", files=files)
        
        assert response.status_code == 413
        assert "exceeds maximum" in response.json()["detail"]
    finally:
        settings.max_file_size = original_limit


@pytest.mark.asyncio
async def test_upload_filename_sanitization(client, test_db, test_upload_dir):
    """Test XSS protection in filename sanitization."""
    malicious_filename = "<script>alert('xss')</script>test.txt"
    file_content = b"test content"
    
    files = {"file": (malicious_filename, io.BytesIO(file_content), "text/plain")}
    response = await client.post("/api/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    # Filename should be sanitized
    assert "<script>" not in data["filename"]
    # We allow 'alert' text as long as script tags are removed
    assert "alert" in data["filename"]
    assert "xss" in data["filename"]
    
    # Verify in database
    stmt = select(FileRecord).where(FileRecord.share_code == data["share_code"])
    result = await test_db.execute(stmt)
    record = result.scalar_one_or_none()
    
    assert "<script>" not in record.original_filename
    assert "<script>" not in record.filename


@pytest.mark.asyncio
async def test_upload_unique_share_codes(client, test_upload_dir, sample_file):
    """Test that each upload generates a unique share code."""
    with open(sample_file, "rb") as f:
        file_content = f.read()
    
    share_codes = set()
    
    # Upload same file multiple times
    for _ in range(5):
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        response = await client.post("/api/upload", files=files)
        
        assert response.status_code == 200
        share_code = response.json()["share_code"]
        share_codes.add(share_code)
    
    # All share codes should be unique
    assert len(share_codes) == 5


@pytest.mark.asyncio
async def test_upload_stores_client_ip(client, test_db, test_upload_dir, sample_file):
    """Test that uploader IP is stored correctly."""
    with open(sample_file, "rb") as f:
        file_content = f.read()
    
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    response = await client.post("/api/upload", files=files)
    
    assert response.status_code == 200
    share_code = response.json()["share_code"]
    
    # Check database record
    stmt = select(FileRecord).where(FileRecord.share_code == share_code)
    result = await test_db.execute(stmt)
    record = result.scalar_one_or_none()
    
    assert record.uploader_ip is not None
    assert len(record.uploader_ip) > 0


@pytest.mark.asyncio
async def test_upload_date_based_storage(client, test_db, test_upload_dir, sample_file):
    """Test that files are stored in date-based directory structure."""
    with open(sample_file, "rb") as f:
        file_content = f.read()
    
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    response = await client.post("/api/upload", files=files)
    
    assert response.status_code == 200
    share_code = response.json()["share_code"]
    
    # Check file path structure
    stmt = select(FileRecord).where(FileRecord.share_code == share_code)
    result = await test_db.execute(stmt)
    record = result.scalar_one_or_none()
    
    file_path = Path(record.file_path)
    # Path should contain YYYY/MM/DD structure
    assert len(file_path.parts) >= 3
    assert file_path.parts[-4].isdigit()  # Year
    assert file_path.parts[-3].isdigit()  # Month
    assert file_path.parts[-2].isdigit()  # Day
