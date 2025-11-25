# NewsNewt Documentation

Welcome to the NewsNewt documentation. This guide will help you deploy, configure, and use NewsNewt to archive and extract news article content.

## What is NewsNewt?

NewsNewt is a single-purpose Python microservice that:

- Accepts news article URLs via HTTP POST
- Archives articles using Archive.is/Archive.today
- Extracts main article content from archived pages
- Returns clean, structured JSON optimized for downstream LLM processing

The service is designed to run in private Docker networks, particularly for use in n8n workflows.

## Quick Start

Get NewsNewt running in minutes:

```bash
# Start with Docker Compose
docker compose up -d

# Verify it's working
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

See the [Deployment Guide](DEPLOYMENT.md) for detailed setup instructions.

## Documentation Overview

### Getting Started

- **[Project Overview](project-brief.md)** - Complete project specifications and requirements
- **[Deployment Guide](DEPLOYMENT.md)** - Step-by-step deployment instructions for local and production environments

### User Guide

- **[API Reference](technical.md)** - Complete API documentation with examples
- **[Architecture](architecture.md)** - System architecture and component interactions

### Operations

- **[Testing](TESTING.md)** - Test suite documentation and coverage
- **[Deployment](DEPLOYMENT.md)** - Production deployment, monitoring, and troubleshooting

## Key Features

- **Archive-First Workflow:** Mandatory archiving ensures content preservation
- **Structured JSON Output:** Optimized for LLM consumption
- **Error Handling:** Clear error codes and structured error messages
- **Health Checks:** Container orchestration support
- **Rate Limiting:** Built-in protection against Archive.is rate limits
- **Comprehensive Logging:** Configurable log levels with rotation

## Example Usage

Archive and extract an article:

```bash
curl -X POST http://localhost:8000/article \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/news/article",
    "force_archive": false,
    "archive_service": "archive_is"
  }'
```

**Response:**

```json
{
  "url": "https://example.com/news/article",
  "archive_url": "https://archive.is/abc123",
  "body_text": "Article content here...",
  "title": null,
  "byline": null,
  "published_at": null,
  "source_domain": null,
  "language": null
}
```

## Configuration

All configuration is done via environment variables:

- `NEWSNEWT_ARCHIVE_SERVICE` - Archive backend (default: `archive_is`)
- `NEWSNEWT_TIMEOUT_SECONDS` - Request timeout (default: `300`)
- `NEWSNEWT_LOG_LEVEL` - Log verbosity (default: `INFO`)
- `TZ` - Timezone (recommended: `UTC`)

See the [Deployment Guide](DEPLOYMENT.md#configuration) for complete configuration options.

## Support

- Check the [Deployment Guide](DEPLOYMENT.md#troubleshooting) for common issues
- Review the [Testing Documentation](TESTING.md) for test coverage details
- See the [Project Brief](project-brief.md) for complete specifications

---

**Version:** 0.1.0  
**Status:** Production Ready
