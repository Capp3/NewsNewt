"""Extraction utilities for web scraping."""

import logging
from typing import Any

from playwright.async_api import Page

logger = logging.getLogger(__name__)


async def dismiss_popups(page: Page) -> None:
    """
    Attempt to dismiss common cookie banners and popups.

    Args:
        page: Playwright page instance

    This function tries common patterns for dismissing popups but
    does not fail if none are found.
    """
    # Common button text patterns for cookie acceptance
    button_texts = [
        "Accept",
        "Accept all",
        "Agree",
        "OK",
        "Allow",
        "Got it",
        "I agree",
        "Continue",
        "Consent",
        "Allow all",
    ]

    # Try to find and click acceptance buttons
    for text in button_texts:
        try:
            # Case-insensitive button search
            button = page.locator(f"button:has-text('{text}')").first
            if await button.count() > 0:
                await button.click(timeout=1000)
                logger.debug(f"Clicked button with text: {text}")
                await page.wait_for_timeout(500)  # Brief wait after click
                break
        except Exception:
            continue

    # Common close button selectors
    close_selectors = [
        ".modal-close",
        ".popup-close",
        ".cookie-close",
        "[aria-label*='close' i]",
        "[aria-label*='dismiss' i]",
        ".close-button",
        "button.close",
        "[data-dismiss='modal']",
    ]

    for selector in close_selectors:
        try:
            element = page.locator(selector).first
            if await element.count() > 0:
                await element.click(timeout=1000)
                logger.debug(f"Clicked close element: {selector}")
                await page.wait_for_timeout(500)
                break
        except Exception:
            continue

    # Common banner/notice IDs and classes
    banner_selectors = [
        "#cookie-banner",
        "#cookie-notice",
        ".cookie-notice",
        ".cookie-banner",
        ".gdpr-banner",
        ".consent-banner",
        "[data-testid*='cookie' i]",
        "[data-testid*='consent' i]",
    ]

    # Try to remove banners directly
    for selector in banner_selectors:
        try:
            await page.eval_on_selector_all(
                selector, "elements => elements.forEach(e => e.remove())"
            )
        except Exception:
            continue


async def extract_with_fallbacks(
    page: Page, selectors: dict[str, dict[str, str]]
) -> dict[str, Any]:
    """
    Extract data from page using provided selectors with fallback patterns.

    Args:
        page: Playwright page instance
        selectors: Dictionary mapping field names to selector configs
                  e.g. {"title": {"css": "h1"}, "content": {"css": "article"}}

    Returns:
        Dictionary with extracted data. If a selector fails, tries common
        fallbacks for that field type. Returns empty string if nothing found.
    """
    data: dict[str, Any] = {}

    # Define fallback patterns for common field types
    fallbacks = {
        "title": [
            "h1",
            ".article-title",
            ".entry-title",
            ".post-title",
            "[itemprop='headline']",
            "meta[property='og:title']",
        ],
        "content": [
            "article",
            "main",
            ".article-body",
            ".entry-content",
            ".post-content",
            "[role='main']",
            "[itemprop='articleBody']",
        ],
        "author": [
            ".author",
            ".author-name",
            "[rel='author']",
            "[itemprop='author']",
            "meta[name='author']",
        ],
        "date": [
            "time",
            ".published-date",
            ".post-date",
            "[itemprop='datePublished']",
            "meta[property='article:published_time']",
        ],
        "description": [
            ".excerpt",
            ".description",
            ".summary",
            "meta[name='description']",
            "meta[property='og:description']",
        ],
    }

    # Process each requested field
    for field_name, selector_config in selectors.items():
        value = None

        # Try the user-provided selector first
        if "css" in selector_config:
            css_selector = selector_config["css"]
            try:
                element = page.locator(css_selector).first
                if await element.count() > 0:
                    # Check if it's a meta tag
                    if css_selector.startswith("meta"):
                        value = await element.get_attribute("content")
                    else:
                        value = await element.text_content()
                    logger.debug(f"Extracted {field_name} using provided selector")
            except Exception as e:
                logger.debug(
                    f"Failed to extract {field_name} with provided selector: {e}"
                )

        # If still no value, try fallbacks
        if not value and field_name.lower() in fallbacks:
            for fallback_selector in fallbacks[field_name.lower()]:
                try:
                    element = page.locator(fallback_selector).first
                    if await element.count() > 0:
                        # Check if it's a meta tag
                        if fallback_selector.startswith("meta"):
                            value = await element.get_attribute("content")
                        else:
                            value = await element.text_content()
                        if value:
                            logger.debug(
                                f"Extracted {field_name} using fallback: {fallback_selector}"
                            )
                            break
                except Exception:
                    continue

        # Store result (empty string if nothing found)
        data[field_name] = (value or "").strip()

    # If no selectors provided, try to extract basic page info
    if not selectors:
        # Extract title
        try:
            title_element = page.locator("h1").first
            if await title_element.count() > 0:
                data["title"] = (await title_element.text_content() or "").strip()
        except Exception:
            pass

        # Extract main content
        try:
            content_element = page.locator("article, main").first
            if await content_element.count() > 0:
                data["content"] = (await content_element.text_content() or "").strip()
        except Exception:
            pass

    return data


async def detect_captcha(page: Page) -> bool:
    """
    Detect if a CAPTCHA is present on the page.

    Args:
        page: Playwright page instance

    Returns:
        True if CAPTCHA detected, False otherwise
    """
    # Check for common CAPTCHA indicators in page text
    captcha_keywords = [
        "captcha",
        "recaptcha",
        "hcaptcha",
        "verify you are human",
        "verify you're human",
        "security check",
        "prove you're not a robot",
        "cloudflare",
    ]

    try:
        page_text = (await page.text_content("body") or "").lower()
        for keyword in captcha_keywords:
            if keyword in page_text:
                logger.warning(f"CAPTCHA keyword detected: {keyword}")
                return True
    except Exception:
        pass

    # Check for CAPTCHA-related iframes
    captcha_iframe_patterns = [
        "google.com/recaptcha",
        "hcaptcha.com",
        "captcha",
        "recaptcha",
    ]

    try:
        frames = page.frames
        for frame in frames:
            frame_url = frame.url.lower()
            for pattern in captcha_iframe_patterns:
                if pattern in frame_url:
                    logger.warning(f"CAPTCHA iframe detected: {frame_url}")
                    return True
    except Exception:
        pass

    # Check for specific CAPTCHA elements
    captcha_selectors = [
        ".g-recaptcha",
        "#g-recaptcha",
        ".h-captcha",
        "#h-captcha",
        "[data-sitekey]",
        "iframe[src*='recaptcha']",
        "iframe[src*='hcaptcha']",
    ]

    for selector in captcha_selectors:
        try:
            element = page.locator(selector).first
            if await element.count() > 0:
                logger.warning(f"CAPTCHA element detected: {selector}")
                return True
        except Exception:
            continue

    return False
