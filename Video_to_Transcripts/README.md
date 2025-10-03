# YouTube Transcript API

A professional FastAPI application for extracting and converting YouTube video transcripts to various formats (TXT, PDF, JSON).

## Features

- 🎥 Extract transcripts from YouTube videos
- 🌍 Multi-language support with fallback options
- 📄 Export to multiple formats: TXT, PDF, JSON
- ⚡ Fast API with async processing capabilities
- 🔄 Background task processing with Celery
- 📁 File management and cleanup utilities
- 🏥 Health monitoring and system status
- 🔒 Rate limiting and security features
- 📊 Comprehensive logging and error handling
- 🧪 Full test coverage

## Project Structure

```
project/
├── app/
│   ├── api/
│   │   ├── routes/          # API route definitions
│   │   └── dependencies.py  # FastAPI dependencies
│   ├── core/
│   │   ├── config.py        # Application configuration
│   │   └── security.py      # Security utilities
│   ├── models/              # Pydantic models
│   ├── services/            # Business logic services
│   │   ├── video_service.py
│   │   ├── transcription_service.py
│   │   └── storage_service.py
│   ├── tasks/               # Background tasks
│   │   └── transcription_tasks.py
│   └── utils/               # Utility functions
├── tests/                   # Test suite
├── requirements.txt         # Python dependencies
└── main.py                 # Application entry point
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and customize:

```bash
cp env.example .env
```

Edit `.env` with your preferred settings.

### 3. Run the Application

```bash
python main.py
```

Or with uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## API Endpoints

### Transcripts

- `POST /api/v1/transcripts/` - Create transcript with file generation
- `POST /api/v1/transcripts/async` - Create transcript (background processing)
- `POST /api/v1/transcripts/quick` - Get transcript text only (fast)
- `GET /api/v1/transcripts/{task_id}` - Get transcript by task ID
- `GET /api/v1/transcripts/{task_id}/status` - Get task status
- `GET /api/v1/transcripts/` - List all transcripts
- `DELETE /api/v1/transcripts/{task_id}` - Delete transcript
- `GET /api/v1/transcripts/info/video` - Get video transcript info

### Files

- `GET /api/v1/files/` - List generated files
- `GET /api/v1/files/{filename}` - Download file
- `DELETE /api/v1/files/{filename}` - Delete file
- `GET /api/v1/files/{filename}/info` - Get file information
- `GET /api/v1/files/stats` - Get file statistics
- `POST /api/v1/files/cleanup` - Cleanup old files

### Health & Monitoring

- `GET /api/v1/health/` - Basic health check
- `GET /api/v1/health/detailed` - Detailed system information
- `GET /api/v1/health/ready` - Readiness probe
- `GET /api/v1/health/live` - Liveness probe

## Usage Examples

### Quick Transcript (Text Only)

```bash
curl -X POST "http://localhost:8000/api/v1/transcripts/quick" \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

### Full Transcript with Files

```bash
curl -X POST "http://localhost:8000/api/v1/transcripts/" \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "format": "both",
    "languages": ["en", "es"],
    "custom_filename": "my_transcript"
  }'
```

### Get Video Information

```bash
curl "http://localhost:8000/api/v1/transcripts/info/video?url=https://www.youtube.com/watch?v=VIDEO_ID"
```

## Background Processing (Optional)

For production deployments with background processing:

### 1. Install Redis

```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis
```

### 2. Start Celery Worker

```bash
celery -A app.tasks.transcription_tasks worker --loglevel=info
```

### 3. Start Celery Beat (for scheduled tasks)

```bash
celery -A app.tasks.transcription_tasks beat --loglevel=info
```

## Testing

Run the test suite:

```bash
pytest
```

With coverage:

```bash
pytest --cov=app tests/
```

## Configuration Options

Key configuration options in `app/core/config.py`:

- `OUTPUT_DIRECTORY`: Where to store generated files
- `MAX_FILE_SIZE`: Maximum file size limit
- `DEFAULT_LANGUAGES`: Default language preferences
- `PDF_SETTINGS`: PDF generation settings
- `RATE_LIMITING`: API rate limiting configuration

## Supported YouTube URL Formats

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://m.youtube.com/watch?v=VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`

## Error Handling

The API provides comprehensive error handling with detailed error messages:

- `400` - Bad Request (invalid URL, parameters)
- `404` - Not Found (video/transcript not available)
- `422` - Validation Error (invalid request format)
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

## Rate Limiting

- Default: 50 requests per hour per IP
- Configurable via settings
- Returns `429` status when exceeded

## Security Features

- Input validation and sanitization
- File path security
- Rate limiting
- CORS configuration
- Trusted host middleware

## Deployment

### Docker (Recommended)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t youtube-transcript-api .
docker run -p 8000:8000 youtube-transcript-api
```

### Production Deployment

For production, consider:

1. Use a production WSGI server (uvicorn with multiple workers)
2. Set up reverse proxy (nginx)
3. Configure SSL/TLS
4. Set up monitoring and logging
5. Use a proper database for task storage
6. Configure Redis for Celery
7. Set up file storage (S3, etc.)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:

1. Check the API documentation at `/docs`
2. Review the health endpoints for system status
3. Check application logs for detailed error information
4. Open an issue on GitHub

## Changelog

### v1.0.0
- Initial release
- Core transcript extraction functionality
- Multiple output formats (TXT, PDF, JSON)
- FastAPI web interface
- Background processing support
- File management utilities
- Health monitoring
- Comprehensive test suite
