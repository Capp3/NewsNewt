## NewsNewt – Project Brief

### 1. Overview

NewsNewt is a small, single-purpose Python microservice that:

- Accepts a news article URL over HTTP.
- Ensures the article is archived via a third-party web archive (Archive.is / Archive.today).
- Fetches the archived page and extracts the main article content.
- Returns a clean JSON representation of the article, optimized for downstream LLM consumption.

The service is designed to be used primarily from n8n workflows and runs as a private Dockerized microservice inside a controlled network. It is intentionally minimal and focused, with a strong bias against feature creep.

---

### 2. Goals and Non‑Goals

- **Primary goal**: Provide a simple, reliable, and consistent way to convert a news article URL into structured JSON via an archive-first workflow.
- **Secondary goal**: Make the service easy to operate in containerized environments with clear configuration and logging.

- **Non‑goals**:
  - No direct scraping of the live site if the archive service fails (archive-first is mandatory).
  - No WARC file persistence or local archival storage.
  - No generic web-page or non-news extraction; the primary target is news articles.
  - No public, internet-facing API management (authentication, rate limiting, quotas) beyond what the private environment provides.
  - No LLM-based content extraction or enrichment; extraction must be purely Python-library-based.

---

### 3. Primary Use Case

- **Use case: n8n RSS processing pipeline**
  - n8n scrapes RSS feeds and identifies candidate news article URLs.
  - For each URL, n8n calls NewsNewt via an HTTP node.
  - NewsNewt:
    - Archives the URL (or finds the latest archived copy) using Archive.is / Archive.today.
    - Fetches the archived HTML.
    - Extracts the main article body text and core metadata.
    - Returns a JSON object.
  - n8n stores or processes the JSON further, including possible LLM-based summarization or analysis.

NewsNewt itself is a “one-trick pony”: given a URL, it returns an article JSON or a clear error.

---

### 4. Functional Requirements

#### 4.1 High-Level Behavior

- The service MUST:

  - Accept an HTTP POST request containing at least one required field: the article URL.
  - Resolve the effective archive service and optionally whether to force a new archive.
  - Use the archive service (Archive.is / Archive.today) to obtain an archived snapshot URL:
    - Prefer the **most recent existing snapshot** when not forcing a re-archive.
    - Trigger a **new archive operation** when no snapshot is available or when explicitly requested by the client.
  - Fetch the archived HTML using the resolved archive URL.
  - Extract:
    - Main article body text (required for success).
    - Optional metadata (title, byline, publish timestamp, language, source domain).
  - Return JSON formatted output on success.
  - Return a structured error JSON with appropriate HTTP status on failure.

- The service MUST treat each request as **all-or-nothing**:
  - If any critical step (archiving or extraction) fails, the service returns an error response.
  - It MUST NOT return partially successful article data.

#### 4.2 Input Contract (Request)

- **Endpoint**: `POST /article`
- **Content-Type**: `application/json`

- **Required field**:

  - `url` (string)
    - The original article URL.
    - MUST be a valid `http` or `https` URL.

- **Optional fields**:
  - `force_archive` (boolean, default: `false`)
    - `false`: Use the latest existing archive snapshot if one exists; otherwise create a new one.
    - `true`: Always trigger creation of a new archive snapshot, even if one already exists.
  - `archive_service` (string, default: `"auto"`)
    - Allowed values:
      - `"auto"` – use service configured via environment (see configuration).
      - `"archive_is"` – explicitly request Archive.is / Archive.today.
      - `"archive_today"` – alias, functionally identical to `"archive_is"` in early versions.

**Example request**

```json
{
  "url": "https://example.com/news/article-123",
  "force_archive": false,
  "archive_service": "auto"
}
```

#### 4.3 Output Contract (Success Response)

- **Status Code**: `200 OK`
- **Content-Type**: `application/json`

- **Required fields**:

  - `url` (string)
    - Original article URL.
  - `archive_url` (string)
    - URL of the archive snapshot used for extraction.
  - `body_text` (string)
    - Plain-text version of the main article body.
    - MUST be non-empty for a successful response.

- **Optional / nullable fields**:
  - `title` (string | null)
  - `byline` (string | null) – e.g. author name.
  - `published_at` (string | null)
    - ISO 8601 UTC timestamp when available (e.g. `"2025-11-25T10:35:00Z"`).
  - `source_domain` (string | null)
    - Domain extracted from the original URL (e.g. `"example.com"`).
  - `language` (string | null)
    - Language code (e.g. `"en"`), when detectable from metadata or extraction library.

**Example success response**

```json
{
  "url": "https://example.com/news/article-123",
  "archive_url": "https://archive.is/abcdE",
  "title": "Example Headline",
  "byline": "Jane Doe",
  "published_at": "2025-11-25T10:35:00Z",
  "body_text": "Full article text here...",
  "source_domain": "example.com",
  "language": "en"
}
```

#### 4.4 Error Handling Contract

- **Envelope**

All error responses MUST use a standard envelope:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable explanation",
    "details": {
      "...": "optional structured context"
    }
  }
}
```

- **Error codes and HTTP statuses**:

  - `INVALID_URL` – `400 Bad Request`
    - URL is missing, malformed, or uses an unsupported scheme.
  - `UNSUPPORTED_ARCHIVE_SERVICE` – `400 Bad Request`
    - `archive_service` is not one of the allowed values.
  - `ARCHIVE_TIMEOUT` – `500 Internal Server Error`
    - Archiving did not complete within the configured timeout.
  - `ARCHIVE_FAILURE` – `500 Internal Server Error`
    - Archive service interaction failed (non-2xx, unexpected response, or similar).
  - `EXTRACTION_FAILURE` – `500 Internal Server Error`
    - Article extraction library did not produce a valid body text.
  - `INTERNAL_ERROR` – `500 Internal Server Error`
    - Fallback for unexpected/unhandled errors.

- **Example error**

```json
{
  "error": {
    "code": "ARCHIVE_TIMEOUT",
    "message": "Archiving operation exceeded configured timeout of 300 seconds",
    "details": {
      "url": "https://example.com/news/article-123",
      "archive_service": "archive_is"
    }
  }
}
```

#### 4.5 Health Check

- **Endpoint**: `GET /health`

  - Returns minimal JSON on success:

  ```json
  {
    "status": "ok"
  }
  ```

  - Used for basic container health checks and service discovery within the Docker network.

---

### 5. Non‑Functional Requirements

#### 5.1 Performance and Timeouts

- End-to-end processing time SHOULD be configurable via an environment variable:
  - `NEWSNEWT_TIMEOUT_SECONDS` (default: `300` seconds).
- The service MUST:
  - Enforce this timeout across archiving, fetching, and extraction steps.
  - Fail with `ARCHIVE_TIMEOUT` if the limit is exceeded.
- The system is intended for batch use driven by n8n; extremely high throughput or low latency are not primary goals.

#### 5.2 Reliability

- Each request MUST be independent and deterministic given:
  - The input URL.
  - The chosen archive service.
  - The current state of the archive provider.
- The system SHOULD:
  - Return clear, actionable error messages for operational debugging.
  - Avoid partial successes; either the article is fully extracted or an error is returned.

#### 5.3 Security

- The service is intended to run inside a **private Docker network**:
  - No public internet exposure.
  - No direct user authentication is required at the service level.
- All outgoing requests SHOULD only target:
  - The chosen archive service.
  - The archive snapshot URLs returned by that service.

#### 5.4 Maintainability

- Code should remain minimal and focused around:
  - Request validation.
  - Archive service interaction.
  - Extraction and JSON mapping.
  - Logging and error handling.
- Avoid unnecessary dependencies; keep the runtime environment as light as practicable while still supporting robust article extraction.

#### 5.5 Observability

- Logging MUST include:
  - Timestamp.
  - Log level.
  - URL (or a safe representation).
  - Archive service and `force_archive` flag.
  - Outcome (success or specific error code).
  - Request duration.
- Log level MUST be configurable via environment variable:
  - `NEWSNEWT_LOG_LEVEL` (e.g. `DEBUG`, `INFO`, `WARNING`, `ERROR`).
- Log rotation SHOULD be enabled using rotating file handlers or similar:
  - Sensible defaults for file size and backup count.

---

### 6. System Architecture

#### 6.1 Components

- **NewsNewt Service**

  - Python 3.12 application running in a single Docker container.
  - Exposes an HTTP API internally within the Docker network.
  - Responsible for:
    - Validating and normalizing input.
    - Interacting with archive services (via `archivenow` and related tooling).
    - Fetching archived HTML.
    - Extracting article content.
    - Formatting and returning JSON responses.

- **Archive Provider(s)**

  - Archive.is / Archive.today.
  - Accessed via:
    - `archivenow` library.
    - Direct HTTP calls to the archive snapshot URLs.

- **n8n (Client / Orchestrator)**
  - External system that:
    - Provides URLs from RSS or other sources.
    - Calls NewsNewt via HTTP.
    - Consumes and stores the returned JSON for further processing (e.g. LLM flows).

#### 6.2 Data Flow

1. n8n sends a `POST /article` request with JSON payload containing `url` and optional flags.
2. NewsNewt:
   - Validates request.
   - Resolves archive service choice.
   - Locates or creates an archive snapshot.
   - Fetches the archived page.
   - Extracts article content.
3. NewsNewt returns either:
   - A structured JSON article object (on success).
   - A structured error JSON (on failure).
4. n8n uses the returned JSON downstream.

---

### 7. Technology and Dependencies

- **Language**: Python 3.12 (runtime image base).
- **Core libraries**:
  - `archivenow` – interacting with web archive services.
  - A Python article extraction library (to be selected) for robust news article content extraction.
- **Supporting libraries**:
  - HTTP client stack (standard library or a well-known HTTP client library).
  - Logging and configuration utilities.

No LLM or heavy ML dependencies are expected; extraction must be rule-/heuristics-based via Python libraries.

---

### 8. Configuration and Environment

#### 8.1 Environment Variables

- `NEWSNEWT_ARCHIVE_SERVICE`

  - Default archival backend; values:
    - `"archive_is"` (recommended default for Archive.is / Archive.today).
  - Used when the request-level `archive_service` is `"auto"` or omitted.

- `NEWSNEWT_TIMEOUT_SECONDS`

  - Global timeout for a single request (archive + fetch + extraction).
  - Default: `300` seconds (5 minutes).

- `NEWSNEWT_LOG_LEVEL`

  - Log verbosity; defaults to `"INFO"`.
  - Common values: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`.

- `TZ`
  - Timezone configuration for logs and any local-time operations.
  - Recommended to use UTC in logs and convert to local time only when needed externally.

#### 8.2 Deployment Model

- The service is designed to run:
  - As a single container in a Docker environment.
  - Connected to a private Docker network shared with n8n.
- `docker-compose.yml` (or equivalent) can define:
  - Internal port exposure (e.g. `8000`).
  - Environment variables listed above.
  - Network configuration (no public port exposure required by default).

---

### 9. Testing and Acceptance Criteria

#### 9.1 Test Categories

- **Unit tests**

  - URL validation and normalization.
  - Archive service selection logic.
  - Error mapping and JSON response structure.

- **Integration tests**

  - Interaction with archive services:
    - Successful snapshot lookup.
    - Successful new archive creation.
    - Timeout and failure scenarios (mocked or sandboxed).
  - Article extraction correctness for representative news sites.

- **End-to-end tests**
  - Full path from `POST /article` to JSON response for:
    - Valid URLs with existing archives.
    - Valid URLs requiring new archives.
    - Invalid URLs and unsupported archive services.

#### 9.2 Acceptance Criteria (MVP)

- Given a valid news article URL and a reachable archive service:

  - The service returns `200 OK` with a JSON body containing:
    - Non-empty `body_text`.
    - Populated `url` and `archive_url`.
  - Optional metadata fields are filled when reasonably available.

- Given an invalid URL:

  - The service returns `400 Bad Request` with `error.code = "INVALID_URL"`.

- Given an invalid `archive_service` value:

  - The service returns `400 Bad Request` with `error.code = "UNSUPPORTED_ARCHIVE_SERVICE"`.

- When archiving or extraction cannot complete within `NEWSNEWT_TIMEOUT_SECONDS`:

  - The service returns `500 Internal Server Error` with `error.code = "ARCHIVE_TIMEOUT"` or `EXTRACTION_FAILURE` as appropriate.

- Logging is present, correctly formatted, and respects `NEWSNEWT_LOG_LEVEL`.

---

### 10. Future Enhancements (Out of Scope for MVP)

The following items are explicitly out of scope for the first production version but may be considered later:

- Support for additional archive providers or an abstraction layer for multiple archives.
- More advanced URL normalization and de-duplication strategies.
- Enhanced metadata extraction (tags, categories, section hierarchy).
- Custom n8n node wrapping this API.
- Built-in rate limiting or domain-level politeness policies.
- Optional support for non-news content with different extraction strategies.

These should only be revisited once the core “news URL → archive → JSON” workflow is stable and proven useful in production.
