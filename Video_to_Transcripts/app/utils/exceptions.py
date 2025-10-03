"""
Custom exception classes for the application.
"""


class TranscriptAPIException(Exception):
    """Base exception for transcript API errors."""
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class VideoNotFoundError(TranscriptAPIException):
    """Raised when a YouTube video is not found or inaccessible."""
    
    def __init__(self, video_id: str, message: str = None):
        self.video_id = video_id
        if message is None:
            message = f"Video {video_id} not found or is not accessible"
        super().__init__(message, status_code=404)


class TranscriptNotAvailableError(TranscriptAPIException):
    """Raised when transcript is not available for a video."""
    
    def __init__(self, video_id: str, languages: list = None, message: str = None):
        self.video_id = video_id
        self.languages = languages or []
        if message is None:
            lang_str = ", ".join(self.languages) if self.languages else "any language"
            message = f"Transcript not available for video {video_id} in {lang_str}"
        super().__init__(message, status_code=404)


class FileProcessingError(TranscriptAPIException):
    """Raised when file processing fails."""
    
    def __init__(self, filename: str, operation: str, message: str = None):
        self.filename = filename
        self.operation = operation
        if message is None:
            message = f"Failed to {operation} file {filename}"
        super().__init__(message, status_code=500)


class RateLimitExceededError(TranscriptAPIException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class InvalidURLError(TranscriptAPIException):
    """Raised when an invalid YouTube URL is provided."""
    
    def __init__(self, url: str, message: str = None):
        self.url = url
        if message is None:
            message = f"Invalid YouTube URL: {url}"
        super().__init__(message, status_code=400)
