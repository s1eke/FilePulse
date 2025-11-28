"""Tests for file download functionality."""
import io
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy import select

from app.models import FileRecord


@pytest.mark.asyncio
async def test_get_file_info_success(client, test_db, test_upload_dir, sample_file):
    """Test retrieving file information with valid share code."""
    # First upload a file
    with open(sample_file, "rb") as f:
        file_content = f.read()
    
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    upload_response = await client.post("/api/upload", files=files)
    share_code = upload_response.json()["share_code"]
    
    # Get file info
    response = await client.get(f"/api/file/{share_code}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["filename"] == "test.txt"
    assert data["file_size"] == len(file_content)
    assert data["share_code"] == share_code
    assert "upload_time" in data
    assert "expiry_time" in data


@pytest.mark.asyncio
async def test_get_file_info_invalid_code(client):
    """Test file info retrieval with invalid share code."""
    response = await client.get("/api/file/INVALID")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_file_info_expired(client, test_db, test_upload_dir):
    """Test file info retrieval for expired file."""
    # Create expired file record manually
    from app.utils.security import generate_share_code
    
    share_code = generate_share_code()
    upload_time = datetime.utcnow() - timedelta(days=10)
    expiry_time = upload_time + timedelta(days=7)
    
    # Create file
    file_path = test_upload_dir / "expired_test.txt"
    file_path.write_text("expired content")
    
    record = FileRecord(
        filename="expired_test.txt",
        original_filename="expired_test.txt",
        share_code=share_code,
        uploader_ip="127.0.0.1",
        upload_time=upload_time,
        expiry_time=expiry_time,
        file_path=str(file_path),
        file_size=15
    )
    
    test_db.add(record)
    await test_db.commit()
    
    # Try to get info
    response = await client.get(f"/api/file/{share_code}")
    
    assert response.status_code == 410
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_download_file_success(client, test_db, test_upload_dir, sample_file):
    """Test successful file download."""
    # Upload file
    with open(sample_file, "rb") as f:
        file_content = f.read()
    
    files = {"file": ("test_download.txt", io.BytesIO(file_content), "text/plain")}
    upload_response = await client.post("/api/upload", files=files)
    share_code = upload_response.json()["share_code"]
    
    # Download file
    response = await client.get(f"/api/download/{share_code}")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert 'attachment; filename="test_download.txt"' in response.headers["content-disposition"]
    assert await response.aread() == file_content


@pytest.mark.asyncio
async def test_download_file_preserves_filename(client, test_db, test_upload_dir, sample_file):
    """Test that download preserves original filename."""
    original_filename = "my_important_doc.txt"
    
    with open(sample_file, "rb") as f:
        file_content = f.read()
    
    files = {"file": (original_filename, io.BytesIO(file_content), "text/plain")}
    upload_response = await client.post("/api/upload", files=files)
    share_code = upload_response.json()["share_code"]
    
    # Download
    response = await client.get(f"/api/download/{share_code}")
    
    assert response.status_code == 200
    assert f'filename="{original_filename}"' in response.headers["content-disposition"]


@pytest.mark.asyncio
async def test_download_invalid_code(client):
    """Test download with invalid share code."""
    response = await client.get("/api/download/INVALID")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_download_expired_file(client, test_db, test_upload_dir):
    """Test download of expired file."""
    from app.utils.security import generate_share_code
    
    share_code = generate_share_code()
    upload_time = datetime.utcnow() - timedelta(days=10)
    expiry_time = upload_time + timedelta(days=7)
    
    # Create file
    file_path = test_upload_dir / "expired.txt"
    file_path.write_text("expired")
    
    record = FileRecord(
        filename="expired.txt",
        original_filename="expired.txt",
        share_code=share_code,
        uploader_ip="127.0.0.1",
        upload_time=upload_time,
        expiry_time=expiry_time,
        file_path=str(file_path),
        file_size=7
    )
    
    test_db.add(record)
    await test_db.commit()
    
    # Try to download
    response = await client.get(f"/api/download/{share_code}")
    
    assert response.status_code == 410
    assert "expired" in (await response.json())["detail"].lower()
