# NewsNewt

**Crawlee-based scraping microservice for n8n**

## Overview

NewsNewt is a self-hosted web scraping microservice designed specifically for integration with n8n workflows. Built on Crawlee for Python with Playwright, it provides robust JavaScript rendering capabilities and intelligent content extraction.

### Key Features

- **Playwright-Powered**: Full JavaScript rendering for modern web applications
- **Stealth Mode**: Configurable anti-detection measures to reduce CAPTCHA triggers
- **Intelligent Extraction**: Flexible CSS selector matching with automatic fallbacks
- **Popup Handling**: Automatic dismissal of cookie banners and popups
- **CAPTCHA Detection**: Identifies CAPTCHAs and returns structured error responses
- **n8n Optimized**: JSON-only API designed for HTTP Request node integration
- **Docker Native**: Single-container deployment via docker-compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Basic understanding of n8n HTTP Request nodes

### Running the Service

1. **Clone the repository**:

```bash
git clone <repository-url>
cd NewsNewt
```

2. **Start the service**:

```bash
docker-compose up -d
```

The service will be available at `http://localhost:3000`

3. **Verify it's running**:

```bash
curl http://localhost:3000/health
```

Expected response: `{"status": "ok"}`

### Basic Usage Example

Scrape a webpage with automatic content extraction:

```bash
curl -X POST http://localhost:3000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "selectors": {
      "title": {"css": "h1"},
      "content": {"css": "article"}
    }
  }'
```

### Using with n8n

1. Add an **HTTP Request** node to your workflow
2. Configure:
   - **Method**: POST
   - **URL**: `http://newsnewt:3000/scrape` (if on same Docker network) or `http://localhost:3000/scrape`
   - **Body Content Type**: JSON
   - **Body**:
     ```json
     {
       "url": "{{$json.url}}",
       "selectors": {
         "title": { "css": "h1" },
         "content": { "css": "article" }
       }
     }
     ```
3. The response will contain:
   - `url`: The scraped URL
   - `data`: Extracted fields as key-value pairs
   - `meta`: Status, duration, and any error information

## Configuration

The service is configured via environment variables in `compose.yml`:

| Variable              | Default | Description                                    |
| --------------------- | ------- | ---------------------------------------------- |
| `CRAWL_CONCURRENCY`   | `3`     | Maximum concurrent scraping operations         |
| `LOG_LEVEL`           | `INFO`  | Logging level (DEBUG, INFO, WARNING, ERROR)    |
| `PLAYWRIGHT_HEADLESS` | `true`  | Run browser in headless mode                   |
| `ENABLE_STEALTH`      | `true`  | Enable stealth mode to avoid CAPTCHA detection |

## API Endpoints

### GET /health

Health check endpoint. Returns 200 OK if service is running.

**Response**:

```json
{
  "status": "ok"
}
```

### POST /scrape

Scrape a URL with optional CSS selectors.

**Request Body**:

```json
{
  "url": "https://example.com",
  "selectors": {
    "field_name": { "css": "selector" }
  },
  "timeout_ms": 30000
}
```

**Response**:

```json
{
  "url": "https://example.com",
  "data": {
    "field_name": "extracted value"
  },
  "meta": {
    "status": 200,
    "duration_ms": 1234
  }
}
```

## Documentation

- **[Architecture](architecture.md)**: System design and component overview
- **[Technical Reference](technical.md)**: Detailed API documentation and configuration

## Support

For issues and feature requests, please use the project's issue tracker.

## License

See LICENSE file for details.
