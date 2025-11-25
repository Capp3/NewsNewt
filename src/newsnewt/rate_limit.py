"""Simple rate limiting for Archive.is to avoid 429 errors."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter to prevent too many requests to Archive.is."""

    def __init__(self, min_interval_seconds: float = 5.0):
        """Initialize rate limiter.

        Args:
            min_interval_seconds: Minimum seconds between requests (default: 5)

        """
        self.min_interval = min_interval_seconds
        self.last_request_time: Optional[datetime] = None
        self._lock = asyncio.Lock()

    async def wait_if_needed(self) -> None:
        """Wait if necessary to respect rate limit."""
        async with self._lock:
            if self.last_request_time is not None:
                elapsed = (datetime.now() - self.last_request_time).total_seconds()
                wait_time = self.min_interval - elapsed

                if wait_time > 0:
                    logger.info("Rate limit: waiting %.2f seconds", wait_time)
                    await asyncio.sleep(wait_time)

            self.last_request_time = datetime.now()


# Global rate limiter for Archive.is
archive_rate_limiter = RateLimiter(min_interval_seconds=5.0)
