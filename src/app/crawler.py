"""Crawler setup and request handling logic."""

import json
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, cast

from crawlee.browsers import BrowserPool, PlaywrightBrowserPlugin
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext
from fastapi import FastAPI

from app.config import Config
from app.extraction import detect_captcha, dismiss_popups, extract_with_fallbacks

logger = logging.getLogger(__name__)

# #region agent log
import os

LOG_PATH = os.getenv("DEBUG_LOG_PATH", "/Users/dcapp3/code/NewsNewt/.cursor/debug.log")


def _debug_log(
    hypothesis_id: str, location: str, message: str, data: dict[str, Any] | None = None
) -> None:
    """Write debug log entry in NDJSON format."""
    try:
        import time as time_module

        log_entry = {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data or {},
            "timestamp": int(time_module.time() * 1000),
        }
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass  # Silently fail if logging fails


# #endregion agent log


def create_request_handler(
    app: FastAPI,
    enable_stealth: bool = True,
) -> Callable[[PlaywrightCrawlingContext], Awaitable[None]]:
    """
    Create a request handler function for the crawler.

    Args:
        app: FastAPI application instance with state

    Returns:
        Request handler function
    """

    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        """Handle each crawl request."""
        request_id = context.request.user_data.get("request_id")
        if not request_id:
            logger.error("⚠️  Missing request_id in user_data - cannot process request")
            return

        start_time = time.time()
        page = context.page
        url = context.request.url

        # Apply stealth IMMEDIATELY at the start (as early as possible)
        if enable_stealth:
            try:
                from playwright_stealth import (
                    stealth_async,  # type: ignore[import-untyped]
                )

                await stealth_async(page)
                logger.debug(f"[{request_id}] Stealth mode applied")
            except ImportError:
                logger.warning(
                    f"⚠️  [{request_id}] playwright-stealth not available - continuing without stealth"
                )

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
            selectors_raw = context.request.user_data.get("selectors", {})
            # Type guard: ensure selectors is a dict
            if not isinstance(selectors_raw, dict):
                selectors: dict[str, dict[str, str]] = {}
            else:
                selectors = cast(dict[str, dict[str, str]], selectors_raw)
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

    return request_handler


def create_crawler(app: FastAPI) -> PlaywrightCrawler:
    """
    Create and configure a PlaywrightCrawler instance.

    Args:
        app: FastAPI application instance

    Returns:
        Configured PlaywrightCrawler instance
    """
    # #region agent log
    _debug_log(
        "A",
        "crawler.py:141",
        "create_crawler entry",
        {"config_keys": list(Config.get_crawler_settings().keys())},
    )
    # #endregion agent log

    config = Config.get_crawler_settings()
    request_handler = create_request_handler(
        app, enable_stealth=config["enable_stealth"]
    )

    # #region agent log
    _debug_log(
        "A",
        "crawler.py:173",
        "Creating browser pool with launch options",
        {"headless": config["headless"]},
    )
    # #endregion agent log

    # Configure browser launch options via BrowserPool (required for Crawlee 0.4.0+)
    browser_plugin = PlaywrightBrowserPlugin(
        browser_type="chromium",
        browser_launch_options={
            "headless": config["headless"],
            "args": ["--no-sandbox", "--disable-setuid-sandbox"],  # Required for Docker
        },
    )
    browser_pool = BrowserPool(plugins=[browser_plugin])

    # #region agent log
    _debug_log(
        "A",
        "crawler.py:185",
        "BrowserPool created",
        {"plugin_type": type(browser_plugin).__name__},
    )
    _debug_log(
        "B", "crawler.py:185", "Using BrowserPool approach", {"has_browser_pool": True}
    )
    # #endregion agent log

    # Initialize crawler with BrowserPool
    try:
        # #region agent log
        _debug_log(
            "C", "crawler.py:190", "Creating PlaywrightCrawler with browser_pool", {}
        )
        # #endregion agent log

        crawler = PlaywrightCrawler(
            browser_pool=browser_pool,
            max_requests_per_crawl=None,  # No limit
            max_request_retries=1,
            request_handler=request_handler,
        )

        # #region agent log
        _debug_log(
            "A",
            "crawler.py:200",
            "PlaywrightCrawler created successfully",
            {"crawler_type": type(crawler).__name__},
        )
        # #endregion agent log
    except (TypeError, AttributeError) as e:
        # #region agent log
        _debug_log(
            "A",
            "crawler.py:203",
            "Error caught",
            {"error_msg": str(e), "error_type": type(e).__name__},
        )
        _debug_log(
            "B", "crawler.py:203", "Crawler initialization failed", {"error": str(e)}
        )
        # #endregion agent log
        raise

    # Log stealth configuration status
    if config["enable_stealth"]:
        logger.info("✓ Stealth mode enabled - Anti-detection measures active")
    else:
        logger.info("ℹ️  Stealth mode disabled - Browser automation may be detectable")

    return crawler
