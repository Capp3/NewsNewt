# Project Brief

## Project Overview

Build a self-hosted "scraping micro-API" that exposes a small set of HTTP endpoints (FastAPI) which internally use Crawlee for Python with PlaywrightCrawler to fetch and extract structured data from web pages, returning JSON only.

The service runs in Docker (via docker-compose) and is consumed from n8n using the HTTP Request node with JSON request/response.

## Core Requirements

### Self-Hosted Service

- Runs as a Docker container, orchestrated via `docker-compose.yml`
- Exposes one port (`3000`) for FastAPI
- No authentication required (internal service design)

### Scraping Capabilities

- Uses **Crawlee for Python** with **PlaywrightCrawler** for JS-heavy pages
- Supports:
  - Single-URL scrape (primary use case)
  - Optional small multi-page crawl (e.g. follow article pagination or next links)

### Output Format

- Always responds with `Content-Type: application/json`
- For each request returns:
  - `url`
  - `data` (structured fields)
  - `meta` (status code, timestamp, duration, debug info)

### n8n Integration

- Optimized for the n8n HTTP Request node: POST with JSON body, response parsed as JSON
- Stable URL paths
- No authentication required (internal service)

## API Design

All endpoints are `application/json` in and out.

### POST /scrape

**Purpose**: Scrape a single page with user-defined selectors.

**Request body**:

- `url` (string, required)
- `selectors` (object, optional): keys are field names, values indicate CSS selectors, e.g.  
  `{"title": {"css": "h1"}, "content": {"css": "article"}}`
- `timeout_ms` (int, optional): Maximum time to wait for response in milliseconds

**Response body**:

- `url` (string)
- `data` (object): extracted fields (strings, arrays, etc.)
- `meta`: `{ "status": int, "duration_ms": int, "error_type": string | null, "error_message": string | null }`

### GET /health

**Purpose**: Health check endpoint.

**Response**: `{ "status": "ok" }`

**Note**: No authentication required.

## Internal Architecture

### FastAPI App

- Follows Crawlee's "running in a web server" pattern with a `lifespan` function that instantiates and holds a crawler instance and a `requests_to_results` dict shared via `app.state`
- Async routes that:
  - Validate payload
  - Register a future / callback with the crawler
  - Enqueue the URL and await completion
  - Return JSON

### Crawlee Setup

- Main crawler: `PlaywrightCrawler` with:
  - Global concurrency limit (configurable via `CRAWL_CONCURRENCY`)
  - Global request timeout
  - Optional stealth mode (configurable via `ENABLE_STEALTH`)
- Default handler extracts:
  - DOM snapshot and then applies selectors
  - Automatic popup dismissal
  - CAPTCHA detection

### Extraction Strategies

- **Selector mode**:
  - If `selectors` provided, map each field to a CSS query and text/attribute extraction
  - Automatic fallback patterns for common field types (title, content, author, date, description)
- **Auto-extraction mode**:
  - If no selectors provided, attempts to extract basic page info (title from h1, content from article/main)

### Error Handling

- Normalize network, timeout, and DOM errors into JSON:
  - `meta.error_type`, `meta.error_message`, `meta.http_status` (if available)
- Never return HTML or stack traces; useful debug info stays in logs
- Structured error responses with actionable suggestions

## Docker & Deployment

### Dockerfile

- Base `python:3.12-slim-bookworm`
- Install system libraries required for Playwright (Chromium, fonts, etc.)
- Install Python deps via UV: `fastapi`, `crawlee[playwright]`, `playwright-stealth`, etc.
- Run `playwright install chromium --with-deps` in build stage
- Set `PYTHONPATH=/app/src` for module resolution
- Expose port 3000

### docker-compose.yml

- Single service `newsnewt`:
  - `build: .`
  - `ports: ["3000:3000"]`
  - `environment`: `CRAWL_CONCURRENCY`, `LOG_LEVEL`, `PLAYWRIGHT_HEADLESS`, `ENABLE_STEALTH`
  - Volume mount for logs: `./logs:/app/logs`
  - Network: `newsnewt-network`

### Runtime

- ASGI server: `uvicorn app.main:app --host 0.0.0.0 --port 3000`
- Healthcheck configured in Compose using Python to `/health`

## n8n Usage Pattern

### HTTP Request Node Configuration

- **Method**: POST
- **URL**: e.g. `http://newsnewt:3000/scrape` (inside Docker network) or `http://localhost:3000/scrape`
- **Body**:
  - Mode: JSON
  - Example body:
    ```json
    {
      "url": "https://example.com/news/123",
      "selectors": {
        "title": { "css": "h1.article-title" },
        "content": { "css": "article" }
      }
    }
    ```
- **Response**:
  - Response format: JSON
  - Use `Field Containing Data` if you want to only pass `data` into later nodes

### Typical Workflows

- Trigger → HTTP Request (`/scrape`) → process JSON → store in DB
- Loop over a list of URLs items, each going through `/scrape`

## Non-Functional Requirements

### Performance & Concurrency

- Configurable `CRAWL_CONCURRENCY` (default: 3) via env, exposed in Docker compose
- Typical single page scrape target: <3–5 seconds on average news site
- Resource usage: ~200-500 MB memory per concurrent scrape

### Observability

- Structured logs per request: URL, status, duration, error
- Log levels: DEBUG, INFO, WARNING, ERROR
- Logs written to console (captured by Docker) and `/app/logs` directory
- Request IDs for tracing requests through their lifecycle

### Security

- No authentication (internal service design)
- Should NOT be exposed to the public internet
- Intended for use within private Docker networks
- For production environments requiring public access:
  - Add API key authentication
  - Implement rate limiting
  - Use reverse proxy with authentication

## Technology Stack

- **Runtime**: Python 3.12
- **Package Manager**: UV 0.9.11
- **Web Framework**: FastAPI 0.115+
- **ASGI Server**: Uvicorn 0.32+
- **Crawler Framework**: Crawlee 0.4+
- **Browser Automation**: Playwright Latest
- **Browser**: Chromium Latest
- **Anti-Detection**: playwright-stealth 1.0.6+
- **Validation**: Pydantic 2.0+
- **HTTP Client**: httpx 0.27+
- **Container**: Docker 20.10+

## References

- [Crawlee Python - Running in Web Server](https://crawlee.dev/python/docs/guides/running-in-web-server)
- [Crawlee Python - Quick Start](https://crawlee.dev/python/docs/quick-start)
- [n8n HTTP Request Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/)
- [FastAPI in Docker](https://stackoverflow.com/questions/65233680/run-fastapi-inside-docker-container)
