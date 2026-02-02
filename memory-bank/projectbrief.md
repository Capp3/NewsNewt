# Project Brief: NewsNewt

## Overview

NewsNewt is a self-hosted web scraping microservice designed for integration with n8n workflows. Built with FastAPI and Crawlee, it provides Playwright-powered JavaScript rendering, intelligent content extraction, and automatic popup handling.

## Core Purpose

- **Primary Use Case**: Scrape web pages and extract structured data for n8n automation workflows
- **Target Users**: n8n users who need reliable web scraping capabilities
- **Deployment**: Docker container via docker-compose, single service on port 3000

## Key Features

1. **Playwright-Powered**: Full JavaScript rendering for modern web applications
2. **Stealth Mode**: Configurable anti-detection measures to reduce CAPTCHA triggers
3. **Intelligent Extraction**: Flexible CSS selector matching with automatic fallbacks
4. **Popup Handling**: Automatic dismissal of cookie banners and popups
5. **CAPTCHA Detection**: Identifies CAPTCHAs and returns structured error responses
6. **n8n Optimized**: JSON-only API designed for HTTP Request node integration
7. **Docker Native**: Single-container deployment via docker-compose

## API Design

### POST /scrape
- **Input**: URL, optional CSS selectors, optional timeout
- **Output**: JSON with `url`, `data` (extracted fields), `meta` (status, duration, errors)
- **Error Handling**: Structured JSON errors (CAPTCHA, timeout, scraping errors)

### GET /health
- **Output**: `{"status": "ok"}`

## Architecture Principles

1. **Simplicity**: Single purpose, minimal configuration
2. **Reliability**: Structured error handling, no crashes
3. **Integration**: Designed specifically for n8n workflows
4. **Observability**: Comprehensive logging, health checks
5. **Maintainability**: Clean code, clear separation of concerns

## Technology Stack

- **Runtime**: Python 3.12
- **Package Manager**: UV 0.9.11
- **Web Framework**: FastAPI 0.115+
- **ASGI Server**: Uvicorn 0.32+
- **Crawler Framework**: Crawlee 0.4+
- **Browser Automation**: Playwright Latest
- **Browser**: Chromium Latest
- **Anti-Detection**: playwright-stealth 1.0.6+
- **Validation**: Pydantic 2.0+

## Current Status

- **Version**: 0.1.0
- **Status**: Functional but needs refactoring and debugging
- **Known Issues**: To be documented during refactoring phase

## Non-Functional Requirements

- **Performance**: Target <3-5 seconds per scrape on average news site
- **Concurrency**: Configurable via `CRAWL_CONCURRENCY` (default: 3)
- **Resource Usage**: ~200-500 MB memory per concurrent scrape
- **Security**: Internal service design (no authentication, not for public internet)
