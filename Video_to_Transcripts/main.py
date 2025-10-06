from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import pandas as pd
from pathlib import Path

# Initialize FastAPI app
app = FastAPI(title="Video to Transcript API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# =====================
# API ROUTES
# =====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint for keeping app awake"""
    return {"status": "healthy", "message": "Server is running"}

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload video file endpoint"""
    try:
        # Validate file type
        if not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{file_id}{file_extension}"
        file_path = UPLOAD_DIR / filename
        
        # Save file
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        return JSONResponse({
            "success": True,
            "job_id": file_id,
            "filename": file.filename,
            "message": "Video uploaded successfully. Transcription will begin shortly."
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Check transcription job status"""
    # This is a placeholder - you'll implement actual status checking later
    return {
        "job_id": job_id,
        "status": "processing",
        "progress": 50,
        "message": "Transcription in progress..."
    }

@app.get("/api/transcript/{job_id}")
async def get_transcript(job_id: str):
    """Get completed transcript"""
    # This is a placeholder - you'll implement actual transcript retrieval later
    transcript_file = OUTPUT_DIR / f"{job_id}.txt"
    
    if not transcript_file.exists():
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    with open(transcript_file, "r") as f:
        content = f.read()
    
    return {
        "job_id": job_id,
        "transcript": content,
        "status": "completed"
    }

# =====================
# SERVE FRONTEND
# =====================

# Mount static files (CSS, JS, images, etc.)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Serve index.html for root and any non-API routes
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve frontend for all non-API routes"""
    
    # Don't interfere with API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Serve index.html
    index_path = "static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"message": "Frontend not found. Please ensure static/index.html exists."}

# Root endpoint - serves index.html
@app.get("/")
async def read_root():
    """Serve the main page"""
    index_path = "static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {
            "message": "Video to Transcript API",
            "docs": "/docs",
            "health": "/api/health"
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

# let go to render