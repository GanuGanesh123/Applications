"""
Application configuration settings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "YouTube Transcript API"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # API
    api_v1_prefix: str = "/api/v1"
    allowed_hosts: List[str] = ["*"]
    
    # File Storage
    output_directory: str = Field(default="./outputs", env="OUTPUT_DIR")
    max_file_size: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    
    # YouTube API Settings
    default_languages: List[str] = ["en", "en-US", "en-GB"]
    max_transcript_length: int = Field(default=1000000, env="MAX_TRANSCRIPT_LENGTH")  # 1MB
    
    # PDF Settings
    pdf_page_size: str = "A4"
    pdf_font_size: int = 11
    pdf_margins: int = 72  # Points (1 inch)
    
    # Celery (for background tasks)
    celery_broker_url: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    # Database (optional)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure output directory exists
        os.makedirs(self.output_directory, exist_ok=True)


# Global settings instance
settings = Settings()
