"""
Transcription processing service.
"""
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.models.transcript_models import (
    TranscriptRequest, 
    TranscriptResponse, 
    TranscriptData, 
    TranscriptStatus,
    VideoInfo,
    FileFormat
)
from app.services.video_service import VideoService
from app.services.storage_service import StorageService
from app.core.config import settings

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for handling transcript processing."""
    
    def __init__(self):
        self.video_service = VideoService()
        self.storage_service = StorageService()
        self._tasks: Dict[str, TranscriptResponse] = {}  # In-memory storage for demo
    
    def create_transcript_task(self, request: TranscriptRequest) -> str:
        """Create a new transcript processing task."""
        task_id = str(uuid.uuid4())
        
        # Get video info
        video_info = self.video_service.get_video_info(str(request.url))
        
        # Create initial response
        response = TranscriptResponse(
            task_id=task_id,
            status=TranscriptStatus.PENDING,
            video_info=video_info,
            created_at=datetime.utcnow()
        )
        
        # Store task
        self._tasks[task_id] = response
        
        logger.info(f"Created transcript task {task_id} for video {video_info.video_id}")
        return task_id
    
    def process_transcript(self, task_id: str, request: TranscriptRequest) -> TranscriptResponse:
        """Process transcript synchronously."""
        if task_id not in self._tasks:
            raise ValueError(f"Task {task_id} not found")
        
        start_time = datetime.utcnow()
        response = self._tasks[task_id]
        
        try:
            # Update status to processing
            response.status = TranscriptStatus.PROCESSING
            self._tasks[task_id] = response
            
            # Fetch transcript data
            transcript_result = self.video_service.fetch_transcript(
                video_id=response.video_info.video_id,
                languages=request.languages,
                preserve_formatting=request.preserve_formatting
            )
            
            # Create transcript data model
            transcript_data = TranscriptData(
                video_info=response.video_info,
                snippets=transcript_result["snippets"],
                full_text=transcript_result["full_text"],
                language=transcript_result["language"],
                is_generated=transcript_result["is_generated"],
                word_count=transcript_result["word_count"],
                duration_seconds=transcript_result["duration_seconds"]
            )
            
            # Generate output files
            files = self.storage_service.save_transcript(
                transcript_data=transcript_data,
                format=request.format,
                custom_filename=request.custom_filename
            )
            
            # Update response with results
            response.transcript_data = transcript_data
            response.files = files
            response.status = TranscriptStatus.COMPLETED
            response.completed_at = datetime.utcnow()
            response.processing_time_seconds = (
                response.completed_at - start_time
            ).total_seconds()
            
            self._tasks[task_id] = response
            
            logger.info(f"Successfully processed transcript task {task_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing transcript task {task_id}: {str(e)}")
            
            # Update response with error
            response.status = TranscriptStatus.FAILED
            response.error_message = str(e)
            response.completed_at = datetime.utcnow()
            response.processing_time_seconds = (
                response.completed_at - start_time
            ).total_seconds()
            
            self._tasks[task_id] = response
            return response
    
    def get_task_status(self, task_id: str) -> Optional[TranscriptResponse]:
        """Get the status of a transcript task."""
        return self._tasks.get(task_id)
    
    def list_tasks(self, limit: int = 50) -> list[TranscriptResponse]:
        """List recent transcript tasks."""
        tasks = list(self._tasks.values())
        # Sort by creation time, newest first
        tasks.sort(key=lambda x: x.created_at, reverse=True)
        return tasks[:limit]
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a transcript task and its files."""
        if task_id not in self._tasks:
            return False
        
        response = self._tasks[task_id]
        
        # Delete associated files
        for file_output in response.files:
            try:
                self.storage_service.delete_file(file_output.file_path)
            except Exception as e:
                logger.warning(f"Failed to delete file {file_output.file_path}: {str(e)}")
        
        # Remove task from memory
        del self._tasks[task_id]
        
        logger.info(f"Deleted transcript task {task_id}")
        return True
    
    def get_transcript_info(self, video_url: str) -> Dict[str, Any]:
        """Get available transcript information for a video."""
        video_info = self.video_service.get_video_info(video_url)
        return self.video_service.get_available_transcripts(video_info.video_id)
