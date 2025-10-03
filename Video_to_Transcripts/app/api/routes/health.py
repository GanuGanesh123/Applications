"""
Health check and system status routes.
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime
import psutil
import os

from app.api.dependencies import get_app_info
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="Health check",
    description="Basic health check endpoint"
)
async def health_check() -> Dict[str, Any]:
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "YouTube Transcript API"
    }


@router.get(
    "/detailed",
    response_model=Dict[str, Any],
    summary="Detailed health check",
    description="Detailed health check with system information"
)
async def detailed_health_check(
    app_info: dict = Depends(get_app_info)
) -> Dict[str, Any]:
    """Detailed health check with system information."""
    try:
        # System information
        system_info = {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "uptime_seconds": (
                datetime.utcnow() - datetime.fromtimestamp(psutil.boot_time())
            ).total_seconds()
        }
        
        # Check output directory
        output_dir_exists = os.path.exists(settings.output_directory)
        output_dir_writable = (
            os.access(settings.output_directory, os.W_OK) 
            if output_dir_exists else False
        )
        
        # Service status
        service_status = {
            "output_directory": {
                "exists": output_dir_exists,
                "writable": output_dir_writable,
                "path": settings.output_directory
            },
            "youtube_transcript_api": "available",  # Could test actual API
            "pdf_generation": "available"  # Could test reportlab
        }
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "app_info": app_info,
            "system_info": system_info,
            "service_status": service_status,
            "configuration": {
                "max_file_size": settings.max_file_size,
                "default_languages": settings.default_languages,
                "debug_mode": settings.debug
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "app_info": app_info
        }


@router.get(
    "/ready",
    response_model=Dict[str, Any],
    summary="Readiness check",
    description="Check if the service is ready to handle requests"
)
async def readiness_check() -> Dict[str, Any]:
    """Check if the service is ready to handle requests."""
    checks = {}
    all_ready = True
    
    try:
        # Check output directory
        output_dir_ready = (
            os.path.exists(settings.output_directory) and
            os.access(settings.output_directory, os.W_OK)
        )
        checks["output_directory"] = output_dir_ready
        if not output_dir_ready:
            all_ready = False
        
        # Check dependencies (basic import test)
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from reportlab.lib.pagesizes import A4
            checks["dependencies"] = True
        except ImportError as e:
            checks["dependencies"] = False
            checks["dependency_error"] = str(e)
            all_ready = False
        
        return {
            "ready": all_ready,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks
        }
        
    except Exception as e:
        return {
            "ready": False,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "checks": checks
        }


@router.get(
    "/live",
    response_model=Dict[str, str],
    summary="Liveness check",
    description="Simple liveness probe for container orchestration"
)
async def liveness_check() -> Dict[str, str]:
    """Simple liveness probe."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }
