# System Patterns: NewsNewt

## Architectural Patterns

### 1. Microservice Pattern
- Single-purpose service focused on web scraping
- Stateless design (except for in-memory request tracking)
- Containerized deployment
- RESTful API interface

### 2. Request-Response Pattern
- Synchronous API design (async internally)
- Request ID tracking for observability
- Future-based result waiting
- Timeout handling

### 3. Lifespan Management Pattern
- FastAPI lifespan context manager
- Crawler initialization on startup
- Clean shutdown on teardown
- Shared state via `app.state`

## Code Patterns

### 1. Dependency Injection
- Configuration via environment variables
- Config class for centralized settings
- Dependency injection via function parameters

### 2. Error Handling Pattern
```python
try:
    # Operation
    result = await operation()
except SpecificError as e:
    # Handle specific error
    logger.error(f"Error: {e}")
    return error_response()
except Exception as e:
    # Handle general error
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return generic_error_response()
```

### 3. Logging Pattern
- Structured logging with request IDs
- Log levels: DEBUG, INFO, WARNING, ERROR
- Emoji indicators for quick scanning
- Request lifecycle tracking

### 4. Extraction Pattern
- Try user-provided selector first
- Fallback to common patterns
- Return empty string if nothing found
- Log extraction attempts

## Design Patterns

### 1. Factory Pattern
- `create_crawler()`: Creates configured crawler instance
- `create_request_handler()`: Creates handler function with closure

### 2. Strategy Pattern
- Extraction strategies: selectors → fallbacks → auto-extraction
- Popup dismissal: multiple strategies tried sequentially

### 3. Observer Pattern
- Future-based result notification
- Request tracking dictionary

## Concurrency Patterns

### 1. Async/Await Pattern
- All I/O operations are async
- FastAPI async route handlers
- Crawlee async request handlers

### 2. Future Pattern
- Each request creates a Future
- Crawler resolves Future when done
- Route handler awaits Future with timeout

### 3. Queue Pattern
- Crawlee internal request queue
- Concurrency limit via Crawlee configuration
- Request tracking via dictionary

## Error Patterns

### 1. Structured Errors
```python
{
    "url": "...",
    "data": {},
    "meta": {
        "status": 422,
        "duration_ms": 1234,
        "error_type": "captcha_detected",
        "error_message": "CAPTCHA detected on page"
    }
}
```

### 2. Error Categories
- **CAPTCHA Detected** (422): CAPTCHA found
- **Timeout** (408): Request exceeded timeout
- **Scraping Error** (500): General error

### 3. Error Logging
- Request ID in all error logs
- Error type and message logged
- Stack traces in DEBUG mode

## Testing Patterns

### 1. Unit Tests
- Test individual functions
- Mock external dependencies
- Test error cases

### 2. Integration Tests
- Test API endpoints
- Test crawler integration
- Test error scenarios

### 3. End-to-End Tests
- Test full request flow
- Test with real websites (if possible)
- Test timeout scenarios

## Configuration Patterns

### 1. Environment Variables
- All configuration via env vars
- Default values provided
- Type conversion in Config class

### 2. Docker Configuration
- Environment variables in compose.yml
- Default values in dockerfile
- Override via .env file

## Logging Patterns

### 1. Request Lifecycle Logging
```
📥 [request_id] New scrape request
🔄 [request_id] Processing: URL
✅ [request_id] Success - Extracted N field(s)
📤 [request_id] Returning successful response
```

### 2. Error Logging
```
❌ [request_id] Error after Xms: error message
🛡️  [request_id] CAPTCHA detected
⏱️  [request_id] Timeout after Xs
```

### 3. Debug Logging
- Detailed step-by-step execution
- Selector attempts
- Fallback attempts
- Extraction details

## Code Organization Patterns

### 1. Separation of Concerns
- Routes: HTTP handling
- Crawler: Scraping orchestration
- Extraction: Content extraction logic
- Config: Configuration management
- Models: Data structures

### 2. Single Responsibility
- Each module has one clear purpose
- Functions are focused and small
- Clear module boundaries

### 3. DRY (Don't Repeat Yourself)
- Common patterns extracted to functions
- Reusable extraction logic
- Shared configuration

## Anti-Patterns to Avoid

1. **Synchronous I/O**: Always use async/await
2. **Blocking Operations**: Use async alternatives
3. **Silent Failures**: Always log errors
4. **Hard-coded Values**: Use configuration
5. **Tight Coupling**: Keep modules independent
