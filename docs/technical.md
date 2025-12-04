# Technical Reference

This document provides detailed technical information about the NewsNewt API, configuration options, and implementation details.

## API Reference

### Base URL

- **Development/Local**: `http://localhost:3000`
- **Docker Network**: `http://newsnewt:3000` (when accessed from other containers)

All endpoints accept and return `application/json` unless otherwise specified.

---

## Endpoints

### GET /health

Health check endpoint to verify the service is running.

**Request**:

- No parameters required
- No authentication required

**Response**: `200 OK`

```json
{
  "status": "ok"
}
```

**Usage in n8n**:

```
HTTP Request Node:
- Method: GET
- URL: http://newsnewt:3000/health
```

---

### POST /scrape

Scrape a web page with optional CSS selectors for targeted content extraction.

#### Request Schema

```json
{
  "url": "string (required)",
  "selectors": {
    "field_name": {
      "css": "string"
    }
  },
  "timeout_ms": "integer (optional)"
}
```

**Parameters**:

| Field                   | Type    | Required | Description                                        |
| ----------------------- | ------- | -------- | -------------------------------------------------- |
| `url`                   | string  | Yes      | Full URL to scrape (must include protocol)         |
| `selectors`             | object  | No       | CSS selectors for content extraction               |
| `selectors.<field>.css` | string  | No       | CSS selector for a specific field                  |
| `timeout_ms`            | integer | No       | Maximum time to wait for response (default: 30000) |

#### Response Schema

**Success**: `200 OK`

```json
{
  "url": "string",
  "data": {
    "field_name": "extracted value"
  },
  "meta": {
    "status": 200,
    "duration_ms": 1234
  }
}
```

**Error**: `4xx` or `5xx`

```json
{
  "url": "string",
  "data": {},
  "meta": {
    "status": 422,
    "duration_ms": 1234,
    "error_type": "captcha_detected",
    "error_message": "CAPTCHA detected on page"
  }
}
```

**Response Fields**:

| Field                | Type         | Description                                       |
| -------------------- | ------------ | ------------------------------------------------- |
| `url`                | string       | The URL that was scraped                          |
| `data`               | object       | Extracted content as key-value pairs              |
| `meta.status`        | integer      | HTTP-like status code for the scrape operation    |
| `meta.duration_ms`   | integer      | Time taken to complete the scrape in milliseconds |
| `meta.error_type`    | string\|null | Error type if scraping failed                     |
| `meta.error_message` | string\|null | Detailed error message if scraping failed         |

#### Status Codes

| Code  | Meaning          | Description                     |
| ----- | ---------------- | ------------------------------- |
| `200` | Success          | Page scraped successfully       |
| `408` | Timeout          | Request exceeded timeout limit  |
| `422` | CAPTCHA Detected | CAPTCHA found on target page    |
| `500` | Scraping Error   | General scraping error occurred |

#### Error Types

| Error Type         | Status Code | Description                              |
| ------------------ | ----------- | ---------------------------------------- |
| `captcha_detected` | 422         | A CAPTCHA was detected on the page       |
| `timeout`          | 408         | The scraping operation timed out         |
| `scraping_error`   | 500         | A general error occurred during scraping |

---

## Request Examples

### Basic Scrape (No Selectors)

When no selectors are provided, the service attempts to extract common page elements:

```bash
curl -X POST http://localhost:3000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article"
  }'
```

**Response**:

```json
{
  "url": "https://example.com/article",
  "data": {
    "title": "Example Article Title",
    "content": "Article content text..."
  },
  "meta": {
    "status": 200,
    "duration_ms": 2341
  }
}
```

### Targeted Extraction with Selectors

Extract specific fields using CSS selectors:

```bash
curl -X POST http://localhost:3000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "selectors": {
      "title": {"css": "h1.article-title"},
      "author": {"css": ".author-name"},
      "date": {"css": "time"},
      "content": {"css": "article.content"},
      "tags": {"css": ".tag"}
    }
  }'
```

**Response**:

```json
{
  "url": "https://example.com/article",
  "data": {
    "title": "Example Article Title",
    "author": "John Doe",
    "date": "2024-12-02",
    "content": "Full article text...",
    "tags": "Technology"
  },
  "meta": {
    "status": 200,
    "duration_ms": 2156
  }
}
```

### Meta Tag Extraction

Extract content from meta tags:

```bash
curl -X POST http://localhost:3000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "selectors": {
      "title": {"css": "meta[property=\"og:title\"]"},
      "description": {"css": "meta[property=\"og:description\"]"},
      "image": {"css": "meta[property=\"og:image\"]"}
    }
  }'
```

### Custom Timeout

Set a longer timeout for slow-loading pages:

```bash
curl -X POST http://localhost:3000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://slow-site.example.com",
    "timeout_ms": 60000
  }'
```

### CAPTCHA Response Example

When a CAPTCHA is detected:

```json
{
  "url": "https://protected-site.example.com",
  "data": {},
  "meta": {
    "status": 422,
    "duration_ms": 1823,
    "error_type": "captcha_detected",
    "error_message": "CAPTCHA detected on page"
  }
}
```

---

## n8n Integration

### HTTP Request Node Configuration

**Basic Configuration**:

```
Method: POST
URL: http://newsnewt:3000/scrape
Content Type: application/json
```

**Body (JSON)**:

```json
{
  "url": "{{$json.article_url}}",
  "selectors": {
    "title": { "css": "h1" },
    "content": { "css": "article" }
  }
}
```

**Response Handling**:

- Response Format: JSON
- Extract nested data: `{{$json.data.title}}`
- Check for errors: `{{$json.meta.error_type}}`

### Workflow Example

```
Trigger (Schedule)
    ↓
Set URLs Node (list of URLs to scrape)
    ↓
Loop over items
    ↓
HTTP Request (NewsNewt scrape)
    ↓
IF Node (check meta.status === 200)
    ↓ Success           ↓ Error
Store Data       Log Error / Retry
```

### Error Handling in n8n

Use an IF node to check for errors:

```javascript
// Condition: Success
{{$json.meta.status}} === 200

// Condition: CAPTCHA
{{$json.meta.error_type}} === "captcha_detected"

// Condition: Timeout
{{$json.meta.error_type}} === "timeout"
```

---

## Extraction Strategies

### Automatic Fallbacks

When a selector fails to match, the service tries common alternatives:

#### Title Fallbacks

1. User-provided selector
2. `h1`
3. `.article-title`
4. `.entry-title`
5. `.post-title`
6. `[itemprop='headline']`
7. `meta[property='og:title']`

#### Content Fallbacks

1. User-provided selector
2. `article`
3. `main`
4. `.article-body`
5. `.entry-content`
6. `.post-content`
7. `[role='main']`
8. `[itemprop='articleBody']`

#### Author Fallbacks

1. User-provided selector
2. `.author`
3. `.author-name`
4. `[rel='author']`
5. `[itemprop='author']`
6. `meta[name='author']`

#### Date Fallbacks

1. User-provided selector
2. `time`
3. `.published-date`
4. `.post-date`
5. `[itemprop='datePublished']`
6. `meta[property='article:published_time']`

#### Description Fallbacks

1. User-provided selector
2. `.excerpt`
3. `.description`
4. `.summary`
5. `meta[name='description']`
6. `meta[property='og:description']`

### Empty Results

If no match is found for a field, an empty string is returned:

```json
{
  "data": {
    "missing_field": ""
  }
}
```

---

## Popup Dismissal

The service automatically attempts to dismiss common popups and cookie banners before extraction.

### Button Text Patterns

Searches for buttons containing:

- "Accept"
- "Accept all"
- "Agree"
- "OK"
- "Allow"
- "Got it"
- "I agree"
- "Continue"
- "Consent"
- "Allow all"

### Close Button Selectors

Attempts to click:

- `.modal-close`
- `.popup-close`
- `.cookie-close`
- `[aria-label*='close']`
- `[aria-label*='dismiss']`
- `.close-button`
- `button.close`
- `[data-dismiss='modal']`

### Banner Removal

Directly removes common banner elements:

- `#cookie-banner`
- `#cookie-notice`
- `.cookie-notice`
- `.cookie-banner`
- `.gdpr-banner`
- `.consent-banner`

**Note**: Popup dismissal is best-effort. Some sites may have custom implementations that aren't covered.

---

## CAPTCHA Detection

The service detects CAPTCHAs using multiple methods:

### Keyword Detection

Scans page text for:

- "captcha"
- "recaptcha"
- "hcaptcha"
- "verify you are human"
- "verify you're human"
- "security check"
- "prove you're not a robot"
- "cloudflare"

### Iframe Detection

Checks for CAPTCHA-related iframes:

- `google.com/recaptcha`
- `hcaptcha.com`

### Element Detection

Searches for CAPTCHA elements:

- `.g-recaptcha`
- `#g-recaptcha`
- `.h-captcha`
- `#h-captcha`
- `[data-sitekey]`
- `iframe[src*='recaptcha']`
- `iframe[src*='hcaptcha']`

When detected, returns:

```json
{
  "meta": {
    "status": 422,
    "error_type": "captcha_detected",
    "error_message": "CAPTCHA detected on page"
  }
}
```

---

## Configuration

### Environment Variables

Configure the service via environment variables in `compose.yml`:

#### CRAWL_CONCURRENCY

Maximum number of concurrent scraping operations.

- **Type**: Integer
- **Default**: `3`
- **Range**: `1-10` (higher values require more resources)
- **Example**: `CRAWL_CONCURRENCY=5`

**Impact**:

- Low (1-2): Conservative, lower resource usage, slower throughput
- Medium (3-5): Balanced for typical workloads
- High (6+): Aggressive, requires significant CPU/memory

#### LOG_LEVEL

Logging verbosity level.

- **Type**: String
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **Example**: `LOG_LEVEL=DEBUG`

**Levels**:

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages for potential issues
- `ERROR`: Error messages only

#### PLAYWRIGHT_HEADLESS

Run browser in headless mode (no visible UI).

- **Type**: Boolean
- **Default**: `true`
- **Options**: `true`, `false`
- **Example**: `PLAYWRIGHT_HEADLESS=false`

**Usage**:

- `true`: Production mode, no GUI (default)
- `false`: Development/debugging, visible browser window

#### ENABLE_STEALTH

Enable stealth mode to avoid CAPTCHA detection.

- **Type**: Boolean
- **Default**: `true`
- **Options**: `true`, `false`
- **Example**: `ENABLE_STEALTH=true`

**Features**:

- Modifies browser fingerprint
- Hides automation indicators
- Mimics real user behavior
- Reduces CAPTCHA trigger rate

**When to disable**:

- Debugging stealth-related issues
- Sites that don't implement detection
- When using authenticated sessions

---

## Logging

### Log Format

All logs follow a consistent format for easy parsing:

```
TIMESTAMP - LOGGER_NAME - LEVEL - MESSAGE
```

**Example Startup Logs**:

```
2024-12-02 10:30:00 - app.main - INFO - ============================================================
2024-12-02 10:30:00 - app.main - INFO - NewsNewt Scraper Service Starting
2024-12-02 10:30:00 - app.main - INFO - ============================================================
2024-12-02 10:30:00 - app.main - INFO - Configuration:
2024-12-02 10:30:00 - app.main - INFO -   - Log Level: INFO
2024-12-02 10:30:00 - app.main - INFO -   - Headless Mode: True
2024-12-02 10:30:00 - app.main - INFO -   - Stealth Mode: True
2024-12-02 10:30:00 - app.main - INFO -   - Max Concurrency: 3
2024-12-02 10:30:00 - app.main - INFO - ------------------------------------------------------------
2024-12-02 10:30:01 - app.main - INFO - ✓ Stealth mode enabled - Anti-detection measures active
2024-12-02 10:30:01 - app.main - INFO - ✓ Crawlee crawler initialized successfully
2024-12-02 10:30:01 - app.main - INFO - ============================================================
2024-12-02 10:30:01 - app.main - INFO - 🚀 NewsNewt ready to accept scraping requests on port 3000
2024-12-02 10:30:01 - app.main - INFO - ============================================================
```

**Example Successful Scrape (INFO level)**:

```
2024-12-02 10:30:45 - app.main - INFO - 📥 [abc-123] New scrape request - URL: https://example.com/article | Selectors: 2 | Timeout: 30.0s
2024-12-02 10:30:46 - app.main - INFO - 🔄 [abc-123] Processing: https://example.com/article
2024-12-02 10:30:47 - app.extraction - INFO - 🍪 Dismissed popup - Clicked button: 'Accept'
2024-12-02 10:30:47 - app.extraction - INFO - ✓ Popup dismissal complete - Clicked: 1, Removed: 0
2024-12-02 10:30:47 - app.extraction - INFO - ✓ Field 'title': Found with provided selector (length: 45)
2024-12-02 10:30:48 - app.extraction - INFO - ✓ Field 'content': Found with provided selector (length: 3421)
2024-12-02 10:30:48 - app.extraction - INFO - 📊 Extraction summary: 2/2 field(s) extracted successfully
2024-12-02 10:30:48 - app.main - INFO - ✅ [abc-123] Success - Extracted 2 field(s) in 2156ms
2024-12-02 10:30:48 - app.main - INFO - 📤 [abc-123] Returning successful response - Duration: 2156ms
```

**Example with Fallbacks (DEBUG level)**:

```
2024-12-02 10:31:00 - app.main - DEBUG - [def-456] Waiting for page to load...
2024-12-02 10:31:01 - app.main - DEBUG - [def-456] Page loaded successfully
2024-12-02 10:31:01 - app.main - DEBUG - [def-456] Attempting to dismiss popups...
2024-12-02 10:31:01 - app.extraction - DEBUG - Scanning for popup buttons with 10 text patterns...
2024-12-02 10:31:01 - app.extraction - DEBUG - No popups or banners found on page
2024-12-02 10:31:01 - app.main - DEBUG - [def-456] Checking for CAPTCHA...
2024-12-02 10:31:01 - app.extraction - DEBUG - Starting CAPTCHA detection scan...
2024-12-02 10:31:01 - app.extraction - DEBUG - ✓ No CAPTCHA detected - page is accessible
2024-12-02 10:31:01 - app.main - DEBUG - [def-456] No CAPTCHA detected
2024-12-02 10:31:01 - app.extraction - DEBUG - Extracting 1 field(s) with custom selectors
2024-12-02 10:31:01 - app.extraction - DEBUG - Trying field 'title' with selector: .article-heading
2024-12-02 10:31:01 - app.extraction - DEBUG - Selector failed for 'title': Element not found
2024-12-02 10:31:01 - app.extraction - DEBUG - Trying 6 fallback(s) for 'title'
2024-12-02 10:31:01 - app.extraction - INFO - ✓ Field 'title': Found with fallback #1: h1 (length: 52)
2024-12-02 10:31:01 - app.extraction - INFO - 📊 Extraction summary: 1/1 field(s) extracted successfully
```

**Example CAPTCHA Detection**:

```
2024-12-02 10:32:00 - app.main - INFO - 🔄 [ghi-789] Processing: https://protected-site.com
2024-12-02 10:32:01 - app.extraction - DEBUG - Starting CAPTCHA detection scan...
2024-12-02 10:32:01 - app.extraction - WARNING - 🛡️  CAPTCHA DETECTED - Keyword found in page text: 'recaptcha'
2024-12-02 10:32:01 - app.extraction - INFO - 💡 Suggestion: Enable stealth mode or reduce concurrency to avoid CAPTCHAs
2024-12-02 10:32:01 - app.main - WARNING - 🛡️  [ghi-789] CAPTCHA detected - Try enabling stealth mode or reduce concurrency
2024-12-02 10:32:01 - app.main - INFO - 📤 [ghi-789] Returning error response - Status: 422 | Type: captcha_detected
```

**Example Timeout**:

```
2024-12-02 10:33:00 - app.main - INFO - 📥 [jkl-012] New scrape request - URL: https://slow-site.com | Selectors: 0 | Timeout: 10.0s
2024-12-02 10:33:00 - app.main - DEBUG - [jkl-012] Queueing request to crawler...
2024-12-02 10:33:00 - app.main - DEBUG - [jkl-012] Waiting for result (timeout: 10.0s)...
2024-12-02 10:33:10 - app.main - ERROR - ⏱️  [jkl-012] Timeout after 10.0s - Try increasing timeout_ms or check if site is responsive
```

### Log Locations

- **Console/STDOUT**: All logs (captured by Docker)
- **File**: `/app/logs/` directory (mounted as volume)

### Log Levels by Component

| Component        | DEBUG             | INFO                  | WARNING        | ERROR               |
| ---------------- | ----------------- | --------------------- | -------------- | ------------------- |
| `app.main`       | Request details   | Request lifecycle     | Config issues  | Fatal errors        |
| `app.extraction` | Selector attempts | Successful extraction | Fallback usage | Extraction failures |
| `crawlee`        | Internal state    | Crawler events        | Retries        | Crashes             |

---

## Performance

### Typical Timings

| Scenario                 | Duration                  |
| ------------------------ | ------------------------- |
| Simple static page       | 500-1500ms                |
| News article (medium JS) | 1500-3000ms               |
| Heavy SPA                | 3000-5000ms               |
| Slow/timeout site        | 30000ms (default timeout) |

### Resource Usage (per concurrent scrape)

| Resource | Usage                    |
| -------- | ------------------------ |
| CPU      | 200-300% (per browser)   |
| Memory   | 200-500 MB (per browser) |
| Disk I/O | Minimal                  |
| Network  | Depends on page size     |

### Optimization Tips

1. **Increase Concurrency**: If CPU/memory allows, raise `CRAWL_CONCURRENCY`
2. **Reduce Timeout**: Lower `timeout_ms` for faster failure on slow sites
3. **Disable Stealth**: If not needed, set `ENABLE_STEALTH=false` for slight speed boost
4. **Target Selectors**: Provide specific selectors to avoid fallback attempts

---

## Troubleshooting

### Reading Log Messages

The service uses emojis and clear messages to help diagnose issues quickly:

| Emoji | Meaning | Level |
| ----- | ------- | ----- |
| 🚀 | Service started successfully | INFO |
| 📥 | New scrape request received | INFO |
| 🔄 | Processing page | INFO |
| 🍪 | Popup/cookie banner action | INFO |
| ✓ | Success/completion marker | INFO/DEBUG |
| ✅ | Successful extraction | INFO |
| 📤 | Sending response | INFO |
| 📊 | Statistics/summary | INFO |
| ⚠️  | Warning or missing data | WARNING |
| 🛡️  | CAPTCHA detected | WARNING |
| 💡 | Helpful suggestion | INFO |
| ❌ | Error occurred | ERROR |
| ⏱️  | Timeout occurred | ERROR |
| 🛑 | Shutdown initiated | INFO |

**Request IDs**: Every request has a unique ID (e.g., `[abc-123]`) that appears in all related log messages, making it easy to trace a request through its lifecycle.

**Log Levels**:
- `DEBUG`: Detailed step-by-step execution (enable with `LOG_LEVEL=DEBUG`)
- `INFO`: Normal operations and request lifecycle
- `WARNING`: Potential issues (CAPTCHAs, missing data, fallbacks)
- `ERROR`: Actual failures (timeouts, exceptions)

### Common Issues

#### 1. CAPTCHA Detected on Every Request

**Symptoms**: All requests return `error_type: "captcha_detected"`

**Solutions**:

- Ensure `ENABLE_STEALTH=true`
- Reduce `CRAWL_CONCURRENCY` to avoid rate limiting
- Check if target site requires authentication
- Consider rotating IP addresses or using proxies

#### 2. Timeout Errors

**Symptoms**: Requests return `error_type: "timeout"`

**Solutions**:

- Increase `timeout_ms` in request body
- Check network connectivity
- Verify target site is accessible
- Reduce `CRAWL_CONCURRENCY` if system is overloaded

#### 3. Empty Data Returned

**Symptoms**: `data: {}` or empty field values

**Solutions**:

- Verify selectors match page structure
- Check if page content loads via JavaScript (needs time)
- Try more specific or alternative selectors
- Enable `LOG_LEVEL=DEBUG` to see extraction attempts

#### 4. Service Crashes or Restarts

**Symptoms**: Container exits or health check fails

**Solutions**:

- Check Docker logs: `docker logs newsnewt`
- Verify sufficient memory allocated
- Reduce `CRAWL_CONCURRENCY`
- Check for Playwright installation issues

### Debug Mode

Enable debug logging:

```yaml
environment:
  - LOG_LEVEL=DEBUG
```

Then check logs:

```bash
docker logs -f newsnewt
```

---

## Development

### Local Development Setup

1. **Install dependencies**:

```bash
uv sync
```

2. **Install Playwright**:

```bash
uv run playwright install chromium --with-deps
```

3. **Run locally**:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

4. **Test endpoint**:

```bash
curl http://localhost:3000/health
```

### Running Tests

```bash
uv run pytest
```

### Code Quality

```bash
# Linting
uv run ruff check src/

# Formatting (check)
uv run ruff format --check src/
```

---

## API Versioning

Current version: **v0.1.0**

The API is currently unversioned. Breaking changes will be documented in release notes.

---

## Limits and Constraints

| Limit                  | Value                              | Notes                     |
| ---------------------- | ---------------------------------- | ------------------------- |
| Max concurrent scrapes | Configured via `CRAWL_CONCURRENCY` | Default: 3                |
| Default timeout        | 30 seconds                         | Configurable per request  |
| Max URL length         | 2048 characters                    | Browser limitation        |
| Response size          | Unlimited                          | Depends on page content   |
| Request rate           | Unlimited                          | No built-in rate limiting |

**Note**: No authentication or rate limiting is implemented. Deploy behind a reverse proxy if these features are required.
