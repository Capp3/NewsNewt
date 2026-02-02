# Refactoring & Testing Plan: NewsNewt

## Code Review Summary

### Strengths ✅
- Good separation of concerns across modules
- Comprehensive docstrings following Google style
- Structured error handling with proper status codes
- Excellent logging with request ID tracking
- Modern Python type hints (3.12+)
- Clean async/await patterns
- Well-organized Pydantic models

### Issues Identified 🔍

#### 1. **CRITICAL: Debug Logging in Production** (Priority: HIGH)
**Location**: `src/app/crawler.py` lines 18-47, 189-268
**Issue**: Hard-coded debug logging function with fixed file paths
**Impact**: Creates unnecessary files, performance overhead, security risk
**Solution**: Remove debug logging code completely

#### 2. **Testing Infrastructure Missing** (Priority: HIGH)
**Issue**: No tests directory, no test coverage
**Impact**: Cannot verify functionality, risky refactoring
**Solution**: Create comprehensive test suite

#### 3. **Configuration Improvements** (Priority: MEDIUM)
**Issue**: 
- Config uses class variables (not thread-safe for modifications)
- No validation on environment variables
- Magic numbers in code (timeouts, waits)
**Solution**: 
- Use dataclass or Pydantic settings
- Add validation
- Extract constants

#### 4. **Error Handling Improvements** (Priority: MEDIUM)
**Issue**:
- Some bare `Exception` catches could be more specific
- Error messages could be more actionable
**Solution**: Use specific exception types, improve messages

#### 5. **Code Quality Improvements** (Priority: LOW)
**Issue**:
- Some functions are long (extract_with_fallbacks: 154 lines)
- Fallback patterns hard-coded
- Some duplicate code in extraction logic
**Solution**: Extract functions, use configuration for patterns

---

## Refactoring Tasks

### Phase 1: Critical Fixes (Estimated: 1-2 hours)

#### Task 1.1: Remove Debug Logging Code ⚡
**Priority**: CRITICAL
**Files**: `src/app/crawler.py`
**Steps**:
1. Remove lines 18-47 (debug logging imports and function)
2. Remove debug log calls on lines 189-195, 202-209, 221-231, 235-239, 248-255, 258-267
3. Test that crawler still works
4. Commit changes

**Expected Outcome**: Clean production code without debug artifacts

#### Task 1.2: Set Up Testing Infrastructure ⚡
**Priority**: HIGH
**Steps**:
1. Create `tests/` directory structure
2. Add `conftest.py` with fixtures
3. Configure pytest in `pyproject.toml`
4. Add test dependencies
5. Create initial smoke tests

**Files to Create**:
```
tests/
├── __init__.py
├── conftest.py
├── test_health.py
├── test_config.py
└── test_models.py
```

---

### Phase 2: Configuration & Constants (Estimated: 1-2 hours)

#### Task 2.1: Improve Configuration Management
**Priority**: MEDIUM
**Files**: `src/app/config.py`
**Changes**:
1. Use Pydantic Settings for validation
2. Add environment variable validation
3. Add default value documentation
4. Make thread-safe

**Example**:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    log_level: str = "INFO"
    playwright_headless: bool = True
    enable_stealth: bool = True
    crawl_concurrency: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

#### Task 2.2: Extract Magic Numbers to Constants
**Priority**: LOW
**Files**: `src/app/routes.py`, `src/app/extraction.py`
**Changes**:
1. Create `src/app/constants.py`
2. Extract timeouts, delays, limits
3. Document why each constant exists

**Example**:
```python
# src/app/constants.py
DEFAULT_TIMEOUT_SECONDS = 30.0
CRAWLER_START_DELAY_MS = 100
POPUP_CLICK_TIMEOUT_MS = 1000
POPUP_WAIT_AFTER_CLICK_MS = 500
```

---

### Phase 3: Code Quality Improvements (Estimated: 2-3 hours)

#### Task 3.1: Refactor Large Functions
**Priority**: MEDIUM
**Files**: `src/app/extraction.py`
**Changes**:
1. Extract `extract_with_fallbacks()` into smaller functions:
   - `_try_selector()`: Try user-provided selector
   - `_try_fallbacks()`: Try fallback patterns
   - `_extract_meta_tag()`: Extract from meta tags
   - `_extract_text_content()`: Extract text content
2. Extract auto-extraction logic

#### Task 3.2: Extract Fallback Patterns
**Priority**: LOW
**Files**: `src/app/extraction.py`
**Changes**:
1. Move fallback patterns to configuration or constants
2. Make extensible (could load from JSON in future)

**Example**:
```python
# src/app/constants.py
FALLBACK_PATTERNS = {
    "title": ["h1", ".article-title", ...],
    "content": ["article", "main", ...],
    ...
}
```

#### Task 3.3: Improve Error Specificity
**Priority**: MEDIUM
**Files**: All modules
**Changes**:
1. Replace bare `Exception` with specific types
2. Create custom exceptions in `src/app/exceptions.py`
3. Improve error messages

**Example**:
```python
# src/app/exceptions.py
class CaptchaDetectedError(Exception):
    """Raised when a CAPTCHA is detected on the page."""
    pass

class ExtractionError(Exception):
    """Raised when data extraction fails."""
    pass
```

---

### Phase 4: Testing (Estimated: 4-6 hours)

#### Task 4.1: Unit Tests
**Priority**: HIGH
**Coverage Target**: 80%+
**Tests to Create**:
1. `test_config.py`: Configuration loading and validation
2. `test_models.py`: Pydantic model validation
3. `test_extraction.py`: Extraction utilities (mocked Page)
4. `test_crawler.py`: Crawler creation (mocked dependencies)

#### Task 4.2: Integration Tests
**Priority**: MEDIUM
**Tests to Create**:
1. `test_routes_integration.py`: Test API endpoints
   - Health check
   - Scrape endpoint with mocked crawler
   - Error scenarios
   - Timeout scenarios

#### Task 4.3: End-to-End Tests (Optional)
**Priority**: LOW
**Tests to Create**:
1. `test_e2e.py`: Full scraping flow with test HTML pages
   - Mock server with test HTML
   - Test complete scrape flow
   - Test popup dismissal
   - Test CAPTCHA detection

---

### Phase 5: Logging Improvements (Estimated: 1 hour)

#### Task 5.1: Standardize Logging
**Priority**: LOW
**Changes**:
1. Create logging utilities in `src/app/logging_utils.py`
2. Standardize emoji usage (optional feature, configurable)
3. Add structured logging option (JSON output)
4. Add request context to all logs

**Example**:
```python
# src/app/logging_utils.py
def log_request_start(request_id: str, url: str, **kwargs):
    """Log request start with consistent format."""
    logger.info(f"📥 [{request_id}] New request - URL: {url}", extra=kwargs)
```

---

## Build & Test Process

### Step 1: Local Development Setup
```bash
# Install dependencies
uv sync

# Install Playwright browsers
uv run playwright install chromium --with-deps

# Run application
uv run uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

### Step 2: Run Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/app --cov-report=html

# Run specific test file
uv run pytest tests/test_health.py -v
```

### Step 3: Code Quality Checks
```bash
# Linting
uv run ruff check src/ tests/

# Formatting check
uv run ruff format --check src/ tests/

# Type checking
uv run mypy src/
```

### Step 4: Build Docker Image
```bash
# Build image
docker build -t newsnewt:latest .

# Run container
docker compose up -d

# Check logs
docker compose logs -f newsnewt

# Test health endpoint
curl http://localhost:3000/health
```

### Step 5: Integration Testing
```bash
# Test scraping endpoint
curl -X POST http://localhost:3000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

---

## Success Criteria

### Code Quality
- ✅ No debug logging code in production
- ✅ All magic numbers extracted to constants
- ✅ Functions under 50 lines
- ✅ No bare Exception catches
- ✅ Type hints on all functions
- ✅ Comprehensive docstrings

### Testing
- ✅ Test coverage >80%
- ✅ All unit tests passing
- ✅ Integration tests for all endpoints
- ✅ CI pipeline runs successfully

### Functionality
- ✅ Health check works
- ✅ Scraping works with selectors
- ✅ Scraping works without selectors
- ✅ CAPTCHA detection works
- ✅ Popup dismissal works
- ✅ Error handling works
- ✅ Timeout handling works

### Documentation
- ✅ Code comments updated
- ✅ README accurate
- ✅ API docs accurate
- ✅ Developer guide exists

---

## Implementation Order

1. **Remove debug logging** (30 min) - CRITICAL
2. **Set up testing** (1 hour) - HIGH
3. **Add unit tests for models/config** (1 hour) - HIGH
4. **Improve configuration** (1 hour) - MEDIUM
5. **Extract constants** (30 min) - MEDIUM
6. **Add integration tests** (2 hours) - MEDIUM
7. **Refactor large functions** (2 hours) - MEDIUM
8. **Improve error handling** (1 hour) - MEDIUM
9. **Standardize logging** (1 hour) - LOW
10. **Add E2E tests** (2 hours) - OPTIONAL

**Total Estimated Time**: 10-12 hours for core work
**Total with Optional**: 12-14 hours

---

## Risk Mitigation

1. **Backup before refactoring**: Git commit before each phase
2. **Test after each change**: Run tests immediately
3. **Small commits**: Commit frequently with clear messages
4. **Review changes**: Check diffs before committing
5. **Keep running version**: Always have working state in git

---

## Next Steps

Start with Phase 1:
1. Remove debug logging code
2. Set up testing infrastructure
3. Add initial tests
4. Verify everything still works

This creates a solid foundation for further improvements.
