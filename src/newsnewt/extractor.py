"""Content extraction from archived HTML.

This module extracts article body text from archived HTML using trafilatura.
"""

import logging

import trafilatura

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Raised when content extraction fails."""

    pass


async def extract_article_content(html: str, url: str) -> str:
    """Extract article body text from HTML.

    Args:
        html: Raw HTML content from archive
        url: Original article URL (for logging/context)

    Returns:
        Extracted body text (non-empty, minimum 50 characters)

    Raises:
        ExtractionError: If extraction fails or body text is empty/insufficient

    """
    logger.info(f"Extracting content from URL: {url}")
    logger.debug(f"HTML size: {len(html):,} bytes")

    try:
        # Use trafilatura to extract main content
        # Options:
        # - include_comments=False: Skip comment sections
        # - include_tables=False: Skip data tables (focus on article text)
        # - no_fallback=False: Use fallback extraction if needed
        body_text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
            url=url,
        )

        # Validate extraction results
        if not body_text or len(body_text.strip()) == 0:
            logger.error(f"Extraction returned empty body text for URL: {url}")
            raise ExtractionError("Extraction returned empty body text")

        # Require minimum content length for valid article (at least 50 characters)
        if len(body_text.strip()) < 50:
            logger.error(
                f"Extraction returned insufficient content ({len(body_text)} chars) for URL: {url}"
            )
            raise ExtractionError(
                f"Insufficient article content (minimum 50 characters required, got {len(body_text)})"
            )

        logger.info(f"Successfully extracted {len(body_text):,} characters")
        logger.debug(f"Body text preview: {body_text[:200]}...")

        return body_text.strip()

    except Exception as e:
        if isinstance(e, ExtractionError):
            raise
        logger.error(f"Extraction failed for URL {url}: {e}")
        raise ExtractionError(f"Failed to extract content: {str(e)}")


def extract_article_content_sync(html: str, url: str) -> str:
    """Synchronous version of extract_article_content.

    Trafilatura is synchronous, so we provide this wrapper for non-async contexts.

    Args:
        html: Raw HTML content from archive
        url: Original article URL (for logging/context)

    Returns:
        Extracted body text (non-empty, minimum 50 characters)

    Raises:
        ExtractionError: If extraction fails or body text is empty/insufficient

    """
    logger.info(f"Extracting content (sync) from URL: {url}")
    logger.debug(f"HTML size: {len(html):,} bytes")

    try:
        body_text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
            url=url,
        )

        # Validate extraction results
        if not body_text or len(body_text.strip()) == 0:
            logger.error("Extraction returned empty body text for URL: %s", url)
            raise ExtractionError("Extraction returned empty body text")

        # Require minimum content length (at least 50 characters)
        if len(body_text.strip()) < 50:
            logger.error(
                "Extraction returned insufficient content (%d chars) for: %s",
                len(body_text),
                url,
            )
            raise ExtractionError(
                f"Insufficient content (min 50 chars, got {len(body_text)})"
            )

        logger.info("Successfully extracted %d characters", len(body_text))
        logger.debug("Body text preview: %s", body_text[:200])

        return body_text.strip()

    except Exception as e:
        if isinstance(e, ExtractionError):
            raise
        logger.error(f"Extraction failed for URL {url}: {e}")
        raise ExtractionError(f"Failed to extract content: {str(e)}")
