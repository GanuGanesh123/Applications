"""
File storage and management service.
"""
import os
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import logging

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.models.transcript_models import TranscriptData, FileOutput, FileFormat
from app.core.config import settings
from app.core.security import sanitize_filename, generate_file_hash

logger = logging.getLogger(__name__)


class StorageService:
    """Service for handling file storage operations."""
    
    def __init__(self):
        self.output_dir = Path(settings.output_directory)
        self.output_dir.mkdir(exist_ok=True, parents=True)
    
    def save_transcript(
        self, 
        transcript_data: TranscriptData,
        format: FileFormat,
        custom_filename: Optional[str] = None
    ) -> List[FileOutput]:
        """Save transcript data in the specified format(s)."""
        files = []
        
        # Generate base filename
        if custom_filename:
            base_filename = sanitize_filename(custom_filename)
        else:
            base_filename = f"{transcript_data.video_info.video_id}_transcript"
        
        # Add timestamp to ensure uniqueness
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{base_filename}_{timestamp}"
        
        try:
            if format in [FileFormat.TXT, FileFormat.BOTH]:
                txt_file = self._save_as_txt(transcript_data, base_filename)
                files.append(txt_file)
            
            if format in [FileFormat.PDF, FileFormat.BOTH]:
                pdf_file = self._save_as_pdf(transcript_data, base_filename)
                files.append(pdf_file)
            
            if format == FileFormat.JSON:
                json_file = self._save_as_json(transcript_data, base_filename)
                files.append(json_file)
            
            logger.info(f"Saved transcript files: {[f.filename for f in files]}")
            return files
            
        except Exception as e:
            logger.error(f"Error saving transcript files: {str(e)}")
            # Clean up any partially created files
            for file_output in files:
                try:
                    os.remove(file_output.file_path)
                except:
                    pass
            raise
    
    def _save_as_txt(self, transcript_data: TranscriptData, base_filename: str) -> FileOutput:
        """Save transcript as plain text file."""
        filename = f"{base_filename}.txt"
        file_path = self.output_dir / filename
        
        content = f"YouTube Video Transcript\n"
        content += f"Video ID: {transcript_data.video_info.video_id}\n"
        content += f"URL: {transcript_data.video_info.url}\n"
        content += f"Language: {transcript_data.language}\n"
        content += f"Generated: {transcript_data.is_generated}\n"
        content += f"Word Count: {transcript_data.word_count}\n"
        content += f"Duration: {transcript_data.duration_seconds:.2f} seconds\n"
        content += f"Generated on: {datetime.utcnow().isoformat()}\n"
        content += "\n" + "="*80 + "\n\n"
        content += transcript_data.full_text
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return FileOutput(
            filename=filename,
            format=FileFormat.TXT,
            size_bytes=file_path.stat().st_size,
            file_path=str(file_path)
        )
    
    def _save_as_pdf(self, transcript_data: TranscriptData, base_filename: str) -> FileOutput:
        """Save transcript as PDF file."""
        filename = f"{base_filename}.pdf"
        file_path = self.output_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=A4,
            rightMargin=settings.pdf_margins,
            leftMargin=settings.pdf_margins,
            topMargin=settings.pdf_margins,
            bottomMargin=settings.pdf_margins
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center
        )
        
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=12,
            leftIndent=0
        )
        
        content_style = ParagraphStyle(
            'ContentStyle',
            parent=styles['Normal'],
            fontSize=settings.pdf_font_size,
            spaceAfter=12,
            leading=14,
            alignment=0  # Left
        )
        
        # Build PDF content
        story = []
        
        # Title
        title = Paragraph("YouTube Video Transcript", title_style)
        story.append(title)
        
        # Video information
        info_text = f"""
        <b>Video ID:</b> {transcript_data.video_info.video_id}<br/>
        <b>URL:</b> {transcript_data.video_info.url}<br/>
        <b>Language:</b> {transcript_data.language}<br/>
        <b>Auto-generated:</b> {'Yes' if transcript_data.is_generated else 'No'}<br/>
        <b>Word Count:</b> {transcript_data.word_count:,}<br/>
        <b>Duration:</b> {transcript_data.duration_seconds:.2f} seconds<br/>
        <b>Generated on:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
        """
        
        info = Paragraph(info_text, info_style)
        story.append(info)
        story.append(Spacer(1, 20))
        
        # Transcript content
        # Split into sentences for better formatting
        sentences = transcript_data.full_text.split('. ')
        
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                # Add period back except for last sentence
                if i < len(sentences) - 1 and not sentence.endswith('.'):
                    sentence += '.'
                
                para = Paragraph(sentence.strip(), content_style)
                story.append(para)
        
        # Build PDF
        doc.build(story)
        
        return FileOutput(
            filename=filename,
            format=FileFormat.PDF,
            size_bytes=file_path.stat().st_size,
            file_path=str(file_path)
        )
    
    def _save_as_json(self, transcript_data: TranscriptData, base_filename: str) -> FileOutput:
        """Save transcript as JSON file."""
        filename = f"{base_filename}.json"
        file_path = self.output_dir / filename
        
        # Convert to JSON-serializable format
        data = {
            "video_info": {
                "video_id": transcript_data.video_info.video_id,
                "url": transcript_data.video_info.url,
                "title": transcript_data.video_info.title
            },
            "transcript": {
                "language": transcript_data.language,
                "is_generated": transcript_data.is_generated,
                "word_count": transcript_data.word_count,
                "duration_seconds": transcript_data.duration_seconds,
                "full_text": transcript_data.full_text,
                "snippets": [
                    {
                        "text": snippet.text,
                        "start": snippet.start,
                        "duration": snippet.duration
                    }
                    for snippet in transcript_data.snippets
                ]
            },
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "content_hash": generate_file_hash(transcript_data.full_text)
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return FileOutput(
            filename=filename,
            format=FileFormat.JSON,
            size_bytes=file_path.stat().st_size,
            file_path=str(file_path)
        )
    
    def get_file(self, filename: str) -> Optional[Path]:
        """Get file path if it exists."""
        file_path = self.output_dir / filename
        return file_path if file_path.exists() else None
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False
    
    def list_files(self) -> List[dict]:
        """List all files in the output directory."""
        files = []
        for file_path in self.output_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime)
                })
        return files
    
    def cleanup_old_files(self, days_old: int = 7) -> int:
        """Clean up files older than specified days."""
        cutoff_time = datetime.utcnow().timestamp() - (days_old * 24 * 60 * 60)
        deleted_count = 0
        
        for file_path in self.output_dir.iterdir():
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old file: {file_path.name}")
                except Exception as e:
                    logger.error(f"Error deleting old file {file_path.name}: {str(e)}")
        
        return deleted_count
