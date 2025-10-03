"""
File management API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import FileResponse
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
import logging

from app.services.storage_service import StorageService
from app.api.dependencies import get_storage_service, validate_pagination, validate_file_format

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])


@router.get(
    "/",
    response_model=List[Dict[str, Any]],
    summary="List files",
    description="List all generated transcript files"
)
async def list_files(
    pagination: dict = Depends(validate_pagination),
    file_format: Optional[str] = Depends(validate_file_format),
    storage_service: StorageService = Depends(get_storage_service)
) -> List[Dict[str, Any]]:
    """List all generated transcript files."""
    try:
        files = storage_service.list_files()
        
        # Filter by format if specified
        if file_format:
            files = [f for f in files if f["filename"].endswith(f".{file_format}")]
        
        # Apply pagination
        start_idx = pagination["skip"]
        end_idx = start_idx + pagination["limit"]
        
        return files[start_idx:end_idx]
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list files"
        )


@router.get(
    "/{filename}",
    summary="Download file",
    description="Download a specific transcript file"
)
async def download_file(
    filename: str,
    storage_service: StorageService = Depends(get_storage_service)
):
    """Download a specific transcript file."""
    try:
        file_path = storage_service.get_file(filename)
        
        if not file_path or not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {filename} not found"
            )
        
        # Determine media type based on file extension
        media_type_map = {
            ".txt": "text/plain",
            ".pdf": "application/pdf",
            ".json": "application/json"
        }
        
        file_extension = file_path.suffix.lower()
        media_type = media_type_map.get(file_extension, "application/octet-stream")
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file"
        )


@router.delete(
    "/{filename}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete file",
    description="Delete a specific transcript file"
)
async def delete_file(
    filename: str,
    storage_service: StorageService = Depends(get_storage_service)
):
    """Delete a specific transcript file."""
    try:
        file_path = storage_service.get_file(filename)
        
        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {filename} not found"
            )
        
        success = storage_service.delete_file(str(file_path))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file"
            )
        
        logger.info(f"Deleted file: {filename}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )


@router.get(
    "/{filename}/info",
    response_model=Dict[str, Any],
    summary="Get file info",
    description="Get information about a specific file"
)
async def get_file_info(
    filename: str,
    storage_service: StorageService = Depends(get_storage_service)
) -> Dict[str, Any]:
    """Get information about a specific file."""
    try:
        file_path = storage_service.get_file(filename)
        
        if not file_path or not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {filename} not found"
            )
        
        stat = file_path.stat()
        
        return {
            "filename": filename,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
            "file_type": file_path.suffix.lower().lstrip('.'),
            "full_path": str(file_path),
            "is_readable": os.access(file_path, os.R_OK),
            "is_writable": os.access(file_path, os.W_OK)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file info for {filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file information"
        )


@router.post(
    "/cleanup",
    response_model=Dict[str, Any],
    summary="Cleanup old files",
    description="Delete files older than specified days"
)
async def cleanup_old_files(
    days_old: int = 7,
    storage_service: StorageService = Depends(get_storage_service)
) -> Dict[str, Any]:
    """Delete files older than specified days."""
    try:
        if days_old < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="days_old must be at least 1"
            )
        
        deleted_count = storage_service.cleanup_old_files(days_old)
        
        logger.info(f"Cleaned up {deleted_count} files older than {days_old} days")
        
        return {
            "deleted_files": deleted_count,
            "days_old": days_old,
            "message": f"Successfully deleted {deleted_count} files"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup files"
        )


@router.get(
    "/stats",
    response_model=Dict[str, Any],
    summary="Get file statistics",
    description="Get statistics about stored files"
)
async def get_file_stats(
    storage_service: StorageService = Depends(get_storage_service)
) -> Dict[str, Any]:
    """Get statistics about stored files."""
    try:
        files = storage_service.list_files()
        
        if not files:
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "file_types": {},
                "average_size_bytes": 0
            }
        
        total_size = sum(f["size_bytes"] for f in files)
        file_types = {}
        
        for file_info in files:
            filename = file_info["filename"]
            extension = Path(filename).suffix.lower().lstrip('.')
            if extension:
                file_types[extension] = file_types.get(extension, 0) + 1
        
        return {
            "total_files": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types": file_types,
            "average_size_bytes": round(total_size / len(files)) if files else 0,
            "oldest_file": min(files, key=lambda x: x["created_at"])["filename"] if files else None,
            "newest_file": max(files, key=lambda x: x["created_at"])["filename"] if files else None
        }
        
    except Exception as e:
        logger.error(f"Error getting file stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file statistics"
        )
