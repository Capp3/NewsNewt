# Architecture

This document describes the system architecture of NewsNewt, a Crawlee-based web scraping microservice.

## System Overview

NewsNewt is designed as a single-purpose microservice that sits between n8n workflows and target websites, providing intelligent web scraping capabilities with JavaScript rendering support.

```
┌─────────┐      HTTP/JSON      ┌───────────┐      Browser      ┌──────────────┐
│   n8n   │ ──────────────────> │ NewsNewt  │ ───────────────> │ Target Sites │
│Workflow │ <────────────────── │  Service  │ <─────────────── │              │
└─────────┘      HTTP/JSON      └───────────┘      HTML/Data   └──────────────┘
```

## Core Components

### 1. FastAPI Application

**Location**: `src/app/main.py`

The FastAPI application serves as the HTTP interface, providing:

- **Health Check Endpoint** (`GET /health`): Simple liveness check
- **Scrape Endpoint** (`POST /scrape`): Main scraping functionality
- **Lifespan Management**: Initializes and manages the Crawlee crawler instance

**Key Responsibilities**:

- Request validation via Pydantic models
- Crawler lifecycle management
- Request/response tracking
- Error handling and JSON response formatting

### 2. Crawlee Crawler

**Technology**: Crawlee for Python with PlaywrightCrawler

The crawler is initialized during application startup and runs continuously, processing queued requests.

**Configuration**:

- **Headless Mode**: Configurable via `PLAYWRIGHT_HEADLESS` env var
- **Concurrency**: Limited by `CRAWL_CONCURRENCY` setting
- **Stealth Mode**: Optional anti-detection via `ENABLE_STEALTH`

**Request Processing Flow**:

1. FastAPI endpoint receives request
2. Request is queued with unique ID and user data
3. Crawler processes request asynchronously
4. Result is stored and returned via Future
5. Response sent back to client

### 3. Playwright Browser

**Technology**: Chromium browser via Playwright

Provides full JavaScript rendering capabilities:

- Executes client-side JavaScript
- Handles SPAs and dynamic content
- Supports modern web standards
- Optional stealth mode to avoid detection

### 4. Extraction Utilities

**Location**: `src/app/extraction.py`

A collection of utility functions for intelligent content extraction:

#### `dismiss_popups(page)`

Attempts to automatically close common popups and cookie banners:

- Searches for acceptance buttons ("Accept", "OK", "Agree", etc.)
- Clicks close buttons and removes banner elements
- Silently continues if no popups found

#### `extract_with_fallbacks(page, selectors)`

Extracts content using provided selectors with automatic fallbacks:

- Tries user-provided CSS selectors first
- Falls back to common patterns for known field types
- Supports: title, content, author, date, description
- Returns empty string if no matches found

#### `detect_captcha(page)`

Detects if a CAPTCHA is present:

- Scans page text for CAPTCHA keywords
- Checks for CAPTCHA-related iframes
- Looks for common CAPTCHA elements (reCAPTCHA, hCaptcha)
- Returns boolean result

## Request Flow

### Successful Scrape

```
1. n8n → POST /scrape with URL and selectors
         ↓
2. FastAPI validates request → generates request_id
         ↓
3. Creates Future and adds to tracker
         ↓
4. Enqueues request to Crawlee with user_data
         ↓
5. Crawlee spawns Playwright browser
         ↓
6. Playwright navigates to URL (with stealth if enabled)
         ↓
7. dismiss_popups() removes cookie banners
         ↓
8. detect_captcha() checks for CAPTCHAs
         ↓
9. extract_with_fallbacks() extracts data
         ↓
10. Result stored and Future resolved
         ↓
11. FastAPI returns JSON response to n8n
```

### Error Handling

Errors are categorized and returned as structured JSON:

- **CAPTCHA Detected** (`422`): CAPTCHA found on page
- **Timeout** (`408`): Request exceeded timeout limit
- **Scraping Error** (`500`): General scraping failure

All errors include:

```json
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

## Docker Architecture

### Container Structure

```
┌─────────────────────────────────────────┐
│          newsnewt Container             │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   FastAPI App (port 3000)       │   │
│  │   - uvicorn ASGI server         │   │
│  │   - Request handling            │   │
│  └──────────────┬──────────────────┘   │
│                 │                       │
│  ┌──────────────▼──────────────────┐   │
│  │   Crawlee Crawler               │   │
│  │   - Request queue               │   │
│  │   - Concurrency control         │   │
│  └──────────────┬──────────────────┘   │
│                 │                       │
│  ┌──────────────▼──────────────────┐   │
│  │   Playwright + Chromium         │   │
│  │   - Browser automation          │   │
│  │   - JS rendering                │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Volumes:                               │
│  - ./logs → /app/logs (log files)      │
└─────────────────────────────────────────┘
```

### Networking

- **Internal Port**: 3000 (application listens)
- **External Port**: 3000 (mapped via docker-compose)
- **Network**: `newsnewt-network` (bridge)

When used with n8n in the same Docker network:

```yaml
# n8n HTTP Request node URL
http://newsnewt:3000/scrape
```

When accessed from host machine:

```bash
http://localhost:3000/scrape
```

## Environment Variables

Configuration is managed via environment variables:

| Variable                   | Purpose                  | Default            | Notes                                 |
| -------------------------- | ------------------------ | ------------------ | ------------------------------------- |
| `CRAWL_CONCURRENCY`        | Max simultaneous scrapes | `3`                | Higher values increase resource usage |
| `LOG_LEVEL`                | Logging verbosity        | `INFO`             | Options: DEBUG, INFO, WARNING, ERROR  |
| `PLAYWRIGHT_HEADLESS`      | Run browser headless     | `true`             | Set to `false` for debugging          |
| `ENABLE_STEALTH`           | Enable anti-detection    | `true`             | Reduces CAPTCHA triggers              |
| `PLAYWRIGHT_BROWSERS_PATH` | Browser install location | `/app/.playwright` | Set in Dockerfile                     |

## Performance Considerations

### Concurrency

The `CRAWL_CONCURRENCY` setting controls how many pages can be scraped simultaneously:

- **Low (1-2)**: Conservative, lower resource usage
- **Medium (3-5)**: Balanced for typical use cases
- **High (6+)**: Aggressive, requires more CPU/memory

### Resource Usage

Typical resource consumption per concurrent scrape:

- **CPU**: ~200-300% per browser instance
- **Memory**: ~200-500 MB per browser instance
- **Network**: Depends on target page size

### Recommended Limits

For production deployment:

```yaml
services:
  newsnewt:
    deploy:
      resources:
        limits:
          cpus: "4"
          memory: 4G
        reservations:
          cpus: "2"
          memory: 2G
```

## Security

### Internal Service Design

NewsNewt is designed as an **internal service** with no authentication:

- Should NOT be exposed to the public internet
- Intended for use within private Docker networks
- No rate limiting or authentication built-in

### Recommended Deployment

1. **Same Network as n8n**: Deploy in the same Docker network
2. **Firewall Protection**: Do not expose port 3000 publicly
3. **Reverse Proxy**: If external access needed, use authenticated reverse proxy

### Future Security Enhancements

For production environments requiring public access:

- Add API key authentication
- Implement rate limiting
- Add request validation and sanitization
- Consider using a reverse proxy with authentication

## Monitoring and Logging

### Logging

Logs are written to:

- **Console**: Standard output (captured by Docker)
- **Log Files**: `/app/logs` directory (mounted volume)

Log format:

```
2024-12-02 10:30:45 - app.main - INFO - Received scrape request abc123 for URL: https://example.com
```

### Health Checks

Docker Compose includes automatic health checking:

```yaml
healthcheck:
  test:
    [
      "CMD",
      "python",
      "-c",
      "import urllib.request; urllib.request.urlopen('http://localhost:3000/health')",
    ]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 5s
```

Container is marked unhealthy if `/health` endpoint fails to respond.

## Scalability

### Horizontal Scaling

NewsNewt can be horizontally scaled using Docker Compose or orchestration:

```yaml
services:
  newsnewt:
    deploy:
      replicas: 3
```

Add a load balancer (nginx, traefik) to distribute requests across instances.

### Vertical Scaling

Increase resources per container:

- Raise `CRAWL_CONCURRENCY` for more parallel scrapes
- Allocate more CPU and memory via Docker limits
- Monitor resource usage and adjust accordingly

## Technology Stack

| Layer              | Technology         | Version | Purpose                       |
| ------------------ | ------------------ | ------- | ----------------------------- |
| Runtime            | Python             | 3.12    | Application runtime           |
| Package Manager    | uv                 | 0.9.11  | Fast dependency management    |
| Web Framework      | FastAPI            | 0.115+  | HTTP API server               |
| ASGI Server        | Uvicorn            | 0.32+   | Production ASGI server        |
| Crawler Framework  | Crawlee            | 0.4+    | Scraping orchestration        |
| Browser Automation | Playwright         | Latest  | Browser control and rendering |
| Browser            | Chromium           | Latest  | JavaScript execution          |
| Anti-Detection     | playwright-stealth | 1.0.6+  | Stealth mode support          |
| Validation         | Pydantic           | 2.0+    | Request/response models       |
| HTTP Client        | httpx              | 0.27+   | Async HTTP requests           |
| Container          | Docker             | 20.10+  | Containerization              |

## Design Principles

1. **Simplicity**: Single purpose, minimal configuration
2. **Reliability**: Structured error handling, no crashes
3. **Integration**: Designed specifically for n8n workflows
4. **Observability**: Comprehensive logging, health checks
5. **Maintainability**: Clean code, clear separation of concerns
