# Technical Context

## Playwright Stealth Integration

### Current State

**Package**: `playwright-stealth>=1.0.6` (already installed)

**Current Implementation Location**: `src/app/crawler.py` (lines 216-242)

**Current Approach**:

```python
# Current hacky approach
if config["enable_stealth"]:
    from playwright_stealth import stealth_async

    async def combined_handler(context: PlaywrightCrawlingContext) -> None:
        await stealth_async(context.page)
        await original_handler(context)

    crawler._request_handler = combined_handler  # Modifies internal attribute
```

### Recommended Approach (ZenRows Blog)

According to the ZenRows blog post on Playwright Stealth:

1. **Apply stealth BEFORE navigation** - This is critical for effectiveness
2. **Use proper integration points** - Work with Crawlee's architecture, not against it
3. **Apply to page context** - Use `stealth_async(page)` before `page.goto()`

### Crawlee Integration Points

**BrowserPool Plugin**: Crawlee 0.4.0+ uses `BrowserPool` with `PlaywrightBrowserPlugin`

**Request Handler**: The `request_handler` receives `PlaywrightCrawlingContext` which contains:

- `context.page` - Playwright Page instance
- `context.request` - Request object with URL

**Key Insight**: The page is already created when the request handler is called, but navigation happens inside Crawlee. We need to intercept BEFORE navigation.

### Best Practice Pattern

```python
async def request_handler(context: PlaywrightCrawlingContext) -> None:
    # Apply stealth BEFORE any navigation
    if enable_stealth:
        await stealth_async(context.page)

    # Crawlee handles navigation internally
    # Then proceed with extraction
```

## Crawlee Architecture

- **BrowserPool**: Manages browser instances
- **PlaywrightBrowserPlugin**: Configures browser launch options
- **PlaywrightCrawler**: Orchestrates crawling with request handlers
- **PlaywrightCrawlingContext**: Provides page and request context

## Environment Configuration

- `ENABLE_STEALTH`: Boolean flag (default: `true`)
- `PLAYWRIGHT_HEADLESS`: Boolean flag (default: `true`)
- `CRAWL_CONCURRENCY`: Integer (default: `3`)

## Dependency Management

**Package Manager**: `uv` (not pip)

**Configuration File**: `pyproject.toml`

**Installation**:

```bash
# Install all dependencies (including playwright-stealth)
uv sync

# Install Playwright browsers
uv run playwright install chromium --with-deps
```

**Dependencies are defined in** `pyproject.toml`:

- `playwright-stealth>=1.0.6` - Already configured
- `crawlee[playwright]>=0.4.0` - Crawler framework
- `fastapi>=0.115.0` - Web framework
- All other dependencies listed in `pyproject.toml`

**Note**: Never use `pip install` - always use `uv sync` or `uv add` for this project.
