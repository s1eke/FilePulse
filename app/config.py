"""Application configuration using Pydantic settings."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    upload_dir: str = "./uploads"
    database_url: str = "sqlite+aiosqlite:///./filepulse.db"
    max_file_size: int = 104857600  # 100MB
    enable_docs: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # File expiry (days)
    file_expiry_days: int = 7
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
