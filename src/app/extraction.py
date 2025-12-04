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
    dismissed_count = 0

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

    logger.debug(f"Scanning for popup buttons with {len(button_texts)} text patterns...")

    # Try to find and click acceptance buttons
    for text in button_texts:
        try:
            # Case-insensitive button search
            button = page.locator(f"button:has-text('{text}')").first
            if await button.count() > 0:
                await button.click(timeout=1000)
                logger.info(f"🍪 Dismissed popup - Clicked button: '{text}'")
                dismissed_count += 1
                await page.wait_for_timeout(500)  # Brief wait after click
                break
        except Exception as e:
            logger.debug(f"Failed to click button '{text}': {e}")
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

    logger.debug(f"Scanning for close buttons with {len(close_selectors)} selectors...")

    for selector in close_selectors:
        try:
            element = page.locator(selector).first
            if await element.count() > 0:
                await element.click(timeout=1000)
                logger.info(f"🍪 Dismissed popup - Clicked close element: {selector}")
                dismissed_count += 1
                await page.wait_for_timeout(500)
                break
        except Exception as e:
            logger.debug(f"Failed to click close element '{selector}': {e}")
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

    logger.debug(f"Scanning for banner elements with {len(banner_selectors)} selectors...")
    removed_banners = 0

    # Try to remove banners directly
    for selector in banner_selectors:
        try:
            result = await page.eval_on_selector_all(
                selector, "elements => { const count = elements.length; elements.forEach(e => e.remove()); return count; }"
            )
            if result and result > 0:
                logger.info(f"🍪 Removed {result} banner element(s): {selector}")
                removed_banners += result
        except Exception as e:
            logger.debug(f"Failed to remove banner '{selector}': {e}")
            continue

    if dismissed_count > 0 or removed_banners > 0:
        logger.info(
            f"✓ Popup dismissal complete - Clicked: {dismissed_count}, Removed: {removed_banners}"
        )
    else:
        logger.debug("No popups or banners found on page")


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
    if selectors:
        logger.debug(f"Extracting {len(selectors)} field(s) with custom selectors")

    for field_name, selector_config in selectors.items():
        value = None
        used_selector = None

        # Try the user-provided selector first
        if "css" in selector_config:
            css_selector = selector_config["css"]
            logger.debug(f"Trying field '{field_name}' with selector: {css_selector}")
            try:
                element = page.locator(css_selector).first
                if await element.count() > 0:
                    # Check if it's a meta tag
                    if css_selector.startswith("meta"):
                        value = await element.get_attribute("content")
                    else:
                        value = await element.text_content()
                    if value and value.strip():
                        used_selector = css_selector
                        logger.info(
                            f"✓ Field '{field_name}': Found with provided selector (length: {len(value.strip())})"
                        )
            except Exception as e:
                logger.debug(f"Selector failed for '{field_name}': {e}")

        # If still no value, try fallbacks
        if not value and field_name.lower() in fallbacks:
            logger.debug(
                f"Trying {len(fallbacks[field_name.lower()])} fallback(s) for '{field_name}'"
            )
            for idx, fallback_selector in enumerate(fallbacks[field_name.lower()], 1):
                try:
                    element = page.locator(fallback_selector).first
                    if await element.count() > 0:
                        # Check if it's a meta tag
                        if fallback_selector.startswith("meta"):
                            value = await element.get_attribute("content")
                        else:
                            value = await element.text_content()
                        if value and value.strip():
                            used_selector = fallback_selector
                            logger.info(
                                f"✓ Field '{field_name}': Found with fallback #{idx}: {fallback_selector} (length: {len(value.strip())})"
                            )
                            break
                except Exception as e:
                    logger.debug(f"Fallback #{idx} failed for '{field_name}': {e}")
                    continue

        # Store result (empty string if nothing found)
        cleaned_value = (value or "").strip()
        data[field_name] = cleaned_value

        if not cleaned_value:
            logger.warning(
                f"⚠️  Field '{field_name}': No data found (tried {1 + (len(fallbacks.get(field_name.lower(), [])) if field_name.lower() in fallbacks else 0)} selector(s))"
            )

    # If no selectors provided, try to extract basic page info
    if not selectors:
        logger.debug("No selectors provided - extracting basic page information")

        # Extract title
        try:
            title_element = page.locator("h1").first
            if await title_element.count() > 0:
                title_value = (await title_element.text_content() or "").strip()
                if title_value:
                    data["title"] = title_value
                    logger.info(
                        f"✓ Auto-extracted title from h1 (length: {len(title_value)})"
                    )
        except Exception as e:
            logger.debug(f"Failed to auto-extract title: {e}")

        # Extract main content
        try:
            content_element = page.locator("article, main").first
            if await content_element.count() > 0:
                content_value = (await content_element.text_content() or "").strip()
                if content_value:
                    data["content"] = content_value
                    logger.info(
                        f"✓ Auto-extracted content from article/main (length: {len(content_value)})"
                    )
        except Exception as e:
            logger.debug(f"Failed to auto-extract content: {e}")

    # Summary
    success_count = len([v for v in data.values() if v])
    total_count = len(data)
    logger.info(
        f"📊 Extraction summary: {success_count}/{total_count} field(s) extracted successfully"
    )

    return data


async def detect_captcha(page: Page) -> bool:
    """
    Detect if a CAPTCHA is present on the page.

    Args:
        page: Playwright page instance

    Returns:
        True if CAPTCHA detected, False otherwise
    """
    logger.debug("Starting CAPTCHA detection scan...")

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

    logger.debug(f"Scanning page text for {len(captcha_keywords)} CAPTCHA keywords...")
    try:
        page_text = (await page.text_content("body") or "").lower()
        for keyword in captcha_keywords:
            if keyword in page_text:
                logger.warning(
                    f"🛡️  CAPTCHA DETECTED - Keyword found in page text: '{keyword}'"
                )
                logger.info(
                    "💡 Suggestion: Enable stealth mode or reduce concurrency to avoid CAPTCHAs"
                )
                return True
    except Exception as e:
        logger.debug(f"Failed to scan page text for keywords: {e}")

    # Check for CAPTCHA-related iframes
    captcha_iframe_patterns = [
        "google.com/recaptcha",
        "hcaptcha.com",
        "captcha",
        "recaptcha",
    ]

    logger.debug(
        f"Scanning {len(captcha_iframe_patterns)} iframe patterns for CAPTCHA..."
    )
    try:
        frames = page.frames
        logger.debug(f"Found {len(frames)} iframe(s) on page")
        for frame in frames:
            frame_url = frame.url.lower()
            for pattern in captcha_iframe_patterns:
                if pattern in frame_url:
                    logger.warning(
                        f"🛡️  CAPTCHA DETECTED - CAPTCHA iframe found: {frame_url}"
                    )
                    logger.info(
                        "💡 Suggestion: Enable stealth mode or use a different IP address"
                    )
                    return True
    except Exception as e:
        logger.debug(f"Failed to scan iframes: {e}")

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

    logger.debug(f"Scanning for {len(captcha_selectors)} CAPTCHA element selectors...")
    for selector in captcha_selectors:
        try:
            element = page.locator(selector).first
            if await element.count() > 0:
                logger.warning(
                    f"🛡️  CAPTCHA DETECTED - CAPTCHA element found: {selector}"
                )
                logger.info(
                    "💡 Suggestion: This site uses CAPTCHA protection. Consider stealth mode or manual solving"
                )
                return True
        except Exception as e:
            logger.debug(f"Failed to check selector '{selector}': {e}")
            continue

    logger.debug("✓ No CAPTCHA detected - page is accessible")
    return False
