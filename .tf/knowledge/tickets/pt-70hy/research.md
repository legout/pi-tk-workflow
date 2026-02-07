# Research: pt-70hy

## Status
Research completed via local code analysis. No external research needed.

## Problem Statement
The `extract_ticket_title()` function in `tf_cli/ralph.py` is called multiple times for the same ticket during a Ralph run, causing repeated subprocess calls to `tk show`. This is inefficient.

## Current Implementation Analysis

### Function Location
- `tf_cli/ralph.py:460` - `extract_ticket_title(ticket: str)`
- `tf_cli/ralph.py:492` - `extract_ticket_titles(tickets: List[str])`

### Usage Points (Current)
1. `ralph_run()` line 821: `ticket_title = extract_ticket_title(ticket)`
2. `ralph_start()` serial mode line 976: `ticket_title = extract_ticket_title(ticket)`
3. `ralph_start()` parallel mode line 1077: `ticket_titles = extract_ticket_titles(selected)`
4. `update_state()` line 571: `fallback_summary = extract_ticket_title(ticket)` (called indirectly)

### Problem
- Each call spawns `subprocess.run(["tk", "show", ticket], ...)`
- In parallel mode, `extract_ticket_titles()` calls `extract_ticket_title()` for each ticket
- The same ticket may be processed multiple times in the same loop iteration (different contexts)

## Proposed Solution

### Approach: Module-level in-memory cache
```python
# Module-level cache: ticket_id -> title
_ticket_title_cache: Dict[str, Optional[str]] = {}

def extract_ticket_title(ticket: str, use_cache: bool = True) -> Optional[str]:
    if use_cache and ticket in _ticket_title_cache:
        return _ticket_title_cache[ticket]
    # ... existing logic ...
    _ticket_title_cache[ticket] = title
    return title
```

### Cache Clearing
- Cache should be cleared between Ralph runs to prevent stale data
- Can be done via a `clear_ticket_title_cache()` function or by exposing cache management

## Implementation Plan
1. Add `_ticket_title_cache: Dict[str, Optional[str]] = {}` at module level
2. Modify `extract_ticket_title()` to check and populate cache
3. Add `clear_ticket_title_cache()` for explicit cache reset
4. Call cache clear at start of `ralph_run()` and `ralph_start()`
5. Ensure tests still pass

## Files to Modify
- `tf_cli/ralph.py` - Add cache and modify functions

## References
- Seed: seed-add-ticket-title-in-the-logging-when-run
- Related: pt-ul76 (depends on this), pt-7i3q (tests)
