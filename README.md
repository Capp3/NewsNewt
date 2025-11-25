# NewsNewt

A single-purpose Python microservice that archives news articles and extracts their content as structured JSON, optimized for LLM consumption in n8n workflows.

## Overview

NewsNewt is designed to:

- Accept a news article URL via HTTP POST
- Archive the article using Archive.is/Archive.today
- Extract the main article content from the archived page
- Return clean, structured JSON optimized for downstream LLM processing

The service runs as a private Dockerized microservice in controlled networks and is intentionally minimal and focused.

## Features

- **Archive-First Workflow:** Mandatory archiving ensures content preservation
- **Structured JSON Output:** Optimized for LLM consumption
- **Error Handling:** Clear error codes and structured error messages
- **Health Checks:** Container orchestration support
- **Comprehensive Logging:** Configurable log levels with rotation
- **Rate Limiting:** Built-in rate limiting for Archive.is to prevent 429 errors

## Architecture

- **Language:** Python 3.12
- **HTTP Framework:** FastAPI
- **Archive Integration:** Archive.is (direct httpx integration)
- **Content Extraction:** trafilatura
- **Deployment:** Docker container in private network

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Ports 8000 available

### Run with Docker Compose

```bash
# Clone the repository
git clone <repository-url>
cd NewsNewt

# Copy environment configuration (optional - uses defaults if not present)
cp .env.sample .env

# Start the service
docker compose up -d

# Check service status
curl http://localhost:8000/health
# Expected response: {"status":"ok"}

# Stop the service
docker compose down
```

## API Usage

### Health Check

```bash
GET /health
```

**Response:**

```json
{
  "status": "ok"
}
```

### Service Information

```bash
GET /
```

**Response:**

```json
{
  "service": "NewsNewt",
  "version": "0.1.0",
  "status": "running",
  "endpoints": {
    "health": "/health",
    "article": "/article (POST)"
  }
}
```

### Archive and Extract Article

```bash
POST /article
Content-Type: application/json

{
  "url": "https://example.com/news/article",
  "force_archive": false,
  "archive_service": "archive_is"
}
```

**Successful Response (200 OK):**

```json
{
  "url": "https://example.com/news/article",
  "archive_url": "https://archive.is/abc123",
  "body_text": "Article content here...",
  "title": null,
  "byline": null,
  "published_date": null
}
```

**Error Response (400/500):**

```json
{
  "detail": {
    "error": {
      "code": "INVALID_URL",
      "message": "URL must be a valid http or https URL"
    }
  }
}
```

### Error Codes

| Code                 | HTTP Status | Description                    |
| -------------------- | ----------- | ------------------------------ |
| `INVALID_URL`        | 422         | Invalid URL format or protocol |
| `ARCHIVE_TIMEOUT`    | 500         | Archive service timed out      |
| `ARCHIVE_FAILURE`    | 500         | Archive service failed         |
| `EXTRACTION_FAILURE` | 500         | Content extraction failed      |
| `INTERNAL_ERROR`     | 500         | Unexpected error occurred      |

## Configuration

Environment variables can be configured in `.env` or passed directly to Docker.

### Environment Variables

| Variable                   | Options                                         | Default      | Description                |
| -------------------------- | ----------------------------------------------- | ------------ | -------------------------- |
| `NEWSNEWT_ARCHIVE_SERVICE` | `archive_is`, `archive_today`, `auto`           | `archive_is` | Archive service to use     |
| `NEWSNEWT_TIMEOUT_SECONDS` | 10-600                                          | 300          | Request timeout in seconds |
| `NEWSNEWT_LOG_LEVEL`       | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` | `INFO`       | Logging verbosity          |
| `TZ`                       | Timezone string                                 | `UTC`        | Container timezone         |

### Example .env File

```env
NEWSNEWT_ARCHIVE_SERVICE=archive_is
NEWSNEWT_TIMEOUT_SECONDS=300
NEWSNEWT_LOG_LEVEL=INFO
TZ=UTC
```

## Development

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

```bash
# Install dependencies
uv sync

# Install development dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v

# Run tests with coverage
uv run pytest tests/ --cov=src/newsnewt --cov-report=term-missing

# Run linter
uv run ruff check src/

# Format code
uv run black src/ tests/
```

### Run Locally

```bash
# Run the service
uv run python -m newsnewt.main

# Service will be available at http://localhost:8000
```

## Project Structure

```
NewsNewt/
├── src/newsnewt/          # Source code
│   ├── api.py             # FastAPI application and endpoints
│   ├── archive.py         # Archive.is integration
│   ├── config.py          # Configuration management
│   ├── extractor.py       # Content extraction with trafilatura
│   ├── logging_config.py  # Logging configuration
│   ├── main.py            # Application entry point
│   ├── models.py          # Pydantic models
│   ├── rate_limit.py      # Rate limiting for Archive.is
│   └── utils.py           # Utility functions
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── config/                # Configuration files
│   └── .env.sample        # Environment variable template
├── logs/                  # Application logs (created at runtime)
├── docs/                  # Documentation
│   ├── project-brief.md   # Project specifications
│   ├── technical.md       # Technical details
│   ├── TESTING.md         # Testing documentation
│   └── DEPLOYMENT.md      # Deployment guide
├── dockerfile             # Docker image definition
├── compose.yml            # Docker Compose configuration
├── pyproject.toml         # Project metadata and dependencies
└── README.md              # This file
```

## Docker

### Build Manually

```bash
# Build the image
docker build -t newsnewt:latest -f dockerfile .

# Run the container
docker run -d \
  --name newsnewt \
  -p 8000:8000 \
  -e NEWSNEWT_LOG_LEVEL=INFO \
  -v $(pwd)/logs:/app/logs \
  newsnewt:latest

# Check logs
docker logs newsnewt

# Stop the container
docker stop newsnewt && docker rm newsnewt
```

### Health Check

The Docker image includes a built-in health check that runs every 30 seconds:

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' newsnewt
```

## Testing

The project includes comprehensive test coverage:

- **Unit Tests:** 33 tests covering critical paths (URL validation, config, utils, rate limiting)
- **Integration Tests:** 10 tests covering full API workflows and error scenarios
- **Coverage:** 63% overall (critical paths at 90%+)

See [docs/TESTING.md](docs/TESTING.md) for detailed testing documentation.

## Documentation

- **[Project Brief](docs/project-brief.md)** - Complete project specifications
- **[Technical Documentation](docs/technical.md)** - Technical details and API specs
- **[Testing Documentation](docs/TESTING.md)** - Testing guide and coverage
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions

## Logging

Logs are written to:

- Console (stdout/stderr)
- File: `logs/newsnewt.log` (with rotation, max 10MB, 5 backups)

Log format:

```
2025-11-25 15:30:00 UTC - module.name - LEVEL - message
```

## Rate Limiting

NewsNewt includes built-in rate limiting for Archive.is to prevent 429 (Too Many Requests) errors:

- Minimum 5-second interval between archive requests
- Async-safe with lock mechanism
- Automatic delay when needed

## Known Limitations

- Archive.is may rate-limit automated requests (this is expected behavior)
- Metadata extraction (title, byline, date) returns `null` in MVP (body text only)
- Archive.today and Archive.is are the same service (different domains)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues or questions:

1. Check the [documentation](docs/)
2. Review the [testing guide](docs/TESTING.md)
3. Check [deployment guide](docs/DEPLOYMENT.md)

## Changelog

### v0.1.0 (2025-11-25)

- ✅ Initial MVP release
- ✅ Archive.is integration with rate limiting
- ✅ Content extraction with trafilatura
- ✅ FastAPI REST API
- ✅ Docker deployment
- ✅ Comprehensive test suite
- ✅ Structured error handling
