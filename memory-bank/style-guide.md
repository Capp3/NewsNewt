# Style Guide: NewsNewt

## Python Style Guide

### Code Formatting
- **Formatter**: Ruff (Black-compatible)
- **Line Length**: 120 characters (as per pyproject.toml)
- **Import Sorting**: isort with Black profile

### Naming Conventions
- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_CASE`
- **Private**: Prefix with `_` (single underscore)
- **Type Variables**: `PascalCase` (e.g., `T`, `Any`)

### Type Hints
- Use type hints for all function parameters and returns
- Use `typing` module for complex types
- Use `Optional[Type]` or `Type | None` for nullable types
- Use `dict[str, Any]` instead of `Dict[str, Any]` (Python 3.9+)

### Docstrings
- Use Google-style docstrings
- Include Args, Returns, Raises sections
- Keep docstrings concise but informative

### Example Function
```python
async def extract_with_fallbacks(
    page: Page, selectors: dict[str, dict[str, str]]
) -> dict[str, Any]:
    """
    Extract data from page using provided selectors with fallback patterns.

    Args:
        page: Playwright page instance
        selectors: Dictionary mapping field names to selector configs

    Returns:
        Dictionary with extracted data
    """
    # Implementation
```

## FastAPI Style Guide

### Route Handlers
- Use async functions for all route handlers
- Use Pydantic models for request/response validation
- Return Pydantic models directly
- Use HTTPException for errors

### Example Route
```python
@app.post("/scrape", response_model=ScrapeResponse)
async def scrape(request: ScrapeRequest) -> ScrapeResponse:
    """
    Scrape a URL with optional selectors.

    Args:
        request: Scrape request with URL and optional selectors

    Returns:
        Scrape response with extracted data and metadata

    Raises:
        HTTPException: If scraping fails
    """
    # Implementation
```

## Logging Style Guide

### Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages (default)
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages only

### Log Format
- Include request ID in brackets: `[request_id]`
- Use emojis for quick scanning (optional but consistent)
- Include relevant context (URL, duration, etc.)

### Example Logging
```python
logger.info(f"📥 [{request_id}] New scrape request - URL: {url}")
logger.debug(f"[{request_id}] Waiting for page to load...")
logger.error(f"❌ [{request_id}] Error: {error}", exc_info=True)
```

## Error Handling Style Guide

### Error Responses
- Always return structured JSON errors
- Include error_type and error_message
- Use appropriate HTTP status codes
- Log errors before returning

### Example Error Handling
```python
try:
    result = await operation()
except ValueError as e:
    logger.warning(f"⚠️  [{request_id}] Validation error: {e}")
    raise HTTPException(status_code=422, detail={
        "error_type": "validation_error",
        "error_message": str(e)
    })
except Exception as e:
    logger.error(f"❌ [{request_id}] Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail={
        "error_type": "internal_error",
        "error_message": "An unexpected error occurred"
    })
```

## Import Style Guide

### Import Order
1. Standard library imports
2. Third-party imports
3. Local application imports

### Import Formatting
```python
# Standard library
import asyncio
import logging
from typing import Any

# Third-party
from fastapi import FastAPI, HTTPException
from crawlee import Request

# Local
from app.config import Config
from app.models import ScrapeRequest
```

## Comment Style Guide

### When to Comment
- Complex logic that isn't self-explanatory
- Workarounds or temporary solutions
- Non-obvious design decisions
- TODO/FIXME items

### Comment Format
- Use full sentences
- Explain "why" not "what"
- Keep comments up-to-date

### Example Comments
```python
# Apply stealth IMMEDIATELY at the start (as early as possible)
# This reduces the chance of detection before page loads
if enable_stealth:
    await stealth_async(page)
```

## File Organization

### Module Structure
1. Module docstring
2. Imports (standard, third-party, local)
3. Constants
4. Classes
5. Functions
6. Main execution (if applicable)

### Example Module Structure
```python
"""Module docstring explaining purpose."""

import logging
from typing import Any

from fastapi import FastAPI

from app.config import Config

logger = logging.getLogger(__name__)

CONSTANT_VALUE = "value"

class MyClass:
    """Class docstring."""
    pass

async def my_function() -> None:
    """Function docstring."""
    pass
```

## Testing Style Guide

### Test Naming
- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Test Structure
- Arrange: Set up test data
- Act: Execute code under test
- Assert: Verify results

### Example Test
```python
async def test_scrape_success():
    """Test successful scrape operation."""
    # Arrange
    request = ScrapeRequest(url="https://example.com")
    
    # Act
    response = await scrape(request)
    
    # Assert
    assert response.meta.status == 200
    assert "data" in response.data
```

## Documentation Style Guide

### README
- Clear project description
- Quick start guide
- Usage examples
- Configuration reference

### Code Documentation
- Docstrings for all public functions
- Type hints for clarity
- Inline comments for complex logic

## Git Commit Style Guide

### Commit Messages
- Use present tense: "Add feature" not "Added feature"
- Be descriptive but concise
- Reference issues if applicable

### Example Commits
```
feat: Add timeout configuration to scrape endpoint
fix: Handle CAPTCHA detection edge cases
refactor: Extract popup dismissal logic to separate function
docs: Update API documentation with examples
```
