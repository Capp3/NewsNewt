"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application."""
    # Import here to avoid circular imports
    from app.main import app

    return TestClient(app)


@pytest.fixture
def sample_scrape_request():
    """Sample scrape request data."""
    return {
        "url": "https://example.com",
        "selectors": {"title": {"css": "h1"}, "content": {"css": "article"}},
        "timeout_ms": 30000,
    }


@pytest.fixture
def sample_scrape_response():
    """Sample scrape response data."""
    return {
        "url": "https://example.com",
        "data": {"title": "Example Title", "content": "Example content..."},
        "meta": {"status": 200, "duration_ms": 1234},
    }
