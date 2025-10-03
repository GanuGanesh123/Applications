"""
Security utilities and authentication.
"""
import hashlib
import secrets
from typing import Optional
from fastapi import HTTPException, status
from app.core.config import settings


def generate_file_hash(content: str) -> str:
    """Generate a hash for file content to prevent duplicates."""
    return hashlib.sha256(content.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def validate_youtube_url(url: str) -> bool:
    """Validate if the provided URL is a valid YouTube URL."""
    youtube_domains = [
        "youtube.com",
        "www.youtube.com",
        "youtu.be",
        "m.youtube.com"
    ]
    
    return any(domain in url.lower() for domain in youtube_domains)


def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    if not validate_youtube_url(url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid YouTube URL provided"
        )
    
    # Handle different URL formats
    if "youtu.be/" in url:
        # Short URL format: https://youtu.be/VIDEO_ID
        video_id = url.split("youtu.be/")[1].split("?")[0].split("&")[0]
    elif "watch?v=" in url:
        # Standard URL format: https://www.youtube.com/watch?v=VIDEO_ID
        video_id = url.split("v=")[1].split("&")[0]
    elif "embed/" in url:
        # Embed URL format: https://www.youtube.com/embed/VIDEO_ID
        video_id = url.split("embed/")[1].split("?")[0]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to extract video ID from URL"
        )
    
    if not video_id or len(video_id) != 11:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid YouTube video ID"
        )
    
    return video_id


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system storage."""
    # Remove or replace dangerous characters
    dangerous_chars = '<>:"/\\|?*'
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename.strip()
