"""Database models for file records."""
from datetime import datetime, timedelta
from sqlalchemy import String, Integer, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.config import settings


class FileRecord(Base):
    """Model for uploaded file records."""
    
    __tablename__ = "file_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    share_code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False, index=True)
    uploader_ip: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv6 max length
    upload_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expiry_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Index on expiry_time for efficient cleanup queries
    __table_args__ = (
        Index('idx_expiry_time', 'expiry_time'),
    )
    
    def __init__(self, **kwargs):
        """Initialize file record with auto-calculated expiry time."""
        if 'expiry_time' not in kwargs and 'upload_time' in kwargs:
            kwargs['expiry_time'] = kwargs['upload_time'] + timedelta(days=settings.file_expiry_days)
        elif 'expiry_time' not in kwargs:
            upload_time = datetime.utcnow()
            kwargs['upload_time'] = upload_time
            kwargs['expiry_time'] = upload_time + timedelta(days=settings.file_expiry_days)
        super().__init__(**kwargs)
