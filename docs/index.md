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

The service is configured via environment variables. See [`config/.env.sample`](../config/.env.sample) for a complete template with detailed descriptions.

### Available Settings

| Variable              | Default | Description                                    |
| --------------------- | ------- | ---------------------------------------------- |
| `CRAWL_CONCURRENCY`   | `3`     | Maximum concurrent scraping operations         |
| `LOG_LEVEL`           | `INFO`  | Logging level (DEBUG, INFO, WARNING, ERROR)    |
| `PLAYWRIGHT_HEADLESS` | `true`  | Run browser in headless mode                   |
| `ENABLE_STEALTH`      | `true`  | Enable stealth mode to avoid CAPTCHA detection |

### Customizing Configuration

#### For Docker Deployment (Default)

The default values are set in `compose.yml` and work out of the box:

```bash
docker-compose up -d
```

To override defaults, create a `.env` file in the project root:

```bash
# Copy the sample configuration
cp config/.env.sample .env

# Edit with your preferred values
nano .env
```

Then restart the service:

```bash
docker-compose down
docker-compose up -d
```

#### For Local Development

1. **Copy the sample configuration**:

```bash
cp config/.env.sample .env
```

2. **Customize settings**:

```bash
# Example local development settings
LOG_LEVEL=DEBUG
PLAYWRIGHT_HEADLESS=false
ENABLE_STEALTH=false
CRAWL_CONCURRENCY=1
```

3. **Run the service**:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

#### Environment Variable Reference

- **`CRAWL_CONCURRENCY`**: Controls parallelism
  - Low (1-2): Conservative, slower but safer
  - Medium (3-5): Balanced (recommended)
  - High (6+): Aggressive, requires more resources

- **`LOG_LEVEL`**: Controls verbosity
  - `DEBUG`: Detailed diagnostic information
  - `INFO`: Standard operation logs (recommended)
  - `WARNING`: Only warnings and errors
  - `ERROR`: Only error messages

- **`PLAYWRIGHT_HEADLESS`**: Browser visibility
  - `true`: No visible browser (production)
  - `false`: Show browser window (debugging)

- **`ENABLE_STEALTH`**: Anti-detection features
  - `true`: Hide automation markers (recommended)
  - `false`: Standard browser mode

### Logging

Logs are written to:
- **Console**: Visible in `docker logs newsnewt`
- **Files**: `./logs` directory (mounted volume)

To view live logs:

```bash
docker logs -f newsnewt
```

To change log level to DEBUG for troubleshooting:

```bash
# Add to .env file
LOG_LEVEL=DEBUG

# Restart service
docker-compose restart
```

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
