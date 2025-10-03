"""
Pydantic models for transcript-related operations.
"""
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class FileFormat(str, Enum):
    """Supported output file formats."""
    TXT = "txt"
    PDF = "pdf"
    JSON = "json"
    BOTH = "both"  # txt and pdf


class TranscriptStatus(str, Enum):
    """Status of transcript processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoInfo(BaseModel):
    """Information about the YouTube video."""
    video_id: str
    url: str
    title: Optional[str] = None
    duration: Optional[int] = None  # in seconds
    language: Optional[str] = None


class TranscriptRequest(BaseModel):
    """Request model for transcript generation."""
    url: HttpUrl = Field(..., description="YouTube video URL")
    format: FileFormat = Field(default=FileFormat.BOTH, description="Output format")
    languages: Optional[List[str]] = Field(
        default=["en", "en-US", "en-GB"], 
        description="Preferred languages in order of priority"
    )
    preserve_formatting: bool = Field(
        default=False, 
        description="Whether to preserve HTML formatting in transcript"
    )
    custom_filename: Optional[str] = Field(
        default=None, 
        description="Custom filename (without extension)"
    )

    @validator('languages')
    def validate_languages(cls, v):
        if not v or len(v) == 0:
            return ["en"]
        return v

    @validator('url')
    def validate_youtube_url(cls, v):
        url_str = str(v)
        youtube_domains = ["youtube.com", "youtu.be", "m.youtube.com"]
        if not any(domain in url_str.lower() for domain in youtube_domains):
            raise ValueError("Must be a valid YouTube URL")
        return v


class TranscriptSnippet(BaseModel):
    """Individual transcript snippet."""
    text: str
    start: float  # Start time in seconds
    duration: float  # Duration in seconds


class TranscriptData(BaseModel):
    """Complete transcript data."""
    video_info: VideoInfo
    snippets: List[TranscriptSnippet]
    full_text: str
    language: str
    is_generated: bool
    word_count: int
    duration_seconds: float


class FileOutput(BaseModel):
    """Information about generated output file."""
    filename: str
    format: FileFormat
    size_bytes: int
    file_path: str
    download_url: Optional[str] = None


class TranscriptResponse(BaseModel):
    """Response model for transcript generation."""
    task_id: str = Field(..., description="Unique task identifier")
    status: TranscriptStatus
    video_info: VideoInfo
    transcript_data: Optional[TranscriptData] = None
    files: List[FileOutput] = Field(default_factory=list)
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None


class TranscriptTaskStatus(BaseModel):
    """Status check response for background tasks."""
    task_id: str
    status: TranscriptStatus
    progress: int = Field(default=0, ge=0, le=100)  # Percentage
    message: Optional[str] = None
    result: Optional[TranscriptResponse] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    task_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
