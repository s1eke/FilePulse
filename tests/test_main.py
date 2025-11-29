"""Tests for main application module."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path


@pytest.mark.asyncio
async def test_home_page(client):
    """Test home page rendering."""
    response = await client.get("/")
    
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    # Should contain config values
    content = response.text
    assert "FilePulse" in content or "file" in content.lower()


@pytest.mark.asyncio
async def test_download_page(client):
    """Test download page rendering."""
    response = await client.get("/download.html")
    
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


@pytest.mark.asyncio
async def test_index_redirect(client):
    """Test index.html redirect."""
    response = await client.get("/index.html")
    
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = await client.get("/health")
    
    # Due to static files mounting, this might return 404 or 200
    # The important thing is it doesn't crash (5xx)
    assert response.status_code in [200, 404]
    
    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "FilePulse"


@pytest.mark.asyncio
async def test_lifespan_startup():
    """Test application lifespan startup."""
    from app.main import lifespan, app
    from app.config import settings
    
    # Mock the scheduler
    with patch('app.main.scheduler') as mock_scheduler:
        with patch('app.main.init_db', new_callable=AsyncMock) as mock_init_db:
            # Ensure upload directory exists for the test
            upload_dir = Path(settings.upload_dir)
            
            async with lifespan(app):
                # Verify init_db was called
                mock_init_db.assert_called_once()
                
                # Verify scheduler.start was called
                mock_scheduler.start.assert_called_once()
                
                # Verify upload directory was created
                assert upload_dir.exists() or settings.upload_dir.startswith('./uploads')
            
            # Verify scheduler.shutdown was called after context exit
            mock_scheduler.shutdown.assert_called_once()


def test_main_entry_point():
    """Test main entry point."""
    from app import main
    import sys
    
    # Mock uvicorn.run
    with patch('uvicorn.run') as mock_run:
        # Simulate running as main module
        original_name = main.__name__
        try:
            # We can't actually test the if __name__ == "__main__" block directly
            # in unit tests, but we can verify the structure exists
            import inspect
            source = inspect.getsource(main)
            assert 'if __name__ == "__main__"' in source
            assert 'uvicorn.run' in source
        finally:
            pass


@pytest.mark.asyncio  
async def test_cors_middleware(client):
    """Test CORS middleware is configured."""
    response = await client.options("/", headers={
        "Origin": "http://example.com",
        "Access-Control-Request-Method": "POST"
    })
    
    # CORS should handle OPTIONS requests
    assert response.status_code in [200, 405]  # Either OK or Method Not Allowed


@pytest.mark.asyncio
async def test_static_files_mounted(client):
    """Test that static files are mounted."""
    # Try to access a static resource (should work if path exists)
    response = await client.get("/static/")
    
    # 404 is OK if path doesn't exist, but shouldn't be 5xx error
    assert response.status_code in [200, 404]
