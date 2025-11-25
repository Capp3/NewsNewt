"""Archive service integration for NewsNewt."""

import asyncio
import re
from typing import Optional, Tuple

import httpx

from newsnewt.config import settings
from newsnewt.rate_limit import archive_rate_limiter
from newsnewt.logging_config import get_logger

logger = get_logger(__name__)


class ArchiveError(Exception):
    """Base exception for archive-related errors."""

    pass


class ArchiveTimeoutError(ArchiveError):
    """Raised when archive operation times out."""

    pass


class ArchiveFailureError(ArchiveError):
    """Raised when archive operation fails."""

    pass


async def archive_url(
    url: str,
    force_archive: bool = False,
    archive_service: str = "archive_is",
    timeout: Optional[int] = None,
) -> Tuple[str, str]:
    """Archive a URL and fetch the archived HTML.

    This is the main entry point for archiving operations.

    Args:
        url: Original article URL to archive
        force_archive: If True, always create new archive. If False, use
            existing if available.
        archive_service: Archive service to use (currently only
            "archive_is" supported)
        timeout: Timeout in seconds (defaults to settings.timeout_seconds)

    Returns:
        Tuple of (archive_url, html_content)

    Raises:
        ArchiveTimeoutError: If operation exceeds timeout
        ArchiveFailureError: If archive operation fails

    """
    if timeout is None:
        timeout = settings.timeout_seconds

    logger.info(
        f"Archiving URL: {url} (force={force_archive}, service={archive_service})"
    )

    try:
        # Run the archiving operation with timeout
        archive_url = await asyncio.wait_for(
            _create_archive(url, archive_service), timeout=timeout
        )

        if not archive_url:
            raise ArchiveFailureError("Archive service returned empty URL")

        logger.info(f"Archive created: {archive_url}")

        # Fetch the archived HTML
        html_content = await asyncio.wait_for(
            _fetch_archived_html(archive_url),
            timeout=min(30, timeout // 2),  # Use shorter timeout for fetching
        )

        logger.info(f"Fetched archived HTML, size: {len(html_content)} bytes")
        return archive_url, html_content

    except asyncio.TimeoutError:
        logger.error(f"Archive operation timed out after {timeout}s for URL: {url}")
        raise ArchiveTimeoutError(
            f"Archive operation exceeded timeout of {timeout} seconds"
        )
    except ArchiveError:
        raise  # Re-raise our custom errors
    except Exception as e:
        logger.error(f"Archive operation failed for URL {url}: {e}")
        raise ArchiveFailureError(f"Archive operation failed: {str(e)}")


async def _create_archive(url: str, archive_service: str) -> Optional[str]:
    """Create an archive using direct Archive.is submission.

    Archive.is works by:
    1. Submitting URL WITHOUT protocol prefix to archive.is
    2. Parsing the response to get the archive URL

    Args:
        url: URL to archive (with http:// or https://)
        archive_service: Archive service to use

    Returns:
        Archive URL or None if failed

    """
    if archive_service not in ["archive_is", "archive_today"]:
        raise ArchiveFailureError(f"Unsupported archive service: {archive_service}")

    # Remove http:// or https:// prefix as required by Archive.is
    url_without_protocol = re.sub(r"^https?://", "", url)
    logger.debug("Creating archive for: %s", url_without_protocol)

    # Apply rate limiting to avoid 429 errors from Archive.is
    await archive_rate_limiter.wait_if_needed()

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=90.0) as client:
            # Submit URL to archive.is WITHOUT protocol
            response = await client.post(
                "https://archive.is/submit/",
                data={"url": url_without_protocol},
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; NewsNewt/0.1.0)",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

            # Archive.is redirects to the archive URL on success
            final_url = str(response.url)

            # Check if we got a valid archive URL
            if "archive.is" in final_url or "archive.today" in final_url:
                # Extract the clean archive URL
                if "/submit/" not in final_url:
                    logger.debug(f"Archive created: {final_url}")
                    return final_url

            # Try to extract archive URL from response HTML
            archive_url_match = re.search(
                r'<link rel="canonical" href="(https?://archive\.(is|today)/[^"]+)"',
                response.text,
            )
            if archive_url_match:
                archive_url = archive_url_match.group(1)
                logger.debug(f"Extracted archive URL from HTML: {archive_url}")
                return archive_url

            logger.warning("Could not extract archive URL from response")
            return None

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during archiving: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during archiving: {e}")
        return None


async def _fetch_archived_html(archive_url: str) -> str:
    """Fetch HTML content from archived URL.

    Args:
        archive_url: Archive.is URL to fetch from

    Returns:
        HTML content as string

    Raises:
        ArchiveFailureError: If fetch fails

    """
    logger.debug(f"Fetching archived HTML from: {archive_url}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                archive_url, follow_redirects=True, timeout=30.0
            )
            response.raise_for_status()
            return response.text

    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch archived HTML from {archive_url}: {e}")
        raise ArchiveFailureError(f"Failed to fetch archived content: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching archived HTML: {e}")
        raise ArchiveFailureError(f"Failed to fetch archived content: {str(e)}")
