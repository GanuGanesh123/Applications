"""
Video-related service functions.
"""
import re
from typing import Optional, Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from app.models.transcript_models import VideoInfo, TranscriptSnippet
from app.core.security import extract_video_id, validate_youtube_url
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class VideoService:
    """Service for handling YouTube video operations."""
    
    def __init__(self):
        self.api = YouTubeTranscriptApi()
    
    def get_video_info(self, url: str) -> VideoInfo:
        """Extract basic video information from URL."""
        if not validate_youtube_url(url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid YouTube URL"
            )
        
        video_id = extract_video_id(url)
        
        return VideoInfo(
            video_id=video_id,
            url=url
        )
    
    def get_available_transcripts(self, video_id: str) -> Dict[str, Any]:
        """Get list of available transcripts for a video."""
        try:
            transcript_list = self.api.list(video_id)
            available = []
            
            for transcript in transcript_list:
                available.append({
                    "language": transcript.language,
                    "language_code": transcript.language_code,
                    "is_generated": transcript.is_generated,
                    "is_translatable": len(transcript.translation_languages) > 0
                })
            
            return {
                "video_id": video_id,
                "available_transcripts": available
            }
            
        except TranscriptsDisabled:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcripts are disabled for this video"
            )
        except NoTranscriptFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No transcripts found for this video"
            )
        except Exception as e:
            logger.error(f"Error fetching transcript list for {video_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch transcript information"
            )
    
    def fetch_transcript(
        self, 
        video_id: str, 
        languages: list[str] = None,
        preserve_formatting: bool = False
    ) -> Dict[str, Any]:
        """Fetch transcript for a video."""
        if languages is None:
            languages = ["en", "en-US", "en-GB"]
        
        try:
            # Get the transcript
            fetched_transcript = self.api.fetch(
                video_id=video_id,
                languages=languages,
                preserve_formatting=preserve_formatting
            )
            
            # Convert to our model format
            snippets = []
            full_text = ""
            
            for entry in fetched_transcript:
                snippet = TranscriptSnippet(
                    text=entry.text,
                    start=entry.start,
                    duration=entry.duration
                )
                snippets.append(snippet)
                full_text += entry.text + " "
            
            # Calculate metrics
            word_count = len(full_text.split())
            duration_seconds = max([s.start + s.duration for s in snippets]) if snippets else 0
            
            return {
                "snippets": snippets,
                "full_text": full_text.strip(),
                "language": fetched_transcript.language_code,
                "is_generated": fetched_transcript.is_generated,
                "word_count": word_count,
                "duration_seconds": duration_seconds
            }
            
        except TranscriptsDisabled:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcripts are disabled for this video"
            )
        except NoTranscriptFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No transcript found for languages: {', '.join(languages)}"
            )
        except Exception as e:
            logger.error(f"Error fetching transcript for {video_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch transcript: {str(e)}"
            )
    
    def get_video_title(self, video_id: str) -> Optional[str]:
        """
        Get video title (this would require YouTube Data API).
        For now, returns None as it requires API key.
        """
        # TODO: Implement with YouTube Data API v3
        return None
