# Technical Context: NewsNewt

## Technology Stack

### Core Technologies
- **Python 3.12**: Application runtime
- **FastAPI 0.115+**: Web framework for HTTP API
- **Uvicorn 0.32+**: ASGI server for production
- **Crawlee 0.4+**: Scraping orchestration framework
- **Playwright**: Browser automation and JavaScript rendering
- **Chromium**: Browser engine
- **playwright-stealth 1.0.6+**: Anti-detection measures
- **Pydantic 2.0+**: Request/response validation
- **UV 0.9.11**: Fast Python package manager

### Development Tools
- **Ruff**: Linting and formatting
- **Pytest**: Testing framework
- **MkDocs**: Documentation generation
- **Docker**: Containerization
- **Docker Compose**: Orchestration

## Project Structure

```
NewsNewt/
├── src/app/              # Application source code
│   ├── __init__.py
│   ├── main.py           # FastAPI app initialization
│   ├── config.py         # Configuration management
│   ├── routes.py         # API route handlers
│   ├── models.py         # Pydantic models
│   ├── crawler.py        # Crawlee crawler setup
│   └── extraction.py     # Content extraction utilities
├── docs/                 # Documentation
│   ├── architecture.md
│   ├── technical.md
│   └── project-brief.md
├── config/               # Configuration files
├── memory-bank/          # Memory bank for AI assistance
├── compose.yml           # Docker Compose configuration
├── dockerfile            # Docker image definition
├── pyproject.toml        # Python project configuration
└── Makefile              # Development commands
```

## Architecture Components

### 1. FastAPI Application (`src/app/main.py`)
- Lifespan management for crawler initialization
- Shared state via `app.state`:
  - `requests_to_results`: Maps request IDs to results
  - `pending_requests`: Maps request IDs to Futures
  - `crawler_running`: Boolean flag
  - `crawler_task`: Async task reference
  - `crawler`: PlaywrightCrawler instance

### 2. Route Handlers (`src/app/routes.py`)
- `/health`: Health check endpoint
- `/scrape`: Main scraping endpoint
  - Validates request via Pydantic models
  - Creates unique request ID
  - Queues request to crawler
  - Waits for result with timeout
  - Returns JSON response

### 3. Crawler Setup (`src/app/crawler.py`)
- `create_crawler()`: Initializes PlaywrightCrawler with BrowserPool
- `create_request_handler()`: Creates handler function for each request
- Request handler flow:
  1. Apply stealth mode (if enabled)
  2. Wait for page load
  3. Dismiss popups
  4. Detect CAPTCHA
  5. Extract data with selectors
  6. Store result and resolve Future

### 4. Extraction Utilities (`src/app/extraction.py`)
- `dismiss_popups()`: Attempts to close cookie banners and popups
- `extract_with_fallbacks()`: Extracts content with automatic fallbacks
- `detect_captcha()`: Detects CAPTCHA presence on page

### 5. Configuration (`src/app/config.py`)
- Environment variable management
- Settings: log level, headless mode, stealth mode, concurrency

## Key Patterns

### Request Flow
1. FastAPI receives POST /scrape
2. Validates request, generates request_id
3. Creates Future and adds to tracker
4. Enqueues request to Crawlee with user_data
5. Crawlee processes request asynchronously
6. Result stored and Future resolved
7. Response returned to client

### Error Handling
- Structured JSON errors with `error_type` and `error_message`
- Status codes: 200 (success), 408 (timeout), 422 (CAPTCHA), 500 (error)
- All errors logged with request ID for tracing

### Concurrency Model
- Crawlee manages browser pool
- `CRAWL_CONCURRENCY` limits simultaneous scrapes
- Each request tracked via Future pattern
- Crawler runs continuously, processing queued requests

## Docker Configuration

### Dockerfile
- Base: `python:3.12-slim-bookworm`
- Installs system dependencies for Playwright
- Uses UV for dependency management
- Installs Playwright browsers
- Exposes port 3000
- Health check configured

### Docker Compose
- Single service: `newsnewt`
- Port mapping: `3000:3000`
- Environment variables for configuration
- Volume mount for logs: `./logs:/app/logs`
- Network: `newsnewt-network`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CRAWL_CONCURRENCY` | `3` | Max concurrent scrapes |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `PLAYWRIGHT_HEADLESS` | `true` | Run browser headless |
| `ENABLE_STEALTH` | `true` | Enable anti-detection |

## Development Workflow

### Local Development
```bash
uv sync                                    # Install dependencies
uv run playwright install chromium --with-deps  # Install browsers
uv run uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

### Docker Development
```bash
docker compose up -d                       # Start service
docker compose logs -f newsnewt            # View logs
docker compose down                        # Stop service
```

### Code Quality
```bash
make lint                                  # Run linting
make lint-fix                              # Auto-fix issues
make pytest                                # Run tests
make ci                                    # Full CI checks
```

## Known Technical Debt

1. **Debug logging in production code**: `crawler.py` contains debug logging code (lines 18-44) that should be removed or properly configured
2. **Error handling**: Some error paths may need improvement
3. **Type hints**: Some areas may need better type annotations
4. **Testing**: Test coverage needs to be established
5. **Documentation**: Code comments could be enhanced
