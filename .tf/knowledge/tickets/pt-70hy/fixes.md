# Fixes: pt-70hy

## Issues Fixed

### Critical: Cache inconsistency when `tk` is not in PATH
- **File**: `tf_cli/ralph.py`
- **Issue**: When `shutil.which("tk")` returns `None`, the function returned early without caching the result, causing repeated checks.
- **Fix**: Added `_ticket_title_cache[ticket] = None` before returning when `tk` is not found.

### Major: Inefficient parsing logic
- **File**: `tf_cli/ralph.py`
- **Issue**: The function continued iterating through all lines even after finding the title and transitioning into frontmatter.
- **Fix**: Restructured the logic to return immediately when we find a title and then encounter the frontmatter delimiter (`---`). This avoids unnecessary iteration.

### Minor: Type annotation using `Dict` instead of `dict`
- **File**: `tf_cli/ralph.py`
- **Issue**: Used `Dict[str, Optional[str]]` from typing module instead of built-in `dict[str, Optional[str]]`.
- **Fix**: Changed to use built-in `dict` type for consistency with modern Python 3.9+ patterns.

## Unfixed Issues (Intentionally Deferred)

### Minor: Missing test coverage
- **Reason**: The cache functionality is straightforward and all 693 existing tests pass. Unit tests for caching would be nice but don't block the ticket.
- **Follow-up**: Could be added as a follow-up ticket if desired.

### Warning: `use_cache` parameter not used
- **Reason**: The parameter provides flexibility for future use and testing. It's intentionally designed as opt-out but currently no callers need to bypass the cache.
- **Follow-up**: Could expose via CLI/config if debugging scenarios arise.

### Suggestions
- Cache statistics for debugging - deferred as not essential
- `functools.lru_cache` - manual cache provides more control and explicit clearing
- Regex/YAML parser - current parsing is sufficient for the use case

## Verification
- All 693 existing tests pass
- Syntax check passes
- Cache behavior manually verified
