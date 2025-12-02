
## Project overview

Build a self‑hosted “scraping micro‑API” that exposes a small set of HTTP endpoints (FastAPI) which internally use Crawlee for Python with PlaywrightCrawler to fetch and extract structured data from web pages, returning JSON only.[1][2]
The service runs in Docker (via docker‑compose) and is consumed from n8n using the HTTP Request node with JSON request/response.[3][4][1]

## Core requirements

- **Self‑hosted service**:
  - Runs as a Docker container, orchestrated via `docker-compose.yml`.[5]
  - Exposes one port (e.g. `8080`) for FastAPI.

- **Scraping capabilities**:
  - Uses **Crawlee for Python** with **PlaywrightCrawler** for JS‑heavy pages.[2]
  - Supports:
    - Single‑URL scrape (primary use case).
    - Optional small multi‑page crawl (e.g. follow article pagination or next links).

- **Output format**:
  - Always responds with `Content-Type: application/json`.
  - For each request returns:
    - `url`
    - `data` (structured fields)
    - `meta` (status code, timestamp, duration, debug info).

- **n8n integration**:
  - Optimized for the n8n HTTP Request node: POST with JSON body, response parsed as JSON.[4][3]
  - Stable URL paths and simple authentication (API key header or basic token).

## API design

All endpoints are `application/json` in and out.

1. `POST /scrape`
   - **Purpose**: Scrape a single page with user‑defined selectors.
   - Request body:
     - `url` (string, required)
     - `selectors` (object, optional): keys are field names, values indicate CSS/XPath or simple extraction rules, e.g.  
       `{"title": {"css": "h1"}, "content": {"css": "article"}}`
     - `render_js` (bool, default `true`): whether to use full Playwright rendering.
     - `wait_until` (string, optional): e.g. `"networkidle"`.
     - `timeout_ms` (int, optional).
   - Response body:
     - `url` (string)
     - `data` (object): extracted fields (strings, arrays, etc.).
     - `meta`: `{ "status": int, "fetched_at": string, "duration_ms": int, "selector_mode": "css" | "xpath" }`.

2. `POST /scrape-news`
   - **Purpose**: Opinionated extraction for news/article pages.
   - Request body:
     - `url` (string)
     - Optional `profile` (string): `"generic"` or a site‑specific profile.
   - Response body (`data`):
     - `title`, `subtitle`, `author`, `published_at`, `content`, `images`, `tags`.

3. `POST /crawl`
   - **Purpose**: Shallow multi‑page crawl (e.g. section or tag pages).
   - Request body:
     - `start_url` (string)
     - `max_pages` (int, default 10)
     - `follow_patterns` (array of regex/substring to decide which links to enqueue)
     - `selectors` (as in `/scrape`).
   - Response body:
     - `items`: array of `{ "url": string, "data": {...}, "meta": {...} }`.
     - `meta`: crawl summary (pages_visited, pages_skipped, errors).

4. **Auth / health**
   - `GET /health` – returns `{ "status": "ok" }` without auth.
   - All other endpoints require `X-API-Key: <token>` or `Authorization: Bearer <token>`.

## Internal architecture

- **FastAPI app**:
  - Follows Crawlee’s “running in a web server” pattern with a `lifespan` function that instantiates and holds a crawler instance and a `requests_to_results` dict shared via `app.state`.[1]
  - Async routes that:
    - Validate payload.
    - Register a future / callback with the crawler.
    - Enqueue the URL and await completion.
    - Return JSON.

- **Crawlee setup**:
  - Main crawler: `PlaywrightCrawler` with:
    - Global concurrency limit.
    - Global request timeout.
    - Optional proxy settings.
  - Default handler extracts:
    - DOM snapshot and then applies selectors / news heuristics.
  - For `/crawl`, use Crawlee’s request queue and link extraction logic (select anchors matching `follow_patterns`).[2]

- **Extraction strategies**:
  - **Selector mode**:
    - If `selectors` provided, map each field to a CSS/XPath query and text/attribute extraction.
  - **News mode**:
    - Use heuristics: `<article>`, `<main>`, `meta[property="og:*"]`, date patterns, etc.
    - Allow per‑site overrides via profile definitions.

- **Error handling**:
  - Normalize network, timeout, and DOM errors into JSON:
    - `meta.error_type`, `meta.error_message`, `meta.http_status` (if available).
  - Never return HTML or stack traces; useful debug info stays in logs.

## Docker & deployment

- **Dockerfile**:
  - Base `python:3.12-slim` (or similar).
  - Install system libraries required for Playwright (Chromium, fonts, etc.).
  - Install Python deps: `fastapi[standard]`, `crawlee`, `playwright`, plus any extras.[1][2]
  - Run `playwright install chromium` in build stage or entrypoint.

- **docker-compose.yml**:
  - Single service `scraper-api`:
    - `build: .`
    - `ports: ["8080:8080"]`
    - `environment`: `API_KEY`, `CRAWL_CONCURRENCY`, `PLAYWRIGHT_HEADLESS=true`, proxy settings.
    - Optional resource limits (CPU/memory).
  - (Optional) Attach a shared network and volume if logs or cache are needed.

- **Runtime**:
  - ASGI server: `uvicorn app.main:app --host 0.0.0.0 --port 8080`.
  - Healthcheck configured in Compose using `curl` to `/health`.

## n8n usage pattern

- **HTTP Request node configuration**:[3][4]
  - Method: `POST`.
  - URL: e.g. `http://scraper-api:8080/scrape` (inside Docker network) or external host.
  - Authentication: custom header `X-API-Key`.
  - Body:
    - Mode: JSON.
    - Example body:
      ```json
      {
        "url": "https://example.com/news/123",
        "selectors": {
          "title": { "css": "h1.article-title" },
          "content": { "css": "article" }
        },
        "render_js": true
      }
      ```
  - Response:
    - Response format: JSON.
    - Use `Field Containing Data` if you want to only pass `data` or `items` into later nodes.

- **Typical workflows**:
  - Trigger → HTTP Request (`/scrape-news`) → process JSON → store in DB.
  - Loop over a list of URLs items, each going through `/scrape`.

## Non‑functional requirements

- **Performance & concurrency**:
  - Configurable `CRAWL_CONCURRENCY` (e.g. 3–5) via env, exposed in Docker compose.[6]
  - Typical single page scrape target: <3–5 seconds on average news site.

- **Observability**:
  - Structured logs (JSON) per request: URL, status, duration, error.
  - Optional basic metrics: total requests, failures, average latency.

- **Security**:
  - Simple key‑based auth is acceptable for internal n8n use.
  - Allow IP allow‑listing / reverse proxy hardening (Nginx, Traefik) out of scope but considered.

If you want, the next step can be a concrete skeleton: `app/main.py` with the FastAPI + Crawlee `lifespan` pattern, and sample Dockerfile and docker‑compose tailored to your stack.

[1](https://crawlee.dev/python/docs/guides/running-in-web-server)
[2](https://crawlee.dev/python/docs/quick-start)
[3](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/)
[4](https://n8n.io/integrations/http-request/)
[5](https://stackoverflow.com/questions/65233680/run-fastapi-inside-docker-container)
[6](https://www.reddit.com/r/n8n/comments/1l1i5mp/i_made_a_crawlee_server_built_specifically_for/)
[7](https://www.youtube.com/watch?v=c5dw_jsGNBk)
[8](https://automategeniushub.com/mastering-the-n8n-http-request-node/)
[9](https://community.n8n.io/t/calling-a-python-script-from-n8n/82900)
[10](https://docs.apify.com/platform/integrations/n8n/website-content-crawler)
