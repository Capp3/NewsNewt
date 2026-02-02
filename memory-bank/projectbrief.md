# NewsNewt Project Brief

## Project Overview

NewsNewt is a self-hosted web scraping microservice built with FastAPI and Crawlee, designed for integration with n8n workflows. The service uses Playwright for JavaScript rendering and supports stealth mode to reduce bot detection.

## Core Technology Stack

- **Runtime**: Python 3.12
- **Package Manager**: uv (not pip)
- **Dependency Config**: pyproject.toml
- **Web Framework**: FastAPI 0.115+
- **Crawler Framework**: Crawlee 0.4+ (PlaywrightCrawler)
- **Browser Automation**: Playwright Latest (Chromium)
- **Anti-Detection**: playwright-stealth 1.0.6+
- **Container**: Docker with docker-compose

## Dependency Management

**Important**: This project uses `uv` for package management, not `pip`.

- Dependencies are defined in `pyproject.toml`
- Install with: `uv sync`
- Add packages with: `uv add <package-name>`
- Run commands with: `uv run <command>`

## Current Architecture

### Key Components

1. **FastAPI Application** (`src/app/main.py`)

   - Lifespan management for crawler instance
   - Request tracking via app.state
   - Health check endpoint

2. **Crawler** (`src/app/crawler.py`)

   - PlaywrightCrawler with BrowserPool
   - Request handler for processing URLs
   - Current stealth implementation (needs improvement)

3. **Configuration** (`src/app/config.py`)

   - Environment variable management
   - Stealth mode toggle (`ENABLE_STEALTH`)

4. **Extraction** (`src/app/extraction.py`)
   - Popup dismissal
   - Content extraction with fallbacks
   - CAPTCHA detection

## Current Stealth Implementation

The current implementation in `crawler.py` (lines 216-242) uses a workaround:

- Modifies internal `_request_handler` attribute
- Applies stealth AFTER page navigation
- Uses `stealth_async` from `playwright_stealth`

## Issues with Current Implementation

1. **Timing**: Stealth is applied after navigation, which may be too late
2. **Architecture**: Modifies internal Crawlee attributes (fragile)
3. **Best Practices**: According to ZenRows blog, stealth should be applied before navigation

## Project Goals

- Improve stealth mode implementation following best practices
- Ensure stealth is applied at the correct time (before navigation)
- Maintain compatibility with Crawlee's architecture
- Preserve existing functionality
