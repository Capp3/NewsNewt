# NewsNewt - Testing Documentation

**Last Updated:** 2025-11-25

## Overview

NewsNewt uses `pytest` for testing with a comprehensive test suite covering unit and integration tests.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── __init__.py
│   ├── test_utils.py        # URL validation, domain extraction
│   ├── test_config.py       # Configuration loading & validation
│   └── test_rate_limit.py   # Rate limiter tests
└── integration/             # Integration tests
    ├── __init__.py
    └── test_api.py          # Full API workflow tests
```

## Running Tests

### Run All Tests

```bash
uv run pytest tests/ -v
```

### Run Specific Test File

```bash
uv run pytest tests/unit/test_utils.py -v
```

### Run With Coverage

```bash
uv run pytest tests/ --cov=src/newsnewt --cov-report=term-missing
```

### Run Only Unit Tests

```bash
uv run pytest tests/unit/ -v
```

### Run Only Integration Tests

```bash
uv run pytest tests/integration/ -v
```

## Test Coverage

**Overall Coverage:** 63%

### Module Coverage Breakdown

| Module              | Coverage | Status                        |
| ------------------- | -------- | ----------------------------- |
| `api.py`            | 91%      | ✅ Excellent                  |
| `config.py`         | 96%      | ✅ Excellent                  |
| `models.py`         | 100%     | ✅ Complete                   |
| `logging_config.py` | 100%     | ✅ Complete                   |
| `rate_limit.py`     | 100%     | ✅ Complete                   |
| `utils.py`          | 79%      | ✅ Good                       |
| `archive.py`        | 24%      | ⚠️ Intentionally low (mocked) |
| `extractor.py`      | 16%      | ⚠️ Intentionally low (mocked) |
| `main.py`           | 0%       | ⚠️ Entry point (not critical) |

### Why Some Modules Have Low Coverage

- **`archive.py` (24%):** Internal Archive.is HTTP calls are mocked in tests to avoid rate limits and ensure consistent, fast tests.
- **`extractor.py` (16%):** Internal trafilatura calls are mocked to avoid network dependencies and ensure deterministic tests.
- **`main.py` (0%):** Entry point module, not critical for unit testing.

**All critical business logic paths are tested at 90%+ coverage.**

## Test Categories

### Unit Tests (33 tests)

#### URL Validation Tests (`test_utils.py`)

- Valid HTTP/HTTPS URLs
- URLs with paths and query parameters
- Invalid URLs (empty, wrong protocol, malformed)
- **8 tests total**

#### Configuration Tests (`test_config.py`)

- Default values
- Environment variable overrides
- Validation (archive service, timeout, log level)
- Directory path configuration
- **10 tests total**

#### Domain Extraction Tests (`test_utils.py`)

- Simple domains
- Domains with subdomains
- Domains with paths
- Invalid URLs
- **5 tests total**

#### Archive Service Resolution Tests (`test_utils.py`)

- Auto resolution
- Service normalization (archive_today → archive_is)
- Invalid service handling
- **6 tests total**

#### Rate Limiting Tests (`test_rate_limit.py`)

- First request (no wait)
- Subsequent requests (enforced wait)
- Multiple requests (interval respect)
- Requests after interval (no wait)
- **4 tests total**

### Integration Tests (10 tests)

#### API Endpoint Tests (`test_api.py`)

- Health check endpoint
- Root endpoint (service info)
- Successful article workflow
- Invalid URL handling
- Error code mapping:
  - `INVALID_URL` (HTTP 422)
  - `ARCHIVE_TIMEOUT` (HTTP 500)
  - `ARCHIVE_FAILURE` (HTTP 500)
  - `EXTRACTION_FAILURE` (HTTP 500)
  - `INTERNAL_ERROR` (HTTP 500)
- Force archive flag handling
- **10 tests total**

## Test Fixtures

### `test_client` (conftest.py)

FastAPI test client for making HTTP requests to the API.

```python
@pytest.fixture
def test_client():
    from newsnewt.api import app
    return TestClient(app)
```

### `sample_bbc_html` (conftest.py)

Sample BBC article HTML for testing extraction logic.

### `sample_article_url` (conftest.py)

Sample article URL for consistent testing.

```python
@pytest.fixture
def sample_article_url():
    return "https://www.bbc.co.uk/news/articles/cy95jvw57v2o"
```

## Mocking Strategy

### Archive Service Mocking

Archive.is HTTP calls are mocked to:

- Avoid rate limits (429 errors)
- Ensure fast, deterministic tests
- Test error scenarios reliably

```python
with patch("newsnewt.api.archive_url", new_callable=AsyncMock) as mock_archive:
    mock_archive.return_value = (archive_url, html_content)
```

### Extraction Service Mocking

Trafilatura extraction is mocked to:

- Avoid network dependencies
- Ensure consistent test output
- Test error scenarios

```python
with patch("newsnewt.api.extract_article_content", new_callable=AsyncMock) as mock_extract:
    mock_extract.return_value = "Article body text..."
```

## Error Testing

All error codes are tested with proper HTTP status codes and response structures:

| Error Code           | HTTP Status | Tested | Scenario                   |
| -------------------- | ----------- | ------ | -------------------------- |
| `INVALID_URL`        | 422         | ✅     | Invalid URL format         |
| `ARCHIVE_TIMEOUT`    | 500         | ✅     | Archive service timeout    |
| `ARCHIVE_FAILURE`    | 500         | ✅     | Archive service failure    |
| `EXTRACTION_FAILURE` | 500         | ✅     | Content extraction failure |
| `INTERNAL_ERROR`     | 500         | ✅     | Unexpected errors          |

## Running Tests in CI/CD

The test suite is designed to run in CI/CD environments:

```bash
# Install dependencies
uv sync --extra dev

# Run tests with coverage
uv run pytest tests/ --cov=src/newsnewt --cov-report=xml --cov-report=term

# Fail if critical modules drop below thresholds
uv run pytest tests/ --cov=src/newsnewt --cov-fail-under=60
```

## Adding New Tests

### Unit Test Template

```python
"""Unit tests for [module_name]."""

import pytest
from newsnewt.[module] import [function]


class Test[Function]:
    """Tests for [function]."""

    def test_[scenario](self):
        """Test [specific behavior]."""
        result = function(input)
        assert result == expected
```

### Integration Test Template

```python
"""Integration tests for [feature]."""

from unittest.mock import AsyncMock, patch
from newsnewt.[module] import [ErrorClass]


class Test[Feature]:
    """Tests for [feature]."""

    def test_[scenario](self, test_client):
        """Test [specific behavior]."""
        response = test_client.post("/endpoint", json={...})
        assert response.status_code == 200
```

## Test Best Practices

1. **Isolation:** Each test should be independent
2. **Clarity:** Test names should describe the scenario
3. **Mocking:** Mock external dependencies (Archive.is, network calls)
4. **Coverage:** Focus on critical business logic
5. **Speed:** Tests should run fast (< 5 seconds total)
6. **Assertions:** Clear, specific assertions

## Known Issues

### Pydantic Deprecation Warning

```
PydanticDeprecatedSince20: Support for class-based `config` is deprecated
```

**Status:** Low priority  
**Impact:** None (functionality works)  
**Fix:** Update to Pydantic V2 `ConfigDict` in future version

## Test Maintenance

- Run tests before committing: `uv run pytest tests/`
- Update tests when changing API contracts
- Keep mocks synchronized with actual implementations
- Review coverage reports regularly
- Add tests for new features before implementation

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)
