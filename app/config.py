"""Application configuration using Pydantic settings."""
import os
import re
from typing import Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Environment variables take precedence over .env file
        env_prefix=""
    )
    
    # Application settings
    upload_dir: str = "./uploads"
    database_url: str = "sqlite+aiosqlite:///./filepulse.db"
    max_file_size: Union[str, int] = "100MB"  # Support units: 100MB, 1GB, etc.
    enable_docs: bool = False
    debug: bool = False  # Enable detailed debug logging
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # File expiry (days)
    file_expiry_days: int = 7
    
    @field_validator('max_file_size', mode='before')
    @classmethod
    def parse_file_size(cls, v):
        """Parse file size with units (MB, GB) to bytes.
        
        Priority: Environment variable > .env file > default value
        """
        # If already an integer, return as-is
        if isinstance(v, int):
            return v
        
        # Convert to string and parse
        v_str = str(v).strip().upper()
        
        # Match number and optional unit
        match = re.match(r'^(\d+(?:\.\d+)?)\s*(B|KB|MB|GB)?$', v_str)
        if not match:
            raise ValueError(f"Invalid file size format: {v}. Use formats like: 100MB, 1GB, 500MB")
        
        size = float(match.group(1))
        unit = match.group(2) or 'B'
        
        units = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3
        }
        
        return int(size * units[unit])


settings = Settings()
