# Implementation: pt-70hy

## Summary
Implemented ticket title caching in Ralph to avoid repeated `tk show` subprocess calls for the same ticket during a run.

## Files Changed
- `tf_cli/ralph.py` - Added module-level cache and cache management functions

## Key Changes

### 1. Added Module-Level Cache
```python
# Module-level cache for ticket titles to avoid repeated tk show calls
_ticket_title_cache: Dict[str, Optional[str]] = {}
```

### 2. Added Cache Management Function
```python
def clear_ticket_title_cache() -> None:
    """Clear the ticket title cache.

    Should be called at the start of each Ralph run to ensure fresh data.
    """
    _ticket_title_cache.clear()
```

### 3. Modified `extract_ticket_title()`
- Added `use_cache: bool = True` parameter
- Checks cache before making subprocess call
- Stores result in cache after lookup
- Returns cached value on cache hit (avoids `tk show` call)

### 4. Fixed Bug in `extract_ticket_titles()`
- Removed duplicate type annotation (`titles: Dict[str, str]`)
- Updated docstring to mention caching behavior

### 5. Cache Lifecycle Management
- `clear_ticket_title_cache()` is called at the start of:
  - `ralph_run()` - Single ticket run
  - `ralph_start()` - Loop mode (serial or parallel)
- This ensures fresh data between Ralph runs while caching within a run

## Key Decisions

1. **In-Memory Dict Cache**: Simplest approach, no external dependencies
2. **Module-Level Scope**: Cache persists for the duration of the Python process
3. **Opt-Out Parameter**: `use_cache=False` allows bypassing cache if needed
4. **Explicit Clearing**: Cache is cleared at entry points, not automatically on import

## Tests Run
- All 693 existing tests pass
- Manual cache behavior verification:
  - Cache clear works correctly
  - Cache hit returns cached value
  - Cache miss populates cache

## Verification
```bash
# Run tests
python -m pytest tests/ -v

# Verify cache functionality
python -c "from tf_cli.ralph import _ticket_title_cache, clear_ticket_title_cache; clear_ticket_title_cache()"
```

## Performance Impact
- Before: N `tk show` calls for N ticket title lookups (even for same ticket)
- After: 1 `tk show` call per unique ticket per Ralph run
- Benefit: Significant reduction in subprocess overhead when same ticket is referenced multiple times
