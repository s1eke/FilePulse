"""Download router with progress tracking."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import FileRecord

router = APIRouter(prefix="/api", tags=["download"])

# Store download progress in memory
download_progress: Dict[str, dict] = {}


@router.get("/file/{share_code}")
async def get_file_info(
    share_code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get file information by share code.
    
    Args:
        share_code: The share code for the file
        db: Database session
        
    Returns:
        File metadata
    """
    # Query file record
    stmt = select(FileRecord).where(FileRecord.share_code == share_code)
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if file is expired
    # Check if file is expired
    expiry_check = file_record.expiry_time
    if expiry_check.tzinfo is None:
        expiry_check = expiry_check.replace(tzinfo=timezone.utc)
        
    if expiry_check < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="File has expired")
    
    # Check if file exists on disk
    file_path = Path(file_record.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")
    
    return {
        "filename": file_record.original_filename,
        "file_size": file_record.file_size,
        "upload_time": file_record.upload_time.isoformat(),
        "expiry_time": file_record.expiry_time.isoformat(),
        "share_code": share_code
    }


@router.get("/download/{share_code}")
async def download_file(
    share_code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Download file by share code with streaming.
    
    Args:
        share_code: The share code for the file
        db: Database session
        
    Returns:
        File download stream
    """
    # Query file record
    stmt = select(FileRecord).where(FileRecord.share_code == share_code)
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if file is expired
    expiry_check = file_record.expiry_time
    if expiry_check.tzinfo is None:
        expiry_check = expiry_check.replace(tzinfo=timezone.utc)
        
    if expiry_check < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="File has expired")
    
    # Check if file exists on disk
    file_path = Path(file_record.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")
    
    # Stream file with progress tracking
    def iterfile():
        """Iterator to stream file in chunks."""
        chunk_size = 64 * 1024  # 64KB chunks
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk
    
    # Return file as streaming response
    return StreamingResponse(
        iterfile(),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{file_record.original_filename}"',
            "Content-Length": str(file_record.file_size)
        }
    )


@router.get("/download/progress/{download_id}")
async def get_download_progress(download_id: str):
    """
    SSE endpoint for download progress tracking.
    
    Args:
        download_id: Unique download identifier
        
    Returns:
        Server-sent events with progress updates
    """
    async def event_generator():
        """Generate SSE events for download progress."""
        while True:
            if download_id in download_progress:
                progress = download_progress[download_id]
                yield f"data: {progress}\n\n"
                
                if progress.get("completed", False):
                    del download_progress[download_id]
                    break
            else:
                yield f"data: {{'progress': 0, 'status': 'waiting'}}\n\n"
            
            await asyncio.sleep(0.5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
