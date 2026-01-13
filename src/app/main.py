"""FastAPI application with Crawlee integration."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from app.config import Config
from app.crawler import create_crawler
from app.routes import register_routes

# Configure logging
logging.basicConfig(
    level=Config.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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
    app.state.requests_to_results: dict[str, dict[str, Any]] = {}  # type: ignore[misc]
    app.state.pending_requests: dict[str, asyncio.Future] = {}  # type: ignore[misc]
    app.state.crawler_running: bool = False  # type: ignore[misc]
    app.state.crawler_task: asyncio.Task | None = None  # type: ignore[misc]

    # Get configuration
    config = Config.get_crawler_settings()

    logger.info("Configuration:")
    logger.info(f"  - Log Level: {config['log_level']}")
    logger.info(f"  - Headless Mode: {config['headless']}")
    logger.info(f"  - Stealth Mode: {config['enable_stealth']}")
    logger.info(f"  - Max Concurrency: {config['max_concurrency']}")
    logger.info("-" * 60)

    # Initialize crawler
    app.state.crawler = create_crawler(app)

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
            await app.state.crawler_task  # type: ignore[misc]
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

# Register routes
register_routes(app)
