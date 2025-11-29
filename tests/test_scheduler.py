"""Tests for file cleanup scheduler."""
import pytest
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from app.models import FileRecord
from app.utils.scheduler import FileCleanupScheduler
from sqlalchemy import select


@pytest.mark.asyncio
async def test_cleanup_expired_files(test_db, test_upload_dir):
    """Test that expired files are removed."""
    from app.utils.security import generate_share_code
    
    # Create expired file
    expired_code = generate_share_code()
    expired_path = test_upload_dir / "expired.txt"
    expired_path.write_text("expired content")
    
    expired_record = FileRecord(
        filename="expired.txt",
        original_filename="expired.txt",
        share_code=expired_code,
        uploader_ip="127.0.0.1",
        upload_time=datetime.now(timezone.utc) - timedelta(days=10),
        expiry_time=datetime.now(timezone.utc) - timedelta(days=3),
        file_path=str(expired_path),
        file_size=15,
        file_md5="dummy_md5_expired"
    )
    
    test_db.add(expired_record)
    await test_db.commit()
    
    # Create valid file
    valid_code = generate_share_code()
    valid_path = test_upload_dir / "valid.txt"
    valid_path.write_text("valid content")
    
    valid_record = FileRecord(
        filename="valid.txt",
        original_filename="valid.txt",
        share_code=valid_code,
        uploader_ip="127.0.0.1",
        upload_time=datetime.now(timezone.utc),
        expiry_time=datetime.now(timezone.utc) + timedelta(days=7),
        file_path=str(valid_path),
        file_size=13,
        file_md5="dummy_md5_valid"
    )
    
    test_db.add(valid_record)
    await test_db.commit()
    
    # Run cleanup with test session
    scheduler = FileCleanupScheduler()
    await scheduler.cleanup_expired_files(test_db)
    
    # Refresh session to see changes
    await test_db.commit()
    test_db.expire_all()
    
    # Check expired file is deleted
    stmt = select(FileRecord).where(FileRecord.share_code == expired_code)
    result = await test_db.execute(stmt)
    assert result.scalar_one_or_none() is None
    assert not expired_path.exists()
    
    # Check valid file still exists
    stmt = select(FileRecord).where(FileRecord.share_code == valid_code)
    result = await test_db.execute(stmt)
    assert result.scalar_one_or_none() is not None
    assert valid_path.exists()


@pytest.mark.asyncio
async def test_cleanup_missing_physical_file(test_db, test_upload_dir):
    """Test cleanup handles missing physical files gracefully."""
    from app.utils.security import generate_share_code
    
    share_code = generate_share_code()
    
    # Create record but not physical file
    record = FileRecord(
        filename="missing.txt",
        original_filename="missing.txt",
        share_code=share_code,
        uploader_ip="127.0.0.1",
        upload_time=datetime.now(timezone.utc) - timedelta(days=10),
        expiry_time=datetime.now(timezone.utc) - timedelta(days=3),
        file_path=str(test_upload_dir / "missing.txt"),
        file_size=10,
        file_md5="dummy_md5_missing"
    )
    
    test_db.add(record)
    await test_db.commit()
    
    # Run cleanup (should not raise error)
    scheduler = FileCleanupScheduler()
    await scheduler.cleanup_expired_files(test_db)
    
    # Record should still be deleted
    await test_db.commit()
    test_db.expire_all()
    stmt = select(FileRecord).where(FileRecord.share_code == share_code)
    result = await test_db.execute(stmt)
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_cleanup_preserves_non_expired(test_db, test_upload_dir):
    """Test that non-expired files are preserved."""
    from app.utils.security import generate_share_code
    
    # Create multiple non-expired files
    codes = []
    for i in range(3):
        code = generate_share_code()
        codes.append(code)
        
        file_path = test_upload_dir / f"file_{i}.txt"
        file_path.write_text(f"content {i}")
        
        record = FileRecord(
            filename=f"file_{i}.txt",
            original_filename=f"file_{i}.txt",
            share_code=code,
            uploader_ip="127.0.0.1",
            upload_time=datetime.now(timezone.utc),
            expiry_time=datetime.now(timezone.utc) + timedelta(days=7),
            file_path=str(file_path),
            file_size=len(f"content {i}"),
            file_md5=f"dummy_md5_{i}"
        )
        
        test_db.add(record)
    
    await test_db.commit()
    
    # Run cleanup
    scheduler = FileCleanupScheduler()
    await scheduler.cleanup_expired_files(test_db)
    
    # All files should still exist
    await test_db.commit()
    for code in codes:
        stmt = select(FileRecord).where(FileRecord.share_code == code)
        result = await test_db.execute(stmt)
        assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_cleanup_md5_deduplication(test_db, test_upload_dir):
    """Test that cleanup respects MD5 deduplication."""
    from app.utils.security import generate_share_code
    
    # Create file
    file_path = test_upload_dir / "shared.txt"
    file_path.write_text("shared content")
    shared_md5 = "shared_md5_hash"
    
    # Create two records sharing the same file (via MD5)
    # One expired, one not expired
    expired_code = generate_share_code()
    expired_record = FileRecord(
        filename="shared.txt",
        original_filename="shared.txt",
        share_code=expired_code,
        uploader_ip="127.0.0.1",
        upload_time=datetime.now(timezone.utc) - timedelta(days=10),
        expiry_time=datetime.now(timezone.utc) - timedelta(days=3),
        file_path=str(file_path),
        file_size=14,
        file_md5=shared_md5
    )
    
    valid_code = generate_share_code()
    valid_record = FileRecord(
        filename="shared.txt",
        original_filename="shared.txt",
        share_code=valid_code,
        uploader_ip="127.0.0.1",
        upload_time=datetime.now(timezone.utc),
        expiry_time=datetime.now(timezone.utc) + timedelta(days=7),
        file_path=str(file_path),
        file_size=14,
        file_md5=shared_md5
    )
    
    test_db.add(expired_record)
    test_db.add(valid_record)
    await test_db.commit()
    
    # Run cleanup
    scheduler = FileCleanupScheduler()
    await scheduler.cleanup_expired_files(test_db)
    
    await test_db.commit()
    test_db.expire_all()
    
    # Expired record should be deleted
    stmt = select(FileRecord).where(FileRecord.share_code == expired_code)
    result = await test_db.execute(stmt)
    assert result.scalar_one_or_none() is None
    
    # Valid record should still exist
    stmt = select(FileRecord).where(FileRecord.share_code == valid_code)
    result = await test_db.execute(stmt)
    assert result.scalar_one_or_none() is not None
    
    # Physical file should still exist (because valid record references it)
    assert file_path.exists()


def test_scheduler_initialization():
    """Test scheduler initialization."""
    scheduler = FileCleanupScheduler()
    
    # Should have a scheduler instance
    assert scheduler.scheduler is not None
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    assert isinstance(scheduler.scheduler, AsyncIOScheduler)
    
    # Scheduler should not be running initially
    assert not scheduler.scheduler.running
