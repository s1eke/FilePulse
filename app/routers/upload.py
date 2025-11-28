"""Upload router with progress tracking and MD5 deduplication."""
import os
import asyncio
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict
from fastapi import APIRouter, UploadFile, File, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database import get_db
from app.models import FileRecord
from app.utils.security import sanitize_filename, generate_share_code, get_client_ip
from app.utils.file_utils import calculate_md5_from_bytes
from app.config import settings

logger = logging.getLogger(__name__)

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
    
    # Debug logging
    if settings.debug:
        logger.info(f"[DEBUG] Upload attempt - Filename: {file.filename}")
        logger.info(f"[DEBUG] File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
        logger.info(f"[DEBUG] Max allowed: {settings.max_file_size:,} bytes ({settings.max_file_size / 1024 / 1024:.2f} MB)")
        logger.info(f"[DEBUG] Size check: {file_size} {'<=' if file_size <= settings.max_file_size else '>'} {settings.max_file_size}")
    
    if file_size > settings.max_file_size:
        # Format the limit in a human-readable way
        limit_mb = settings.max_file_size / (1024 * 1024)
        error_msg = f"File size exceeds maximum allowed size of {limit_mb:.0f}MB ({settings.max_file_size} bytes)"
        
        if settings.debug:
            logger.warning(f"[DEBUG] Upload rejected: {error_msg}")
            logger.warning(f"[DEBUG] File: {file.filename}, Size: {file_size:,} bytes")
        
        raise HTTPException(
            status_code=413,
            detail=error_msg
        )
    
    # Calculate MD5 hash
    file_md5 = calculate_md5_from_bytes(file_content)
    
    # Check if file with same MD5 already exists
    stmt = select(FileRecord).where(FileRecord.file_md5 == file_md5).order_by(FileRecord.expiry_time.desc())
    result = await db.execute(stmt)
    existing_record = result.scalars().first()
    
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
    
    upload_time = datetime.utcnow()
    expiry_time = upload_time + timedelta(days=settings.file_expiry_days)
    
    # If duplicate exists, reuse the file path
    if existing_record:
        file_path = existing_record.file_path
        stored_filename = existing_record.filename
        
        # Update expiry_time of existing file to the latest
        # This keeps the physical file until ALL shares expire
        if expiry_time > existing_record.expiry_time:
            stmt = update(FileRecord).where(
                FileRecord.file_md5 == file_md5
            ).values(expiry_time=expiry_time)
            await db.execute(stmt)
    else:
        # New file - save it
        date_path = upload_time.strftime("%Y/%m/%d")
        upload_dir = Path(settings.upload_dir) / date_path
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = int(upload_time.timestamp() * 1000)
        stored_filename = f"{timestamp}_{share_code}_{safe_filename}"
        file_path = upload_dir / stored_filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
    
    # Get client IP
    client_ip = get_client_ip(request)
    
    # Create new database record with new share code
    file_record = FileRecord(
        filename=stored_filename,
        original_filename=safe_filename,
        share_code=share_code,
        uploader_ip=client_ip,
        upload_time=upload_time,
        expiry_time=expiry_time,
        file_path=str(file_path),
        file_size=file_size,
        file_md5=file_md5
    )
    
    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)
    
    # Debug logging
    if settings.debug:
        logger.info(f"[DEBUG] Upload successful!")
        logger.info(f"[DEBUG] Share code: {share_code}")
        logger.info(f"[DEBUG] Stored as: {stored_filename}")
        logger.info(f"[DEBUG] MD5: {file_md5}")
        logger.info(f"[DEBUG] Duplicate file: {'Yes' if existing_record else 'No'}")
        logger.info(f"[DEBUG] Uploader IP: {client_ip}")
    
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
