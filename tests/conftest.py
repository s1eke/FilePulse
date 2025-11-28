"""Pytest configuration and shared fixtures."""
import os
import asyncio
from pathlib import Path
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import Base, get_db
from app.config import settings


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_filepulse.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()
    
    # Clean up database file
    db_file = Path("./test_filepulse.db")
    if db_file.exists():
        db_file.unlink()


@pytest_asyncio.fixture(scope="function")
async def test_db(test_db_engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_db):
    """Create test client with database override."""
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_upload_dir(tmp_path):
    """Create temporary upload directory."""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    
    # Override settings
    original_upload_dir = settings.upload_dir
    settings.upload_dir = str(upload_dir)
    
    yield upload_dir
    
    # Restore original settings
    settings.upload_dir = original_upload_dir


@pytest.fixture
def sample_file(tmp_path):
    """Create a sample file for testing."""
    file_path = tmp_path / "test_file.txt"
    file_content = b"This is a test file content for FilePulse testing."
    file_path.write_bytes(file_content)
    return file_path
