"""Upload router with progress tracking."""
import os
import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict
from fastapi import APIRouter, UploadFile, File, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import FileRecord
from app.utils.security import sanitize_filename, generate_share_code, get_client_ip
from app.config import settings

router = APIRouter(prefix="/api", tags=["upload"])

# Store upload progress in memory (in production, use Redis)
upload_progress: Dict[str, dict] = {}


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a file and return a share code.
    
    Args:
        file: The uploaded file
        request: Request object to extract IP
        db: Database session
        
    Returns:
        Share code and expiry information
    """
    # Validate file size
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
        )
    
    # Sanitize filename
    original_filename = file.filename or "unnamed"
    safe_filename = sanitize_filename(original_filename)
    
    # Generate unique share code
    while True:
        share_code = generate_share_code()
        stmt = select(FileRecord).where(FileRecord.share_code == share_code)
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            break
    
    # Create date-based directory structure  
    upload_time = datetime.utcnow()
    date_path = upload_time.strftime("%Y/%m/%d")
    upload_dir = Path(settings.upload_dir) / date_path
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Create unique filename to avoid collisions
    timestamp = int(upload_time.timestamp() * 1000)
    stored_filename = f"{timestamp}_{share_code}_{safe_filename}"
    file_path = upload_dir / stored_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Get client IP
    client_ip = get_client_ip(request)
    
    # Create database record
    file_record = FileRecord(
        filename=stored_filename,
        original_filename=safe_filename,
        share_code=share_code,
        uploader_ip=client_ip,
        upload_time=upload_time,
        file_path=str(file_path),
        file_size=file_size
    )
    
    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)
    
    return {
        "success": True,
        "share_code": share_code,
        "filename": safe_filename,
        "file_size": file_size,
        "upload_time": upload_time.isoformat(),
        "expiry_time": file_record.expiry_time.isoformat(),
        "message": f"File uploaded successfully. Share code: {share_code}"
    }


@router.get("/upload/progress/{upload_id}")
async def get_upload_progress(upload_id: str):
    """
    SSE endpoint for upload progress tracking (for future chunked uploads).
    
    Args:
        upload_id: Unique upload identifier
        
    Returns:
        Server-sent events with progress updates
    """
    async def event_generator():
        """Generate SSE events for upload progress."""
        while True:
            if upload_id in upload_progress:
                progress = upload_progress[upload_id]
                yield f"data: {progress}\n\n"
                
                if progress.get("completed", False):
                    del upload_progress[upload_id]
                    break
            else:
                yield f"data: {{'progress': 0, 'status': 'waiting'}}\n\n"
            
            await asyncio.sleep(0.5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
