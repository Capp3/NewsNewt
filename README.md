# NewsNewt

**Crawlee-based scraping microservice for n8n**

A simple, self-hosted web scraping microservice designed for integration with n8n workflows. Built with FastAPI and Crawlee, featuring Playwright-powered JavaScript rendering, intelligent content extraction, and automatic popup handling.

## Features

- 🎭 **Playwright-Powered**: Full JavaScript rendering for modern web applications
- 🥷 **Stealth Mode**: Configurable anti-detection measures to reduce CAPTCHA triggers
- 🎯 **Intelligent Extraction**: Flexible CSS selector matching with automatic fallbacks
- 🍪 **Popup Handling**: Automatic dismissal of cookie banners and popups
- 🛡️ **CAPTCHA Detection**: Identifies CAPTCHAs and returns structured error responses
- 🔌 **n8n Optimized**: JSON-only API designed for HTTP Request node integration
- 🐳 **Docker Native**: Single-container deployment via docker-compose

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Basic understanding of n8n HTTP Request nodes (if using n8n)

### Installation

1. **Clone the repository**:

```bash
git clone <repository-url>
cd NewsNewt
```

2. **Start the service**:

```bash
docker compose up -d
```

The service will be available at `http://localhost:3000`

3. **Verify it's running**:

```bash
curl http://localhost:3000/health
```

Expected response: `{"status": "ok"}`

## Usage Examples

### Basic Scrape

Scrape a webpage with automatic content extraction:

```bash
curl -X POST http://localhost:3000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article"
  }'
```

### Scrape with Selectors

Extract specific fields using CSS selectors:

```bash
curl -X POST http://localhost:3000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "selectors": {
      "title": {"css": "h1"},
      "author": {"css": ".author-name"},
      "content": {"css": "article"}
    }
  }'
```

### Response Format

```json
{
  "url": "https://example.com/article",
  "data": {
    "title": "Article Title",
    "author": "John Doe",
    "content": "Article content..."
  },
  "meta": {
    "status": 200,
    "duration_ms": 2156
  }
}
```

## n8n Integration

1. Add an **HTTP Request** node to your workflow
2. Configure:
   - **Method**: POST
   - **URL**: `http://newsnewt:3000/scrape` (same Docker network) or `http://localhost:3000/scrape`
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
3. Access extracted data: `{{$json.data.title}}`, `{{$json.data.content}}`

## Configuration

The service is configured via environment variables in `compose.yml`. See [`config/.env.sample`](config/.env.sample) for detailed documentation.

### Quick Reference

| Variable              | Default | Description                                    |
| --------------------- | ------- | ---------------------------------------------- |
| `CRAWL_CONCURRENCY`   | `3`     | Maximum concurrent scraping operations         |
| `LOG_LEVEL`           | `INFO`  | Logging level (DEBUG, INFO, WARNING, ERROR)    |
| `PLAYWRIGHT_HEADLESS` | `true`  | Run browser in headless mode                   |
| `ENABLE_STEALTH`      | `true`  | Enable stealth mode to avoid CAPTCHA detection |

### Customizing Configuration

Create a `.env` file in the project root to override defaults:

```bash
cp config/.env.sample .env
# Edit .env with your preferred values
docker compose down && docker compose up -d
```

## API Endpoints

### GET /health

Health check endpoint. Returns `{"status": "ok"}` if service is running.

### POST /scrape

Scrape a URL with optional CSS selectors.

**Request**:

```json
{
  "url": "https://example.com",
  "selectors": {
    "field_name": { "css": "selector" }
  },
  "timeout_ms": 30000
}
```

**Response**: See [Usage Examples](#usage-examples) above.

For detailed API documentation, see [`docs/technical.md`](docs/technical.md).

## Logging

View logs in real-time:

```bash
docker compose logs -f newsnewt
```

Enable debug logging by setting `LOG_LEVEL=DEBUG` in your `.env` file or `compose.yml`.

## Documentation

- **[Getting Started](docs/index.md)**: Comprehensive guide with examples
- **[Architecture](docs/architecture.md)**: System design and component overview
- **[Technical Reference](docs/technical.md)**: Complete API documentation
- **[Project Brief](docs/project-brief.md)**: Detailed project requirements and design

## Troubleshooting

### Service won't start

Check logs:

```bash
docker compose logs newsnewt
```

### CAPTCHA detected

- Ensure `ENABLE_STEALTH=true` in your configuration
- Reduce `CRAWL_CONCURRENCY` to avoid rate limiting
- Check if target site requires authentication

### Empty data returned

- Verify selectors match page structure
- Enable `LOG_LEVEL=DEBUG` to see extraction attempts
- Check if page content loads via JavaScript (may need more time)

For more troubleshooting tips, see [`docs/technical.md`](docs/technical.md#troubleshooting).

## Development

### Local Development Setup

```bash
# Install dependencies
uv sync

# Install Playwright browsers
uv run playwright install chromium --with-deps

# Run locally
uv run uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

### Building Documentation

```bash
# Install mkdocs (if not already installed)
pip install mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve
```

## License

See [LICENSE](LICENSE) file for details.

## Support

For issues and feature requests, please use the project's issue tracker.
