"""
Transcript-related API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from app.models.transcript_models import (
    TranscriptRequest,
    TranscriptResponse,
    TranscriptTaskStatus,
    ErrorResponse,
    FileFormat
)
from app.services.transcription_service import TranscriptionService
from app.services.video_service import VideoService
from app.api.dependencies import (
    get_transcription_service,
    get_video_service,
    validate_pagination,
    validate_languages,
    check_rate_limit
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


@router.post(
    "/",
    response_model=TranscriptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create transcript",
    description="Create a new transcript for a YouTube video"
)
async def create_transcript(
    request: TranscriptRequest,
    background_tasks: BackgroundTasks,
    transcription_service: TranscriptionService = Depends(get_transcription_service),
    _rate_limit: bool = Depends(check_rate_limit)
) -> TranscriptResponse:
    """Create a new transcript processing task."""
    try:
        # Create the task
        task_id = transcription_service.create_transcript_task(request)
        
        # Process synchronously for now (could be made async with Celery)
        response = transcription_service.process_transcript(task_id, request)
        
        logger.info(f"Created transcript for video {response.video_info.video_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error creating transcript: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transcript: {str(e)}"
        )


@router.post(
    "/async",
    response_model=Dict[str, str],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create transcript (async)",
    description="Create a new transcript processing task (returns immediately)"
)
async def create_transcript_async(
    request: TranscriptRequest,
    transcription_service: TranscriptionService = Depends(get_transcription_service),
    _rate_limit: bool = Depends(check_rate_limit)
) -> Dict[str, str]:
    """Create a new transcript processing task asynchronously."""
    try:
        # Create the task
        task_id = transcription_service.create_transcript_task(request)
        
        # In a real implementation, you would queue this with Celery
        # For now, just return the task ID
        
        return {
            "task_id": task_id,
            "status": "accepted",
            "message": "Transcript processing started"
        }
        
    except Exception as e:
        logger.error(f"Error creating async transcript: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transcript task: {str(e)}"
        )


@router.get(
    "/{task_id}",
    response_model=TranscriptResponse,
    summary="Get transcript",
    description="Get transcript by task ID"
)
async def get_transcript(
    task_id: str,
    transcription_service: TranscriptionService = Depends(get_transcription_service)
) -> TranscriptResponse:
    """Get transcript by task ID."""
    response = transcription_service.get_task_status(task_id)
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcript task {task_id} not found"
        )
    
    return response


@router.get(
    "/{task_id}/status",
    response_model=TranscriptTaskStatus,
    summary="Get task status",
    description="Get the status of a transcript processing task"
)
async def get_task_status(
    task_id: str,
    transcription_service: TranscriptionService = Depends(get_transcription_service)
) -> TranscriptTaskStatus:
    """Get the status of a transcript processing task."""
    response = transcription_service.get_task_status(task_id)
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    # Calculate progress based on status
    progress_map = {
        "pending": 0,
        "processing": 50,
        "completed": 100,
        "failed": 0
    }
    
    return TranscriptTaskStatus(
        task_id=task_id,
        status=response.status,
        progress=progress_map.get(response.status.value, 0),
        message=response.error_message if response.status.value == "failed" else None,
        result=response if response.status.value == "completed" else None
    )


@router.get(
    "/",
    response_model=List[TranscriptResponse],
    summary="List transcripts",
    description="List recent transcript tasks"
)
async def list_transcripts(
    pagination: dict = Depends(validate_pagination),
    transcription_service: TranscriptionService = Depends(get_transcription_service)
) -> List[TranscriptResponse]:
    """List recent transcript tasks."""
    tasks = transcription_service.list_tasks(limit=pagination["limit"])
    
    # Apply skip
    start_idx = pagination["skip"]
    end_idx = start_idx + pagination["limit"]
    
    return tasks[start_idx:end_idx]


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete transcript",
    description="Delete a transcript task and its files"
)
async def delete_transcript(
    task_id: str,
    transcription_service: TranscriptionService = Depends(get_transcription_service)
):
    """Delete a transcript task and its associated files."""
    success = transcription_service.delete_task(task_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcript task {task_id} not found"
        )
    
    logger.info(f"Deleted transcript task {task_id}")


@router.get(
    "/info/video",
    response_model=Dict[str, Any],
    summary="Get video info",
    description="Get available transcript information for a YouTube video"
)
async def get_video_transcript_info(
    url: str,
    video_service: VideoService = Depends(get_video_service),
    _rate_limit: bool = Depends(check_rate_limit)
) -> Dict[str, Any]:
    """Get available transcript information for a YouTube video."""
    try:
        video_info = video_service.get_video_info(url)
        transcript_info = video_service.get_available_transcripts(video_info.video_id)
        
        return {
            "video_info": video_info.dict(),
            "transcript_info": transcript_info
        }
        
    except Exception as e:
        logger.error(f"Error getting video info for {url}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get video information: {str(e)}"
        )


class QuickTranscriptRequest(BaseModel):
    """Request model for quick transcript."""
    url: str = Field(..., description="YouTube video URL")
    languages: Optional[List[str]] = Field(
        default=None, 
        description="Preferred languages in order of priority"
    )
    preserve_formatting: bool = Field(
        default=False, 
        description="Whether to preserve HTML formatting in transcript"
    )


@router.post(
    "/quick",
    response_model=Dict[str, Any],
    summary="Quick transcript",
    description="Get transcript text quickly without file generation"
)
async def quick_transcript(
    request: QuickTranscriptRequest,
    video_service: VideoService = Depends(get_video_service),
    _rate_limit: bool = Depends(check_rate_limit)
) -> Dict[str, Any]:
    """Get transcript text quickly without generating files."""
    try:
        # Use default languages if not provided
        languages = request.languages or ["en", "en-US", "en-GB"]
        
        video_info = video_service.get_video_info(request.url)
        transcript_data = video_service.fetch_transcript(
            video_id=video_info.video_id,
            languages=languages,
            preserve_formatting=request.preserve_formatting
        )
        
        return {
            "video_id": video_info.video_id,
            "url": request.url,
            "transcript": transcript_data["full_text"],
            "language": transcript_data["language"],
            "is_generated": transcript_data["is_generated"],
            "word_count": transcript_data["word_count"],
            "duration_seconds": transcript_data["duration_seconds"]
        }
        
    except Exception as e:
        logger.error(f"Error getting quick transcript for {request.url}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get transcript: {str(e)}"
        )
