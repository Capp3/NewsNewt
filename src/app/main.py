"""FastAPI application with Crawlee integration."""

import asyncio
import logging
import os
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from crawlee import Request
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext
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
    logger.info("=" * 60)
    logger.info("NewsNewt Scraper Service Starting")
    logger.info("=" * 60)

    # Shared state for tracking requests and results
    app.state.requests_to_results: dict[str, dict[str, Any]] = {}
    app.state.pending_requests: dict[str, asyncio.Future] = {}
    app.state.crawler_running: bool = False
    app.state.crawler_task: asyncio.Task | None = None

    # Configure crawler settings from environment
    headless = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
    enable_stealth = os.getenv("ENABLE_STEALTH", "true").lower() == "true"
    max_concurrency = int(os.getenv("CRAWL_CONCURRENCY", "3"))
    log_level = os.getenv("LOG_LEVEL", "INFO")

    logger.info("Configuration:")
    logger.info(f"  - Log Level: {log_level}")
    logger.info(f"  - Headless Mode: {headless}")
    logger.info(f"  - Stealth Mode: {enable_stealth}")
    logger.info(f"  - Max Concurrency: {max_concurrency}")
    logger.info("-" * 60)

    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        """Handle each crawl request."""
        request_id = context.request.user_data.get("request_id")
        if not request_id:
            logger.error("⚠️  Missing request_id in user_data - cannot process request")
            return

        start_time = time.time()
        page = context.page
        url = context.request.url

        try:
            logger.info(f"🔄 [{request_id}] Processing: {url}")
            logger.debug(f"[{request_id}] Waiting for page to load...")

            # Wait for page to load
            await page.wait_for_load_state("domcontentloaded")
            logger.debug(f"[{request_id}] Page loaded successfully")

            # Dismiss popups and cookie banners
            logger.debug(f"[{request_id}] Attempting to dismiss popups...")
            await dismiss_popups(page)

            # Check for CAPTCHA
            logger.debug(f"[{request_id}] Checking for CAPTCHA...")
            if await detect_captcha(page):
                raise ValueError("CAPTCHA detected on page")
            logger.debug(f"[{request_id}] No CAPTCHA detected")

            # Extract data
            selectors = context.request.user_data.get("selectors", {})
            selector_count = len(selectors) if selectors else 0
            logger.debug(
                f"[{request_id}] Extracting data with {selector_count} selector(s)..."
            )
            data = await extract_with_fallbacks(page, selectors)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Count extracted fields
            extracted_fields = [k for k, v in data.items() if v]
            logger.info(
                f"✅ [{request_id}] Success - Extracted {len(extracted_fields)} field(s) in {duration_ms}ms"
            )
            logger.debug(f"[{request_id}] Extracted fields: {list(data.keys())}")

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
            duration_ms = int((time.time() - start_time) * 1000)
            error_type = "captcha_detected" if "CAPTCHA" in str(e) else "scraping_error"

            if error_type == "captcha_detected":
                logger.warning(
                    f"🛡️  [{request_id}] CAPTCHA detected - Try enabling stealth mode or reduce concurrency"
                )
            else:
                logger.error(
                    f"❌ [{request_id}] Error after {duration_ms}ms: {e}",
                    exc_info=logger.isEnabledFor(logging.DEBUG),
                )

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
        launch_options={
            "args": ["--no-sandbox", "--disable-setuid-sandbox"],  # Required for Docker
        },
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
            logger.info("✓ Stealth mode enabled - Anti-detection measures active")
        except ImportError:
            logger.warning(
                "⚠️  playwright-stealth package not found - continuing without stealth mode"
            )
            logger.warning(
                "   To enable stealth mode, ensure playwright-stealth is installed"
            )
    else:
        logger.info("ℹ️  Stealth mode disabled - Browser automation may be detectable")

    app.state.crawler = crawler

    logger.info("✓ Crawlee crawler initialized successfully")
    logger.info("=" * 60)
    logger.info("🚀 NewsNewt ready to accept scraping requests on port 3000")
    logger.info("=" * 60)

    yield

    # Cleanup: Cancel crawler task
    if app.state.crawler_task:
        logger.info("Cancelling crawler task...")
        app.state.crawler_task.cancel()
        try:
            await app.state.crawler_task
        except asyncio.CancelledError:
            pass

    # Cleanup
    logger.info("=" * 60)
    logger.info("🛑 Shutting down NewsNewt scraper service...")
    logger.info("=" * 60)
    # Crawlee handles cleanup automatically
    logger.info("✓ Shutdown complete")


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
    selector_count = len(request.selectors) if request.selectors else 0
    timeout = (request.timeout_ms / 1000) if request.timeout_ms else 30.0

    logger.info(
        f"📥 [{request_id}] New scrape request - URL: {request.url} | Selectors: {selector_count} | Timeout: {timeout}s"
    )

    # Create a future to track completion
    future: asyncio.Future = asyncio.Future()
    app.state.pending_requests[request_id] = future

    # Prepare user data
    user_data = {
        "request_id": request_id,
        "selectors": request.selectors or {},
    }

    # Add request to crawler
    logger.debug(f"[{request_id}] Queueing request to crawler...")
    crawlee_request = Request.from_url(request.url, user_data=user_data)
    await app.state.crawler.add_requests([crawlee_request])

    # Start crawler if not already running or if it has finished
    if not app.state.crawler_running or (
        app.state.crawler_task and app.state.crawler_task.done()
    ):
        logger.debug(f"[{request_id}] Starting crawler...")
        app.state.crawler_running = True

        # Create a wrapper to reset the flag when crawler finishes
        async def run_crawler():
            try:
                await app.state.crawler.run()
            finally:
                app.state.crawler_running = False

        app.state.crawler_task = asyncio.create_task(run_crawler())
        # Wait a bit for crawler to start processing
        await asyncio.sleep(0.1)

    # Wait for result with timeout
    logger.debug(f"[{request_id}] Waiting for result (timeout: {timeout}s)...")
    try:
        result = await asyncio.wait_for(future, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(
            f"⏱️  [{request_id}] Timeout after {timeout}s - Try increasing timeout_ms or check if site is responsive"
        )
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
        logger.debug(f"[{request_id}] Cleaned up request tracking")

    # Check for errors in result
    if result["meta"].get("error_type"):
        status_code = result["meta"]["status"]
        error_type = result["meta"]["error_type"]
        logger.info(
            f"📤 [{request_id}] Returning error response - Status: {status_code} | Type: {error_type}"
        )
        raise HTTPException(status_code=status_code, detail=result)

    logger.info(
        f"📤 [{request_id}] Returning successful response - Duration: {result['meta']['duration_ms']}ms"
    )
    return ScrapeResponse(**result)
