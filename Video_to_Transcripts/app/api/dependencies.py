"""
FastAPI dependencies for the application.
"""
from fastapi import Depends, HTTPException, status, Query
from typing import Optional, List
import logging

from app.services.transcription_service import TranscriptionService
from app.services.video_service import VideoService
from app.services.storage_service import StorageService
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_transcription_service() -> TranscriptionService:
    """Dependency to get transcription service instance."""
    return TranscriptionService()


def get_video_service() -> VideoService:
    """Dependency to get video service instance."""
    return VideoService()


def get_storage_service() -> StorageService:
    """Dependency to get storage service instance."""
    return StorageService()


def validate_pagination(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return")
) -> dict:
    """Validate pagination parameters."""
    return {"skip": skip, "limit": limit}


def validate_file_format(
    format: Optional[str] = Query(None, description="File format filter")
) -> Optional[str]:
    """Validate file format parameter."""
    valid_formats = ["txt", "pdf", "json"]
    if format and format.lower() not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}"
        )
    return format.lower() if format else None


def validate_languages(
    languages: Optional[str] = Query(
        None, 
        description="Comma-separated list of language codes (e.g., 'en,es,fr')"
    )
) -> List[str]:
    """Validate and parse language codes."""
    if not languages:
        return settings.default_languages
    
    lang_list = [lang.strip() for lang in languages.split(",")]
    
    # Basic validation - you could add more sophisticated language code validation
    for lang in lang_list:
        if not lang or len(lang) > 10:  # Basic sanity check
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid language code: {lang}"
            )
    
    return lang_list


class RateLimiter:
    """Simple in-memory rate limiter for demonstration."""
    
    def __init__(self, max_requests: int = 100, window_minutes: int = 60):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self._requests = {}  # In production, use Redis or similar
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for client."""
        import time
        
        now = time.time()
        window_start = now - (self.window_minutes * 60)
        
        # Clean old entries
        if client_id in self._requests:
            self._requests[client_id] = [
                req_time for req_time in self._requests[client_id]
                if req_time > window_start
            ]
        else:
            self._requests[client_id] = []
        
        # Check if under limit
        if len(self._requests[client_id]) >= self.max_requests:
            return False
        
        # Add current request
        self._requests[client_id].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=50, window_minutes=60)


def check_rate_limit(client_ip: str = None) -> bool:
    """Dependency to check rate limiting."""
    if not client_ip:
        client_ip = "default"  # In production, get from request
    
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    return True


def get_app_info() -> dict:
    """Get application information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug
    }
