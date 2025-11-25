"""Unit tests for rate limiting."""

import asyncio
from datetime import datetime

import pytest

from newsnewt.rate_limit import RateLimiter


@pytest.mark.asyncio
class TestRateLimiter:
    """Tests for RateLimiter."""

    async def test_first_request_no_wait(self):
        """Test that first request doesn't wait."""
        limiter = RateLimiter(min_interval_seconds=1.0)

        start = datetime.now()
        await limiter.wait_if_needed()
        elapsed = (datetime.now() - start).total_seconds()

        # Should be immediate (< 0.1s)
        assert elapsed < 0.1

    async def test_second_request_waits(self):
        """Test that second request waits for rate limit."""
        limiter = RateLimiter(min_interval_seconds=1.0)

        # First request
        await limiter.wait_if_needed()

        # Second request should wait
        start = datetime.now()
        await limiter.wait_if_needed()
        elapsed = (datetime.now() - start).total_seconds()

        # Should wait ~1 second
        assert 0.9 <= elapsed <= 1.2

    async def test_multiple_requests_respect_interval(self):
        """Test that multiple requests respect rate limit."""
        limiter = RateLimiter(min_interval_seconds=0.5)

        start = datetime.now()
        for _ in range(3):
            await limiter.wait_if_needed()
        elapsed = (datetime.now() - start).total_seconds()

        # 3 requests with 0.5s interval should take ~1.0s total
        assert 0.9 <= elapsed <= 1.2

    async def test_requests_after_interval_no_wait(self):
        """Test that requests after interval don't wait."""
        limiter = RateLimiter(min_interval_seconds=0.2)

        # First request
        await limiter.wait_if_needed()

        # Wait longer than interval
        await asyncio.sleep(0.3)

        # Second request should not wait
        start = datetime.now()
        await limiter.wait_if_needed()
        elapsed = (datetime.now() - start).total_seconds()

        # Should be immediate
        assert elapsed < 0.1
