# NewsNewt - Technical Documentation

> **Technical architecture, implementation details, and development guidelines**

## Architecture Overview

NewsNewt is a Python 3.12 microservice providing an HTTP API for archiving and extracting news article content. It follows a simple, focused architecture designed for containerized deployment in private networks.

---

## System Components

### 1. HTTP API Layer

**Responsibility:** Request handling, validation, and response formatting

**Components:**

- Request validation and normalization
- Route handlers (POST /article, GET /health)
- Error response formatting
- Request/response logging

### 2. Archive Service Integration

**Responsibility:** Interaction with Archive.is/Archive.today

**Components:**

- Archive service abstraction
- URL archiving (new or existing snapshot lookup)
- Archive URL resolution
- Timeout and error handling

### 3. Content Extraction

**Responsibility:** Article content extraction from archived HTML

**Components:**

- HTML parsing and cleaning using trafilatura
- Article body text extraction (required, minimum 50 characters)
- Error handling for extraction failures

**Note:** Metadata extraction (title, byline, date) returns `null` in MVP.

### 4. Configuration & Logging

**Responsibility:** Environment configuration and observability

**Components:**

- Environment variable management
- Logging configuration with rotation
- Health check implementation

---

## Technology Stack

### Core Runtime

- **Python:** 3.12
- **HTTP Framework:** FastAPI
- **Archive Integration:** Direct Archive.is integration via httpx
- **Content Extraction:** trafilatura

### Development Tools

- **Code Formatting:** black
- **Linting:** ruff
- **Package Management:** uv (based on pyproject.toml)

### Infrastructure

- **Containerization:** Docker
- **Orchestration:** Docker Compose
- **Logging:** Python logging module with rotating handlers

---

## API Specification

### POST /article

**Purpose:** Archive and extract article content from a URL

**Request:**

```json
{
  "url": "https://example.com/news/article-123",
  "force_archive": false,
  "archive_service": "auto"
}
```

**Response (Success - 200 OK):**

```json
{
  "url": "https://example.com/news/article-123",
  "archive_url": "https://archive.is/abcdE",
  "body_text": "Full article text...",
  "title": null,
  "byline": null,
  "published_at": null,
  "source_domain": null,
  "language": null
}
```

**Note:** In MVP, only `body_text` is populated. Optional metadata fields (title, byline, etc.) are set to `null`.

**Response (Error - 400/422/500):**

```json
{
  "detail": {
    "error": {
      "code": "ERROR_CODE",
      "message": "Human-readable explanation",
      "details": { "optional": "context" }
    }
  }
}
```

**Note:** FastAPI wraps error responses in a `detail` field. For Pydantic validation errors, the format is different.

### GET /health

**Purpose:** Health check for container orchestration

**Response (200 OK):**

```json
{
  "status": "ok"
}
```

---

## Error Handling

### Error Codes

| Code                 | HTTP Status | Description                    |
| -------------------- | ----------- | ------------------------------ |
| `INVALID_URL`        | 422         | URL is missing, malformed, or unsupported (Pydantic validation) |
| `ARCHIVE_TIMEOUT`    | 500         | Archive operation exceeded timeout        |
| `ARCHIVE_FAILURE`    | 500         | Archive service interaction failed        |
| `EXTRACTION_FAILURE` | 500         | Article extraction failed                 |
| `INTERNAL_ERROR`     | 500         | Unexpected/unhandled error                |

### Error Response Format

All errors follow a consistent envelope structure (wrapped in FastAPI's `detail` field):

```json
{
  "detail": {
    "error": {
      "code": "ERROR_CODE",
      "message": "Human-readable explanation",
      "details": {
        "url": "...",
        "archive_service": "..."
      }
    }
  }
}
```

**Note:** Pydantic validation errors (e.g., invalid URL format) return a different structure with `detail` containing a list of validation errors.

---

## Configuration

### Environment Variables

| Variable                   | Default        | Description                                 |
| -------------------------- | -------------- | ------------------------------------------- |
| `NEWSNEWT_ARCHIVE_SERVICE` | `"archive_is"` | Default archive backend                     |
| `NEWSNEWT_TIMEOUT_SECONDS` | `300`          | Global timeout per request (seconds)        |
| `NEWSNEWT_LOG_LEVEL`       | `"INFO"`       | Log verbosity (DEBUG, INFO, WARNING, ERROR) |
| `TZ`                       | -              | Timezone for logs (recommended: UTC)        |

### Configuration Files

- **Location:** `config/` directory
- **`.env.sample`:** Template with all variables documented
- **`.env`:** Actual configuration (git-ignored)

---

## Logging

### Log Structure

All logs include:

- Timestamp (ISO 8601 UTC)
- Log level
- URL (sanitized if needed)
- Archive service and flags
- Outcome (success or error code)
- Request duration

### Log Location

- **Directory:** `logs/` (root level)
- **File:** `newsnewt.log` (rotating)
- **Rotation:** Configurable size and backup count

### Log Levels

- **DEBUG:** Detailed diagnostic information
- **INFO:** General informational messages (default)
- **WARNING:** Warning messages
- **ERROR:** Error conditions

---

## Request Processing Flow

```
1. Receive POST /article request
   ↓
2. Validate request (URL format, optional fields)
   ↓
3. Resolve archive service (from request or env)
   ↓
4. Apply rate limiting (5-second minimum interval)
   ↓
5. Archive URL (or find existing snapshot)
   ├─→ On timeout: Return ARCHIVE_TIMEOUT error (500)
   ├─→ On failure: Return ARCHIVE_FAILURE error (500)
   └─→ On success: Continue
   ↓
6. Fetch archived HTML from archive URL
   ↓
7. Extract article content using trafilatura
   ├─→ On failure: Return EXTRACTION_FAILURE error (500)
   └─→ On success: Continue
   ↓
8. Format and return JSON response (200 OK)
```

---

## File Structure

```
NewsNewt/
├── src/
│   └── newsnewt/
│       ├── __init__.py
│       ├── api.py              # FastAPI application and endpoints
│       ├── archive.py          # Archive.is integration
│       ├── config.py           # Configuration management
│       ├── extractor.py        # Content extraction (trafilatura)
│       ├── logging_config.py  # Logging setup
│       ├── main.py             # Application entry point
│       ├── models.py           # Pydantic models
│       ├── rate_limit.py       # Rate limiting for Archive.is
│       └── utils.py            # Utility functions
├── tests/
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_rate_limit.py
│   │   └── test_utils.py
│   └── integration/
│       └── test_api.py
├── config/
│   └── .env.sample             # Configuration template
├── logs/
│   └── newsnewt.log            # Application logs (rotating)
├── docs/                       # Documentation
├── dockerfile                  # Docker container definition
├── compose.yml                 # Docker Compose configuration
├── pyproject.toml              # Python project configuration
└── README.md                   # Project documentation
```

---

## Dependencies

### Core Dependencies

- **fastapi**: HTTP framework
- **pydantic**: Data validation and models
- **httpx**: HTTP client for Archive.is integration and fetching archived pages
- **trafilatura**: Article content extraction
- **uvicorn**: ASGI server
- **python-dotenv**: Environment variable management

### Development Dependencies

- **black** (>=25.11.0): Code formatting
- **ruff** (>=0.14.6): Linting and code quality
- **pytest**: Testing framework
- **pytest-asyncio**: Async testing support (if using FastAPI)

---

## Testing Strategy

### Test Structure

The project uses pytest with comprehensive test coverage:

**Unit Tests (33 tests):**
- URL validation and normalization
- Configuration loading and validation
- Archive service selection logic
- Rate limiting
- Domain extraction

**Integration Tests (10 tests):**
- Full POST /article workflow (mocked)
- Error scenarios (all error codes)
- Health check endpoint
- Root endpoint

**Coverage:** 63% overall, 90%+ on critical paths

See [Testing Documentation](TESTING.md) for detailed information.

---

## Deployment

### Docker Container

- **Base Image:** Python 3.12 slim
- **Port:** 8000 (internal network only)
- **Health Check:** GET /health
- **Volumes:** `logs/` directory for log persistence (optional)

### Docker Compose

```yaml
services:
  newsnewt:
    build: .
    ports:
      - "8000:8000" # Internal network only
    environment:
      - NEWSNEWT_ARCHIVE_SERVICE=archive_is
      - NEWSNEWT_TIMEOUT_SECONDS=300
      - NEWSNEWT_LOG_LEVEL=INFO
      - TZ=UTC
    networks:
      - private_network
```

---

## Security Considerations

1. **Network Isolation:** Service runs in private Docker network only
2. **No Authentication:** Network-level security assumed
3. **Input Validation:** All URLs validated before processing
4. **Timeout Protection:** Prevents resource exhaustion
5. **Error Information:** Sanitized error messages (no sensitive data)

---

## Performance Considerations

1. **Timeouts:** Configurable per-request timeout (default 300s)
2. **Batch Processing:** Designed for n8n batch workflows
3. **No Caching:** Stateless service, no request caching
4. **Resource Usage:** Minimal memory footprint, single-threaded

---

## Rate Limiting

NewsNewt includes built-in rate limiting for Archive.is:
- Minimum 5-second interval between archive requests
- Prevents 429 (Too Many Requests) errors
- Async-safe with lock mechanism
- Automatic delay when needed

See `src/newsnewt/rate_limit.py` for implementation details.
