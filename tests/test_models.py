"""Tests for database models."""
import pytest
from datetime import datetime, timedelta, timezone
from app.models import FileRecord
from app.config import settings


def test_file_record_with_explicit_times():
    """Test FileRecord creation with explicit times."""
    upload_time = datetime.now(timezone.utc)
    expiry_time = upload_time + timedelta(days=10)
    
    record = FileRecord(
        filename="test.txt",
        original_filename="test.txt",
        share_code="ABC123",
        uploader_ip="192.168.1.1",
        upload_time=upload_time,
        expiry_time=expiry_time,
        file_path="/tmp/test.txt",
        file_size=1024,
        file_md5="abc123def456"
    )
    
    assert record.upload_time == upload_time
    assert record.expiry_time == expiry_time


def test_file_record_auto_expiry_with_upload_time():
    """Test FileRecord auto-calculates expiry when upload_time provided."""
    upload_time = datetime.now(timezone.utc)
    
    record = FileRecord(
        filename="test.txt",
        original_filename="test.txt",
        share_code="ABC123",
        uploader_ip="192.168.1.1",
        upload_time=upload_time,
        file_path="/tmp/test.txt",
        file_size=1024,
        file_md5="abc123def456"
    )
    
    expected_expiry = upload_time + timedelta(days=settings.file_expiry_days)
    assert record.upload_time == upload_time
    # Allow 1 second tolerance for test execution time
    assert abs((record.expiry_time - expected_expiry).total_seconds()) < 1


def test_file_record_auto_times_no_times_provided():
    """Test FileRecord auto-generates both times when none provided."""
    before = datetime.now(timezone.utc)
    
    record = FileRecord(
        filename="test.txt",
        original_filename="test.txt",
        share_code="ABC123",
        uploader_ip="192.168.1.1",
        file_path="/tmp/test.txt",
        file_size=1024,
        file_md5="abc123def456"
    )
    
    after = datetime.now(timezone.utc)
    
    # Upload time should be between before and after
    assert before <= record.upload_time <= after
    
    # Expiry time should be file_expiry_days after upload_time
    expected_expiry = record.upload_time + timedelta(days=settings.file_expiry_days)
    assert abs((record.expiry_time - expected_expiry).total_seconds()) < 1
    
    # Check all required fields are set
    assert record.filename == "test.txt"
    assert record.original_filename == "test.txt"
    assert record.share_code == "ABC123"
    assert record.uploader_ip == "192.168.1.1"
    assert record.file_path == "/tmp/test.txt"
    assert record.file_size == 1024
    assert record.file_md5 == "abc123def456"


@pytest.mark.asyncio
async def test_file_record_persistence(test_db):
    """Test that FileRecord can be persisted to database."""
    record = FileRecord(
        filename="persist_test.txt",
        original_filename="persist_test.txt",
        share_code="PERSIST",
        uploader_ip="127.0.0.1",
        file_path="/tmp/persist_test.txt",
        file_size=2048,
        file_md5="persist123"
    )
    
    test_db.add(record)
    await test_db.commit()
    await test_db.refresh(record)
    
    # Verify it has an ID after commit
    assert record.id is not None
    assert record.id > 0
