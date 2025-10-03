"""
Main FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.utils.logging_config import setup_logging
from app.utils.exceptions import TranscriptAPIException
from app.api.routes import transcripts_router, health_router, files_router

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Output directory: {settings.output_directory}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    YouTube Transcript API - Extract and convert YouTube video transcripts to various formats.
    
    ## Features
    
    * Extract transcripts from YouTube videos
    * Support for multiple languages
    * Export to TXT, PDF, and JSON formats
    * Background processing for large videos
    * File management and cleanup
    * Health monitoring and system status
    
    ## Usage
    
    1. **Quick Transcript**: Use `/api/v1/transcripts/quick` for immediate text extraction
    2. **Full Processing**: Use `/api/v1/transcripts/` to generate files with metadata
    3. **Async Processing**: Use `/api/v1/transcripts/async` for background processing
    4. **File Management**: Use `/api/v1/files/` endpoints to manage generated files
    
    ## Rate Limits
    
    * 50 requests per hour per IP address
    * Larger videos may take longer to process
    
    ## Supported URLs
    
    * https://www.youtube.com/watch?v=VIDEO_ID
    * https://youtu.be/VIDEO_ID
    * https://m.youtube.com/watch?v=VIDEO_ID
    * https://www.youtube.com/embed/VIDEO_ID
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)


# Custom exception handlers
@app.exception_handler(TranscriptAPIException)
async def transcript_api_exception_handler(request: Request, exc: TranscriptAPIException):
    """Handle custom transcript API exceptions."""
    logger.error(f"TranscriptAPIException: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": exc.errors()
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred" if not settings.debug else str(exc),
            "status_code": 500
        }
    )


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(
    transcripts_router,
    prefix=settings.api_v1_prefix
)

app.include_router(
    health_router,
    prefix=settings.api_v1_prefix
)

app.include_router(
    files_router,
    prefix=settings.api_v1_prefix
)


# Root endpoint
@app.get("/", response_model=Dict[str, Any])
async def root() -> Dict[str, Any]:
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "YouTube Transcript API - Extract and convert video transcripts",
        "docs_url": "/docs",
        "health_check": "/api/v1/health",
        "endpoints": {
            "transcripts": "/api/v1/transcripts",
            "files": "/api/v1/files",
            "health": "/api/v1/health"
        }
    }


# Additional metadata endpoint
@app.get("/info", response_model=Dict[str, Any])
async def app_info() -> Dict[str, Any]:
    """Get detailed application information."""
    return {
        "application": {
            "name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug
        },
        "configuration": {
            "output_directory": settings.output_directory,
            "max_file_size_mb": settings.max_file_size // (1024 * 1024),
            "default_languages": settings.default_languages,
            "pdf_settings": {
                "page_size": settings.pdf_page_size,
                "font_size": settings.pdf_font_size,
                "margins": settings.pdf_margins
            }
        },
        "features": [
            "YouTube transcript extraction",
            "Multiple output formats (TXT, PDF, JSON)",
            "Multi-language support",
            "Background processing",
            "File management",
            "Health monitoring"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
