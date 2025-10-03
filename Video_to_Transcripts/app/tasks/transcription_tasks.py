"""
Background tasks for transcript processing using Celery.
"""
from celery import Celery
from typing import Dict, Any
import logging

from app.core.config import settings
from app.models.transcript_models import TranscriptRequest, TranscriptResponse
from app.services.transcription_service import TranscriptionService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "transcript_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.transcription_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)


@celery_app.task(bind=True, name="process_transcript_async")
def process_transcript_async(self, task_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process transcript asynchronously using Celery.
    
    Args:
        task_id: Unique task identifier
        request_data: Serialized TranscriptRequest data
        
    Returns:
        Serialized TranscriptResponse data
    """
    try:
        # Update task state
        self.update_state(
            state="PROCESSING",
            meta={"progress": 10, "message": "Initializing transcript processing..."}
        )
        
        # Create request object from data
        request = TranscriptRequest(**request_data)
        
        # Initialize transcription service
        transcription_service = TranscriptionService()
        
        # Update progress
        self.update_state(
            state="PROCESSING",
            meta={"progress": 30, "message": "Fetching video information..."}
        )
        
        # Process the transcript
        response = transcription_service.process_transcript(task_id, request)
        
        # Update progress
        self.update_state(
            state="PROCESSING",
            meta={"progress": 90, "message": "Finalizing files..."}
        )
        
        # Convert response to dict for serialization
        response_data = response.dict()
        
        logger.info(f"Successfully processed transcript task {task_id}")
        
        return {
            "status": "SUCCESS",
            "result": response_data
        }
        
    except Exception as e:
        logger.error(f"Error processing transcript task {task_id}: {str(e)}")
        
        # Update task state with error
        self.update_state(
            state="FAILURE",
            meta={
                "progress": 0,
                "message": f"Error: {str(e)}",
                "error": str(e)
            }
        )
        
        # Re-raise the exception so Celery can handle it properly
        raise


@celery_app.task(name="cleanup_old_files")
def cleanup_old_files_task(days_old: int = 7) -> Dict[str, Any]:
    """
    Background task to clean up old transcript files.
    
    Args:
        days_old: Number of days after which files should be deleted
        
    Returns:
        Cleanup results
    """
    try:
        from app.services.storage_service import StorageService
        
        storage_service = StorageService()
        deleted_count = storage_service.cleanup_old_files(days_old)
        
        logger.info(f"Cleaned up {deleted_count} old files")
        
        return {
            "status": "SUCCESS",
            "deleted_files": deleted_count,
            "message": f"Successfully deleted {deleted_count} files older than {days_old} days"
        }
        
    except Exception as e:
        logger.error(f"Error during file cleanup: {str(e)}")
        return {
            "status": "FAILURE",
            "error": str(e),
            "message": "Failed to clean up old files"
        }


@celery_app.task(name="health_check")
def health_check_task() -> Dict[str, Any]:
    """Health check task for monitoring."""
    return {
        "status": "OK",
        "message": "Celery worker is healthy",
        "timestamp": "2024-01-01T00:00:00Z"  # This would be actual timestamp
    }


# Task routing (optional - for multiple queues)
celery_app.conf.task_routes = {
    "process_transcript_async": {"queue": "transcripts"},
    "cleanup_old_files": {"queue": "maintenance"},
    "health_check": {"queue": "health"}
}

# Periodic tasks (optional - requires celery beat)
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "cleanup-old-files-daily": {
        "task": "cleanup_old_files",
        "schedule": crontab(hour=2, minute=0),  # Run daily at 2:00 AM
        "args": (7,)  # Delete files older than 7 days
    },
    "health-check-every-5-minutes": {
        "task": "health_check",
        "schedule": 300.0,  # Every 5 minutes
    },
}

celery_app.conf.timezone = "UTC"
