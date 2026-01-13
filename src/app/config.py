"""Configuration settings for the application."""

import os
from typing import Any


class Config:
    """Application configuration loaded from environment variables."""

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Playwright/Crawler settings
    playwright_headless: bool = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
    enable_stealth: bool = os.getenv("ENABLE_STEALTH", "true").lower() == "true"
    crawl_concurrency: int = int(os.getenv("CRAWL_CONCURRENCY", "3"))

    @classmethod
    def get_crawler_settings(cls) -> dict[str, Any]:
        """Get crawler configuration as a dictionary."""
        return {
            "headless": cls.playwright_headless,
            "enable_stealth": cls.enable_stealth,
            "max_concurrency": cls.crawl_concurrency,
            "log_level": cls.log_level,
        }
