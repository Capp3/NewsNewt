"""Data models for NewsNewt API."""

from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class ArticleRequest(BaseModel):
    """Request model for POST /article endpoint."""

    url: HttpUrl = Field(..., description="The original article URL")
    force_archive: bool = Field(
        default=False, description="Force creation of new archive snapshot"
    )
    archive_service: Literal["auto", "archive_is", "archive_today"] = Field(
        default="auto", description="Archive service to use"
    )


class ArticleResponse(BaseModel):
    """Success response model for POST /article endpoint."""

    url: str = Field(..., description="Original article URL")
    archive_url: str = Field(..., description="URL of the archive snapshot used")
    body_text: str = Field(
        ..., description="Plain-text version of the main article body"
    )
    title: Optional[str] = Field(None, description="Article title")
    byline: Optional[str] = Field(None, description="Author/byline")
    published_at: Optional[str] = Field(None, description="ISO 8601 UTC timestamp")
    source_domain: Optional[str] = Field(None, description="Domain extracted from URL")
    language: Optional[str] = Field(None, description="Language code (e.g., 'en')")


class ErrorDetail(BaseModel):
    """Error detail model."""

    url: Optional[str] = None
    archive_service: Optional[str] = None
    additional: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Error response model."""

    error: dict = Field(..., description="Error information")

    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "ERROR_CODE",
                    "message": "Human-readable explanation",
                    "details": {},
                }
            }
        }


class HealthResponse(BaseModel):
    """Health check response model."""

    status: Literal["ok"] = Field(default="ok", description="Service status")
