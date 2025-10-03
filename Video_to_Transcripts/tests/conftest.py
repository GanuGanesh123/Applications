"""
Test configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import shutil

from main import app
from app.core.config import settings


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def temp_output_dir():
    """Temporary output directory for tests."""
    temp_dir = tempfile.mkdtemp()
    original_output_dir = settings.output_directory
    settings.output_directory = temp_dir
    
    yield temp_dir
    
    # Cleanup
    settings.output_directory = original_output_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_youtube_url():
    """Sample YouTube URL for testing."""
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - always available


@pytest.fixture
def sample_transcript_request():
    """Sample transcript request data."""
    return {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "format": "both",
        "languages": ["en"],
        "preserve_formatting": False,
        "custom_filename": "test_transcript"
    }
