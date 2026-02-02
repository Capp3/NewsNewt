# Implementation Plan: Playwright Stealth Update

## Plan Overview

**Task**: Update Playwright Stealth implementation to apply stealth at the start of request handler
**Complexity**: Level 2 (Simple Enhancement)
**Status**: Planning Complete
**Next Mode**: BUILD

## Requirements Analysis

### Current State

- Stealth is applied AFTER navigation (lines 216-242 in `crawler.py`)
- Uses fragile approach: modifies internal `_request_handler` attribute
- Stealth applied via wrapper function after crawler creation

### Target State

- Stealth applied at the very start of request handler
- No modification of internal Crawlee attributes
- Clean integration with Crawlee architecture
- Maintain backward compatibility with configuration

## Affected Components

### Primary File

- **`src/app/crawler.py`**
  - `create_request_handler()` function (lines 44-154)
  - `create_crawler()` function (lines 157-243)

### Configuration Files (Review Only)

- `src/app/config.py` - Already has `enable_stealth` config
- `compose.yml` - Already has `ENABLE_STEALTH` env var
- `pyproject.toml` - Already has `playwright-stealth>=1.0.6` dependency

## Detailed Implementation Steps

### Step 1: Update `create_request_handler()` Signature

**Location**: `src/app/crawler.py` line 44

**Change**:

```python
# BEFORE
def create_request_handler(
    app: FastAPI,
) -> Callable[[PlaywrightCrawlingContext], Awaitable[None]]:

# AFTER
def create_request_handler(
    app: FastAPI,
    enable_stealth: bool = True,
) -> Callable[[PlaywrightCrawlingContext], Awaitable[None]]:
```

**Rationale**: Add parameter to control stealth application per handler instance

### Step 2: Apply Stealth at Request Handler Start

**Location**: `src/app/crawler.py` line 57-68

**Change**: Insert stealth application immediately after getting the page, before any operations

**Code to Add** (after line 65, before line 68):

```python
        page = context.page
        url = context.request.url

        # Apply stealth IMMEDIATELY at the start (as early as possible)
        if enable_stealth:
            try:
                from playwright_stealth import stealth_async  # type: ignore[import-untyped]
                await stealth_async(page)
                logger.debug(f"[{request_id}] Stealth mode applied")
            except ImportError:
                logger.warning(
                    f"⚠️  [{request_id}] playwright-stealth not available - continuing without stealth"
                )

        try:
```

**Rationale**: Apply stealth as early as possible, before any page operations including `wait_for_load_state`

### Step 3: Update `create_crawler()` to Pass Config

**Location**: `src/app/crawler.py` line 172

**Change**:

```python
# BEFORE
    config = Config.get_crawler_settings()
    request_handler = create_request_handler(app)

# AFTER
    config = Config.get_crawler_settings()
    request_handler = create_request_handler(
        app,
        enable_stealth=config["enable_stealth"]
    )
```

**Rationale**: Pass stealth configuration from crawler settings to handler factory

### Step 4: Remove Old Stealth Implementation

**Location**: `src/app/crawler.py` lines 216-242

**Change**: Delete entire block that modifies `_request_handler`

**Code to Remove**:

```python
    # Apply stealth mode if enabled
    if config["enable_stealth"]:
        try:
            from playwright_stealth import stealth_async  # type: ignore[import-untyped]

            async def stealth_handler(context: PlaywrightCrawlingContext) -> None:
                await stealth_async(context.page)

            # Add pre-navigation hook for stealth
            original_handler = crawler._request_handler  # type: ignore[attr-defined]

            async def combined_handler(context: PlaywrightCrawlingContext) -> None:
                await stealth_async(context.page)
                await original_handler(context)

            crawler._request_handler = combined_handler  # type: ignore[attr-defined]
            logger.info("✓ Stealth mode enabled - Anti-detection measures active")
        except ImportError:
            logger.warning(
                "⚠️  playwright-stealth package not found - continuing without stealth mode"
            )
            logger.warning(
                "   To enable stealth mode, ensure playwright-stealth is installed"
            )
    else:
        logger.info("ℹ️  Stealth mode disabled - Browser automation may be detectable")
```

**Rationale**: Remove fragile approach that modifies internal attributes

### Step 5: Add Logging for Stealth Status

**Location**: `src/app/crawler.py` after crawler creation (around line 214)

**Change**: Add logging to indicate stealth configuration

**Code to Add**:

```python
    if config["enable_stealth"]:
        logger.info("✓ Stealth mode enabled - Anti-detection measures active")
    else:
        logger.info("ℹ️  Stealth mode disabled - Browser automation may be detectable")

    return crawler
```

**Rationale**: Maintain visibility into stealth configuration status

## Code Changes Summary

| File                 | Lines Changed | Type   | Description                       |
| -------------------- | ------------- | ------ | --------------------------------- |
| `src/app/crawler.py` | 44-46         | Modify | Add `enable_stealth` parameter    |
| `src/app/crawler.py` | 65-68         | Insert | Apply stealth at handler start    |
| `src/app/crawler.py` | 172-175       | Modify | Pass config to handler factory    |
| `src/app/crawler.py` | 216-242       | Delete | Remove old stealth implementation |
| `src/app/crawler.py` | ~214          | Insert | Add stealth status logging        |

## Testing Strategy

### Test Case 1: Stealth Enabled

**Setup**: `ENABLE_STEALTH=true` in environment
**Expected**:

- Stealth applied at handler start
- Log shows "Stealth mode enabled"
- No errors during execution

### Test Case 2: Stealth Disabled

**Setup**: `ENABLE_STEALTH=false` in environment
**Expected**:

- No stealth application
- Log shows "Stealth mode disabled"
- Normal execution continues

### Test Case 3: Missing Package

**Setup**: Temporarily remove `playwright-stealth` package
**Expected**:

- Warning logged about missing package
- Execution continues without stealth
- No crashes

### Test Case 4: Functional Verification

**Setup**: Normal scraping request
**Expected**:

- All existing functionality preserved
- CAPTCHA detection still works
- Data extraction unchanged
- No regressions

## Challenges & Mitigations

### Challenge 1: Timing - Navigation Already Happened

**Issue**: Crawlee navigates before calling request handler, so stealth may be applied after navigation

**Mitigation**:

- Apply stealth as early as possible in handler (before any page operations)
- Stealth still helps with detection during page interaction
- Document limitation in code comments

### Challenge 2: Backward Compatibility

**Issue**: Need to ensure existing configuration still works

**Mitigation**:

- Use same `ENABLE_STEALTH` configuration variable
- Maintain same default behavior (`true`)
- No changes to configuration files needed

### Challenge 3: Error Handling

**Issue**: Need graceful handling if `playwright-stealth` import fails

**Mitigation**:

- Wrap import in try/except
- Log warning but continue execution
- Match existing error handling pattern

## Technology Validation

### Dependencies

- ✅ `playwright-stealth>=1.0.6` already in `pyproject.toml`
- ✅ Package installed via `uv sync`
- ✅ No new dependencies required

### Configuration

- ✅ `ENABLE_STEALTH` env var already configured
- ✅ `Config.enable_stealth` already exists
- ✅ No configuration changes needed

### Build System

- ✅ Using `uv` for dependency management
- ✅ `pyproject.toml` already configured
- ✅ No build changes required

### Testing Environment

- ✅ FastAPI test server available
- ✅ Docker compose setup for integration testing
- ✅ Logging infrastructure in place

## Verification Checklist

- [ ] Code changes implemented
- [ ] Stealth applied at handler start
- [ ] Old implementation removed
- [ ] Configuration passed correctly
- [ ] Logging updated
- [ ] Test with `ENABLE_STEALTH=true`
- [ ] Test with `ENABLE_STEALTH=false`
- [ ] Test with missing package
- [ ] Verify no regressions
- [ ] Verify CAPTCHA detection still works
- [ ] Code review completed

## Success Criteria

✅ **Stealth applied as early as possible** - At the very start of request handler
✅ **No internal attribute modification** - Clean integration with Crawlee
✅ **Configuration preserved** - `ENABLE_STEALTH` still works
✅ **Backward compatible** - All existing functionality preserved
✅ **Code quality** - Cleaner, more maintainable implementation
✅ **Documentation** - Code comments explain approach and limitations

## Next Steps

1. ✅ Planning complete
2. ➡️ **BUILD Mode** - Implement changes
3. ➡️ **REFLECT Mode** - Review implementation
4. ➡️ **ARCHIVE Mode** - Document completion

## Notes

- This is a Level 2 enhancement - straightforward code refactoring
- No architectural changes required
- No creative phase needed (design decisions already made)
- Can proceed directly to BUILD mode after planning
