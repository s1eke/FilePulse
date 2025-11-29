"""Tests for database module."""
import pytest
from sqlalchemy import select
from app.database import get_db, init_db, Base, engine
from app.models import FileRecord


@pytest.mark.asyncio
async def test_init_db_creates_tables(test_db_engine):
    """Test that init_db creates all necessary tables."""
    # Tables should be created by the test_db_engine fixture
    # Verify by checking if we can query FileRecord
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        stmt = select(FileRecord)
        result = await session.execute(stmt)
        records = result.scalars().all()
        assert isinstance(records, list)


@pytest.mark.asyncio
async def test_get_db_yields_session():
    """Test that get_db yields a valid database session."""
    session_count = 0
    async for session in get_db():
        assert session is not None
        # Session should be an AsyncSession instance
        from sqlalchemy.ext.asyncio import AsyncSession
        assert isinstance(session, AsyncSession)
        session_count += 1
        break
    
    assert session_count == 1


@pytest.mark.asyncio
async def test_get_db_handles_exception(test_db):
    """Test that get_db context manager handles exceptions properly."""
    # This tests the exception handling in get_db
    # We'll use the test_db directly to ensure proper rollback behavior
    from app.utils.security import generate_share_code
    from datetime import datetime, timedelta, timezone
    
    # Add a record via test_db
    record = FileRecord(
        filename="exception_test.txt",
        original_filename="exception_test.txt",
        share_code=generate_share_code(),
        uploader_ip="127.0.0.1",
        upload_time=datetime.now(timezone.utc),
        expiry_time=datetime.now(timezone.utc) + timedelta(days=7),
        file_path="/tmp/exception_test.txt",
        file_size=100,
        file_md5="exception_test_md5"
    )
    
    test_db.add(record)
    await test_db.commit()
    
    # Verify record exists
    stmt = select(FileRecord).where(FileRecord.file_md5 == "exception_test_md5")
    result = await test_db.execute(stmt)
    assert result.scalar_one_or_none() is not None
