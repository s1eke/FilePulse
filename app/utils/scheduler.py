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
        """Remove expired files from database and filesystem."""
        logger.info("Starting expired file cleanup task")
        
        async with AsyncSessionLocal() as session:
            try:
                # Query for expired files
                now = datetime.utcnow()
                stmt = select(FileRecord).where(FileRecord.expiry_time < now)
                result = await session.execute(stmt)
                expired_files = result.scalars().all()
                
                deleted_count = 0
                for file_record in expired_files:
                    try:
                        # Delete physical file
                        file_path = Path(file_record.file_path)
                        if file_path.exists():
                            file_path.unlink()
                            logger.info(f"Deleted expired file: {file_path}")
                        
                        # Delete database record
                        await session.delete(file_record)
                        deleted_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error deleting file {file_record.filename}: {e}")
                        continue
                
                await session.commit()
                logger.info(f"Cleanup completed. Deleted {deleted_count} expired files")
                
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
