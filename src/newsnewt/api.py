"""FastAPI application for NewsNewt."""

from fastapi import FastAPI, HTTPException

from newsnewt.archive import ArchiveFailureError, ArchiveTimeoutError, archive_url
from newsnewt.config import settings
from newsnewt.extractor import ExtractionError, extract_article_content
from newsnewt.logging_config import get_logger, setup_logging
from newsnewt.models import ArticleRequest, ArticleResponse, HealthResponse
from newsnewt.utils import validate_url

# Set up logging
setup_logging()
logger = get_logger(__name__)

# Validate settings
try:
    settings.validate()
except ValueError:
    logger.exception("Configuration validation failed")
    raise

# Create FastAPI application
app = FastAPI(
    title="NewsNewt",
    description="Archive and extract news articles from URLs",
    version="0.1.0",
)

logger.info("NewsNewt API application initialized")


@app.get("/health", tags=["health"])
async def health_check() -> HealthResponse:
    """Health check endpoint for container orchestration.

    Returns:
        HealthResponse with status "ok"

    """
    logger.debug("Health check requested")
    return HealthResponse(status="ok")


@app.get("/", tags=["root"])
async def root() -> dict:
    """Root endpoint."""
    return {
        "service": "NewsNewt",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "article": "/article (POST)",
        },
    }


@app.post("/article", tags=["article"])
async def archive_and_extract_article(request: ArticleRequest) -> ArticleResponse:
    """Archive a news article URL and extract its content.

    This endpoint:
    1. Validates the URL
    2. Archives the URL using a web archive service
    3. Extracts the article body text from the archived HTML
    4. Returns the original URL, archive URL, and body text

    Args:
        request: ArticleRequest with URL and optional settings

    Returns:
        ArticleResponse with URL, archive URL, and body text

    Raises:
        HTTPException: On validation or processing errors

    """
    url = str(request.url)
    logger.info("Processing article request for URL: %s", url)

    # Step 1: Validate URL
    is_valid, error_message = validate_url(url)
    if not is_valid:
        logger.warning("Invalid URL: %s - %s", url, error_message)
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_URL",
                    "message": f"Invalid URL: {error_message}",
                    "details": {"url": url},
                }
            },
        )

    # Resolve archive service and timeout from request or settings
    archive_service = request.archive_service or settings.archive_service
    timeout = settings.timeout_seconds
    force_archive = request.force_archive

    logger.info(
        "Archive settings: service=%s, timeout=%ss, force=%s",
        archive_service,
        timeout,
        force_archive,
    )

    try:
        # Step 2: Archive the URL
        logger.info("Archiving URL: %s", url)
        archive_url_result, html_content = await archive_url(
            url=url,
            force_archive=force_archive,
            archive_service=archive_service,
            timeout=timeout,
        )
        logger.info(
            "Archive created: %s, HTML size: %d bytes",
            archive_url_result,
            len(html_content),
        )

        # Step 3: Extract content
        logger.info("Extracting content from archived HTML")
        body_text = await extract_article_content(html_content, url)
        logger.info("Content extracted: %d characters", len(body_text))

        # Step 4: Return response
        response = ArticleResponse(
            url=url,
            archive_url=archive_url_result,
            body_text=body_text,
            title=None,  # Optional fields for MVP
            byline=None,
            published_at=None,
            source_domain=None,
            language=None,
        )
        logger.info("Successfully processed article: %s", url)
        return response

    except ArchiveTimeoutError as e:
        logger.error("Archive timeout for URL %s: %s", url, e)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "ARCHIVE_TIMEOUT",
                    "message": f"Archive service timed out: {str(e)}",
                    "details": {"url": url, "archive_service": archive_service},
                }
            },
        )

    except ArchiveFailureError as e:
        logger.error("Archive failure for URL %s: %s", url, e)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "ARCHIVE_FAILURE",
                    "message": f"Archive service failed: {str(e)}",
                    "details": {"url": url, "archive_service": archive_service},
                }
            },
        )

    except ExtractionError as e:
        logger.error("Extraction failure for URL %s: %s", url, e)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "EXTRACTION_FAILURE",
                    "message": f"Content extraction failed: {str(e)}",
                    "details": {"url": url},
                }
            },
        )

    except Exception:
        logger.exception("Unexpected error processing URL %s", url)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                    "details": {"url": url},
                }
            },
        )
