"""Utility functions for NewsNewt."""

import re
from typing import Optional
from urllib.parse import urlparse

from newsnewt.config import settings
from newsnewt.logging_config import get_logger

logger = get_logger(__name__)


def validate_url(url: str) -> tuple[bool, Optional[str]]:
    """Validate that a URL is properly formatted and uses http/https.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is None
        If invalid, error_message contains the reason

    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"

    # Basic URL pattern validation
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if not url_pattern.match(url):
        return False, "URL must be a valid http or https URL"

    # Parse URL to validate structure
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            return False, "URL must use http or https protocol"
        if not parsed.netloc:
            return False, "URL must have a valid domain"
    except Exception as e:
        return False, f"URL parsing failed: {str(e)}"

    logger.debug(f"URL validated: {url}")
    return True, None


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL.

    Args:
        url: URL to extract domain from

    Returns:
        Domain string or None if extraction fails

    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove port if present
        if ":" in domain:
            domain = domain.split(":")[0]
        return domain
    except Exception as e:
        logger.warning(f"Failed to extract domain from {url}: {e}")
        return None


def resolve_archive_service(requested_service: str) -> str:
    """Resolve the archive service to use.

    Args:
        requested_service: Service requested in API call
            ("auto", "archive_is", "archive_today")

    Returns:
        Resolved service name ("archive_is")

    """
    if requested_service == "auto":
        # Use configured default
        return settings.archive_service

    # Normalize archive_today to archive_is (they're the same service)
    if requested_service == "archive_today":
        return "archive_is"

    return requested_service
