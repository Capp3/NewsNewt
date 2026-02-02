# System Patterns

## Code Organization

- **Configuration**: Centralized in `app.config.Config` class
- **Crawler Setup**: Factory pattern in `create_crawler()`
- **Request Handling**: Handler functions created by `create_request_handler()`
- **Extraction**: Utility functions in `app.extraction` module

## Stealth Integration Pattern

### Current Pattern (Needs Improvement)

```python
# After crawler creation, modify internal handler
if config["enable_stealth"]:
    original_handler = crawler._request_handler
    async def combined_handler(context):
        await stealth_async(context.page)
        await original_handler(context)
    crawler._request_handler = combined_handler
```

### Recommended Pattern (To Implement)

```python
# Apply stealth in request handler before navigation
async def request_handler(context: PlaywrightCrawlingContext) -> None:
    if enable_stealth:
        await stealth_async(context.page)
    # Crawlee handles navigation, then proceed with extraction
    await page.wait_for_load_state("domcontentloaded")
    # ... rest of handler
```

## Configuration Pattern

- Environment variables loaded via `os.getenv()`
- Defaults provided for all settings
- Configuration exposed via `get_crawler_settings()` method

## Error Handling Pattern

- Structured error responses with `meta` field
- Logging at appropriate levels
- CAPTCHA detection with specific error types
- Graceful degradation when stealth unavailable
