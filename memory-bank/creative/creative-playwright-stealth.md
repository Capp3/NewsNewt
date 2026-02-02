# Creative Phase: Playwright Stealth Implementation

## 1️⃣ PROBLEM DEFINITION

### Current Issue

The current Playwright Stealth implementation has two main problems:

1. **Timing Issue**: Stealth is applied AFTER page navigation, which is too late according to best practices
2. **Architecture Issue**: Uses fragile approach by modifying internal Crawlee attributes (`_request_handler`)

### Requirements

- Apply stealth BEFORE navigation (as recommended by ZenRows blog)
- Work with Crawlee's architecture, not against it
- Maintain backward compatibility
- Preserve existing configuration options

## 2️⃣ OPTIONS ANALYSIS

### Option A: Apply Stealth in Request Handler (Before Navigation Hook)

**Approach**: Use Crawlee's hooks or intercept navigation

**Pros**:

- Works within Crawlee's architecture
- Can apply stealth before navigation
- Clean integration

**Cons**:

- Need to find proper hook point
- May require understanding Crawlee internals

**Feasibility**: Medium - Need to investigate Crawlee hooks

### Option B: Apply Stealth in Browser Context Creation

**Approach**: Apply stealth when browser context is created, before any pages

**Pros**:

- Applies stealth early
- Works with BrowserPool architecture
- Clean separation of concerns

**Cons**:

- May need to apply per-page (not per-context)
- Need to verify if stealth persists across pages

**Feasibility**: Medium - Need to test stealth persistence

### Option C: Use Crawlee's Browser Plugin Hooks

**Approach**: Extend PlaywrightBrowserPlugin to apply stealth on page creation

**Pros**:

- Most aligned with Crawlee architecture
- Applies stealth at the right time
- Reusable pattern

**Cons**:

- Requires creating custom plugin
- More complex implementation

**Feasibility**: High - Aligns with Crawlee patterns

### Option D: Apply Stealth in Request Handler (Current Approach Improved)

**Approach**: Apply stealth at the start of request handler, before any operations

**Pros**:

- Simple change
- Minimal code modification
- Works with current structure

**Cons**:

- Navigation may have already happened
- May still be too late

**Feasibility**: Low - Doesn't solve timing issue

## 3️⃣ DECISION

**Selected Option**: **Option E - Apply Stealth at Request Handler Start (Improved)**

### Rationale

After investigation, Crawlee handles navigation internally before calling the request handler. However:

1. Applying stealth at the very start of the request handler is the earliest practical point
2. Stealth can still help with detection during page interaction
3. Simpler implementation that works with Crawlee's architecture
4. Can be improved later if Crawlee exposes better hooks

### Alternative Consideration

If Crawlee's BrowserPool/Plugin system exposes page creation hooks, we can migrate to Option C later. For now, Option E provides immediate improvement over the current fragile approach.

### Implementation Strategy

Move stealth application to the very beginning of the request handler, before any page operations. This ensures stealth is applied as early as possible within Crawlee's architecture.

## 4️⃣ IMPLEMENTATION GUIDELINES

### Step 1: Update Request Handler

- Move stealth application to the very start of `request_handler`
- Apply `stealth_async(context.page)` immediately after getting the page
- Pass `enable_stealth` config to request handler factory
- Apply stealth before any page operations (including `wait_for_load_state`)

### Step 2: Update Handler Factory

- Modify `create_request_handler()` to accept `enable_stealth` parameter
- Pass config value from `create_crawler()`

### Step 3: Remove Old Implementation

- Remove the `_request_handler` modification code (lines 216-242)
- Remove conditional stealth application after crawler creation
- Clean up unused code paths

### Step 4: Testing

- Test with `ENABLE_STEALTH=true`
- Test with `ENABLE_STEALTH=false`
- Verify stealth is applied as early as possible
- Test CAPTCHA detection still works
- Verify no regressions in existing functionality

## 5️⃣ TECHNICAL DETAILS

### Request Handler Structure

```python
def create_request_handler(
    app: FastAPI,
    enable_stealth: bool = True,
) -> Callable[[PlaywrightCrawlingContext], Awaitable[None]]:
    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        request_id = context.request.user_data.get("request_id")
        if not request_id:
            logger.error("⚠️  Missing request_id in user_data")
            return

        page = context.page

        # Apply stealth IMMEDIATELY at the start (as early as possible)
        if enable_stealth:
            try:
                from playwright_stealth import stealth_async
                await stealth_async(page)
                logger.debug(f"[{request_id}] Stealth mode applied")
            except ImportError:
                logger.warning("⚠️  playwright-stealth not available")

        # Continue with existing handler logic...
        start_time = time.time()
        url = context.request.url
        # ... rest of handler
```

### Integration Point

- Update `create_request_handler()` signature to accept `enable_stealth`
- Pass `config["enable_stealth"]` from `create_crawler()`
- Remove stealth application code after crawler creation

### Configuration Flow

1. `Config.enable_stealth` → `get_crawler_settings()`
2. `get_crawler_settings()` → `create_crawler()`
3. `create_crawler()` → `create_request_handler(enable_stealth=config["enable_stealth"])`
4. Handler applies stealth at the very start, before any operations

## 6️⃣ FUTURE IMPROVEMENTS

### Potential Enhancement: Browser Context Hooks

If Crawlee's API evolves to expose browser context or page creation hooks, we can migrate to applying stealth even earlier (before navigation). This would be the ideal solution but requires Crawlee API support.

### Monitoring

- Monitor Crawlee releases for new hook points
- Consider contributing to Crawlee if hooks are needed
- Document current limitations in code comments
