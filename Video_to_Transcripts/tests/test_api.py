"""
Tests for main API endpoints.
"""
import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "endpoints" in data


def test_app_info_endpoint(client: TestClient):
    """Test application info endpoint."""
    response = client.get("/info")
    
    assert response.status_code == 200
    data = response.json()
    assert "application" in data
    assert "configuration" in data
    assert "features" in data


def test_video_info_endpoint(client: TestClient):
    """Test video info endpoint with valid URL."""
    # Note: This test may fail if the video doesn't have transcripts
    # or if there are network issues
    response = client.get(
        "/api/v1/transcripts/info/video",
        params={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    )
    
    # We expect either 200 (success) or 4xx (no transcripts/video issues)
    assert response.status_code in [200, 400, 404]


def test_video_info_endpoint_invalid_url(client: TestClient):
    """Test video info endpoint with invalid URL."""
    response = client.get(
        "/api/v1/transcripts/info/video",
        params={"url": "https://not-youtube.com/watch?v=invalid"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_files_list_endpoint(client: TestClient):
    """Test files list endpoint."""
    response = client.get("/api/v1/files/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_files_stats_endpoint(client: TestClient):
    """Test files statistics endpoint."""
    response = client.get("/api/v1/files/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_files" in data
    assert "total_size_bytes" in data
    assert "file_types" in data
