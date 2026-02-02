"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from app.models import (
    HealthResponse,
    ScrapeRequest,
    ScrapeResponse,
    ScrapeMeta,
)


class TestScrapeRequest:
    """Test ScrapeRequest model validation."""

    def test_valid_request(self):
        """Test valid scrape request."""
        request = ScrapeRequest(
            url="https://example.com",
            selectors={"title": {"css": "h1"}},
            timeout_ms=30000,
        )

        assert request.url == "https://example.com"
        assert request.selectors == {"title": {"css": "h1"}}
        assert request.timeout_ms == 30000

    def test_url_required(self):
        """Test that URL is required."""
        with pytest.raises(ValidationError):
            ScrapeRequest(selectors={})

    def test_selectors_optional(self):
        """Test that selectors are optional."""
        request = ScrapeRequest(url="https://example.com")

        assert request.url == "https://example.com"
        assert request.selectors is None
        assert request.timeout_ms is None

    def test_timeout_optional(self):
        """Test that timeout is optional."""
        request = ScrapeRequest(
            url="https://example.com", selectors={"title": {"css": "h1"}}
        )

        assert request.timeout_ms is None

    def test_empty_selectors(self):
        """Test that empty selectors dict is valid."""
        request = ScrapeRequest(url="https://example.com", selectors={})

        assert request.selectors == {}


class TestScrapeMeta:
    """Test ScrapeMeta model validation."""

    def test_valid_meta(self):
        """Test valid scrape metadata."""
        meta = ScrapeMeta(status=200, duration_ms=1234)

        assert meta.status == 200
        assert meta.duration_ms == 1234
        assert meta.error_type is None
        assert meta.error_message is None

    def test_meta_with_error(self):
        """Test metadata with error information."""
        meta = ScrapeMeta(
            status=422,
            duration_ms=1234,
            error_type="captcha_detected",
            error_message="CAPTCHA detected on page",
        )

        assert meta.status == 422
        assert meta.error_type == "captcha_detected"
        assert meta.error_message == "CAPTCHA detected on page"

    def test_status_required(self):
        """Test that status is required."""
        with pytest.raises(ValidationError):
            ScrapeMeta(duration_ms=1234)

    def test_duration_required(self):
        """Test that duration is required."""
        with pytest.raises(ValidationError):
            ScrapeMeta(status=200)


class TestScrapeResponse:
    """Test ScrapeResponse model validation."""

    def test_valid_response(self):
        """Test valid scrape response."""
        response = ScrapeResponse(
            url="https://example.com",
            data={"title": "Example Title"},
            meta=ScrapeMeta(status=200, duration_ms=1234),
        )

        assert response.url == "https://example.com"
        assert response.data == {"title": "Example Title"}
        assert response.meta.status == 200
        assert response.meta.duration_ms == 1234

    def test_empty_data(self):
        """Test response with empty data."""
        response = ScrapeResponse(
            url="https://example.com",
            data={},
            meta=ScrapeMeta(
                status=500,
                duration_ms=1234,
                error_type="scraping_error",
                error_message="Failed to scrape",
            ),
        )

        assert response.data == {}
        assert response.meta.error_type == "scraping_error"

    def test_url_required(self):
        """Test that URL is required."""
        with pytest.raises(ValidationError):
            ScrapeResponse(data={}, meta=ScrapeMeta(status=200, duration_ms=1234))

    def test_data_required(self):
        """Test that data is required."""
        with pytest.raises(ValidationError):
            ScrapeResponse(
                url="https://example.com", meta=ScrapeMeta(status=200, duration_ms=1234)
            )

    def test_meta_required(self):
        """Test that meta is required."""
        with pytest.raises(ValidationError):
            ScrapeResponse(url="https://example.com", data={})


class TestHealthResponse:
    """Test HealthResponse model validation."""

    def test_valid_health_response(self):
        """Test valid health response."""
        response = HealthResponse(status="ok")

        assert response.status == "ok"

    def test_status_required(self):
        """Test that status is required."""
        with pytest.raises(ValidationError):
            HealthResponse()
