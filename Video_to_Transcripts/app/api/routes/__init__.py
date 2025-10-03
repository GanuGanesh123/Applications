"""
API routes package.
"""
from .transcripts import router as transcripts_router
from .health import router as health_router
from .files import router as files_router

__all__ = ["transcripts_router", "health_router", "files_router"]
