"""Background scheduler for cleaning up expired files."""
import os
import logging
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import FileRecord

logger = logging.getLogger(__name__)


class FileCleanupScheduler:
    """Scheduler for automatic file cleanup."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = AsyncIOScheduler()
    
    async def cleanup_expired_files(self):
        """Remove expired files from database and filesystem.
        
        With MD5 deduplication, only delete physical file if no other
        active shares reference the same file.
        """
        logger.info("Starting expired file cleanup task")
        
        async with AsyncSessionLocal() as session:
            try:
                # Query for expired files
                now = datetime.utcnow()
                stmt = select(FileRecord).where(FileRecord.expiry_time < now)
                result = await session.execute(stmt)
                expired_files = result.scalars().all()
                
                deleted_count = 0
                files_to_delete = set()  # Track unique file paths to delete
                
                for file_record in expired_files:
                    try:
                        # Check if other non-expired records share the same file
                        stmt_check = select(FileRecord).where(
                            FileRecord.file_md5 == file_record.file_md5,
                            FileRecord.expiry_time >= now,
                            FileRecord.id != file_record.id
                        )
                        check_result = await session.execute(stmt_check)
                        other_shares = check_result.scalars().first()
                        
                        # Only mark for physical deletion if no other shares exist
                        if not other_shares:
                            files_to_delete.add(file_record.file_path)
                        
                        # Always delete the database record
                        await session.delete(file_record)
                        deleted_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing file {file_record.filename}: {e}")
                        continue
                
                # Delete physical files
                for file_path in files_to_delete:
                    try:
                        file_path_obj = Path(file_path)
                        if file_path_obj.exists():
                            file_path_obj.unlink()
                            logger.info(f"Deleted physical file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting physical file {file_path}: {e}")
                
                await session.commit()
                logger.info(f"Cleanup completed. Deleted {deleted_count} expired records, {len(files_to_delete)} physical files")
                
            except Exception as e:
                logger.error(f"Error during file cleanup: {e}")
                await session.rollback()
    
    def start(self):
        """Start the scheduler with daily cleanup job."""
        # Run cleanup every day at 2 AM
        self.scheduler.add_job(
            self.cleanup_expired_files,
            'cron',
            hour=2,
            minute=0,
            id='file_cleanup',
            replace_existing=True
        )
        
        # Also run cleanup on startup
        self.scheduler.add_job(
            self.cleanup_expired_files,
            'date',
            run_date=datetime.now(),
            id='file_cleanup_startup'
        )
        
        self.scheduler.start()
        logger.info("File cleanup scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        self.scheduler.shutdown()
        logger.info("File cleanup scheduler stopped")


# Global scheduler instance
scheduler = FileCleanupScheduler()
