"""FastAPI application with Crawlee integration."""

import asyncio
import logging
import os
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.extraction import detect_captcha, dismiss_popups, extract_with_fallbacks

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Lifespan context manager for FastAPI app.

    Initializes and holds the Crawlee PlaywrightCrawler instance
    and shared request tracking dictionary.
    """
    logger.info("Starting Crawlee PlaywrightCrawler...")

    # Shared state for tracking requests and results
    app.state.requests_to_results: dict[str, dict[str, Any]] = {}
    app.state.pending_requests: dict[str, asyncio.Future] = {}

    # Configure crawler settings from environment
    headless = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
    enable_stealth = os.getenv("ENABLE_STEALTH", "true").lower() == "true"
    max_concurrency = int(os.getenv("CRAWL_CONCURRENCY", "3"))

    logger.info(
        f"Crawler config: headless={headless}, stealth={enable_stealth}, concurrency={max_concurrency}"
    )

    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        """Handle each crawl request."""
        request_id = context.request.user_data.get("request_id")
        if not request_id:
            logger.error("No request_id in user_data")
            return

        start_time = time.time()
        page = context.page
        url = context.request.url

        try:
            logger.info(f"Processing request {request_id} for URL: {url}")

            # Wait for page to load
            await page.wait_for_load_state("domcontentloaded")

            # Dismiss popups and cookie banners
            await dismiss_popups(page)

            # Check for CAPTCHA
            if await detect_captcha(page):
                raise ValueError("CAPTCHA detected on page")

            # Extract data
            selectors = context.request.user_data.get("selectors", {})
            data = await extract_with_fallbacks(page, selectors)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Store result
            result = {
                "url": url,
                "data": data,
                "meta": {
                    "status": 200,
                    "duration_ms": duration_ms,
                },
            }
            app.state.requests_to_results[request_id] = result

            # Complete the future
            if request_id in app.state.pending_requests:
                app.state.pending_requests[request_id].set_result(result)

        except Exception as e:
            logger.error(f"Error processing request {request_id}: {e}", exc_info=True)
            duration_ms = int((time.time() - start_time) * 1000)

            error_type = "captcha_detected" if "CAPTCHA" in str(e) else "scraping_error"
            result = {
                "url": url,
                "data": {},
                "meta": {
                    "status": 422 if error_type == "captcha_detected" else 500,
                    "duration_ms": duration_ms,
                    "error_type": error_type,
                    "error_message": str(e),
                },
            }
            app.state.requests_to_results[request_id] = result

            # Complete the future with error
            if request_id in app.state.pending_requests:
                app.state.pending_requests[request_id].set_result(result)

    # Initialize crawler
    crawler = PlaywrightCrawler(
        headless=headless,
        max_requests_per_crawl=None,  # No limit
        max_request_retries=1,
        request_handler=request_handler,
    )

    # Apply stealth mode if enabled
    if enable_stealth:
        try:
            from playwright_stealth import stealth_async

            async def stealth_handler(context: PlaywrightCrawlingContext) -> None:
                await stealth_async(context.page)

            # Add pre-navigation hook for stealth
            original_handler = crawler._request_handler

            async def combined_handler(context: PlaywrightCrawlingContext) -> None:
                await stealth_async(context.page)
                await original_handler(context)

            crawler._request_handler = combined_handler
            logger.info("Stealth mode enabled")
        except ImportError:
            logger.warning(
                "playwright-stealth not available, continuing without stealth mode"
            )

    app.state.crawler = crawler

    logger.info("Crawlee crawler initialized successfully")

    yield

    # Cleanup
    logger.info("Shutting down crawler...")
    # Crawlee handles cleanup automatically


# Initialize FastAPI app
app = FastAPI(
    title="NewsNewt Scraper",
    description="Crawlee-based scraping microservice for n8n",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok")


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape(request: ScrapeRequest) -> ScrapeResponse:
    """
    Scrape a URL with optional selectors.

    Args:
        request: Scrape request with URL and optional selectors

    Returns:
        Scrape response with extracted data and metadata

    Raises:
        HTTPException: If scraping fails
    """
    import uuid

    request_id = str(uuid.uuid4())
    logger.info(f"Received scrape request {request_id} for URL: {request.url}")

    # Create a future to track completion
    future: asyncio.Future = asyncio.Future()
    app.state.pending_requests[request_id] = future

    # Prepare user data
    user_data = {
        "request_id": request_id,
        "selectors": request.selectors or {},
    }

    # Add request to crawler
    await app.state.crawler.add_requests([{"url": request.url, "user_data": user_data}])

    # Run crawler if not already running
    if not app.state.crawler._has_started:
        asyncio.create_task(app.state.crawler.run())

    # Wait for result with timeout
    timeout = (request.timeout_ms / 1000) if request.timeout_ms else 30.0
    try:
        result = await asyncio.wait_for(future, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"Request {request_id} timed out after {timeout}s")
        raise HTTPException(
            status_code=408,
            detail={
                "url": request.url,
                "data": {},
                "meta": {
                    "status": 408,
                    "duration_ms": int(timeout * 1000),
                    "error_type": "timeout",
                    "error_message": f"Request timed out after {timeout}s",
                },
            },
        )
    finally:
        # Cleanup
        app.state.pending_requests.pop(request_id, None)
        app.state.requests_to_results.pop(request_id, None)

    # Check for errors in result
    if result["meta"].get("error_type"):
        status_code = result["meta"]["status"]
        raise HTTPException(status_code=status_code, detail=result)

    return ScrapeResponse(**result)
