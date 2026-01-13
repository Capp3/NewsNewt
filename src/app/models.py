"""Pydantic models for API requests and responses."""

from typing import Any

from pydantic import BaseModel, Field


class ScrapeRequest(BaseModel):
    """Request model for scraping endpoint."""

    url: str = Field(..., description="URL to scrape")
    selectors: dict[str, dict[str, str]] | None = Field(
        None,
        description="Optional selectors for extraction, e.g. {'title': {'css': 'h1'}}",
    )
    timeout_ms: int | None = Field(None, description="Optional timeout in milliseconds")


class ScrapeMeta(BaseModel):
    """Metadata about the scraping operation."""

    status: int
    duration_ms: int
    error_type: str | None = None
    error_message: str | None = None


class ScrapeResponse(BaseModel):
    """Response model for scraping endpoint."""

    url: str
    data: dict[str, Any]
    meta: ScrapeMeta


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
