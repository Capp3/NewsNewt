"""API route handlers."""

import asyncio
import logging
import uuid

from crawlee import Request
from fastapi import FastAPI, HTTPException

from app.models import HealthResponse, ScrapeRequest, ScrapeResponse

logger = logging.getLogger(__name__)


def register_routes(app: FastAPI) -> None:
    """Register API routes with the FastAPI application."""

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
