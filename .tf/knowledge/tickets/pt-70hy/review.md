# Review: pt-70hy

## Critical (must fix)
- `tf_cli/ralph.py:585-586` - Cache inconsistency: When `shutil.which("tk")` returns `None`, the function returns early without caching the `None` result. This means subsequent calls for the same ticket will repeat the `shutil.which` check instead of using a cached value. Fix: Add `_ticket_title_cache[ticket] = None` before returning.

## Major (should fix)
- `tf_cli/ralph.py:588-623` - Inefficient parsing logic: The `extract_ticket_title()` function continues iterating through all lines even after finding and caching the title. Consider adding early return after finding title and frontmatter transition.

## Minor (nice to fix)
- `tf_cli/ralph.py:369-370` - Same as Critical: Inconsistent cache behavior when `tk` is not in PATH.
- Missing test coverage: The new caching functionality (`use_cache` parameter, cache hit/miss paths, `clear_ticket_title_cache()`) has no tests.
- `tf_cli/ralph.py:17` - Cache type annotation uses `Dict` from typing module instead of built-in `dict` (inconsistent with modern Python 3.9+ patterns).

## Warnings (follow-up ticket)
- `tf_cli/ralph.py:577` - The `use_cache: bool = True` parameter is added but never used in the codebase (all calls use the default). Consider whether this flexibility is needed, or if it should be exposed via CLI/config for debugging scenarios.

## Suggestions (follow-up ticket)
- Consider adding cache statistics (hits/misses) for debugging/monitoring at DEBUG level.
- Consider using `@functools.lru_cache` instead of manual cache management for simpler code.
- Consider using regex or proper YAML frontmatter parser for more robust title extraction.

## Positive Notes
- Clean lifecycle management: Cache is cleared at the start of both `ralph_run()` and `ralph_start()`
- Good opt-out design: The `use_cache: bool = True` parameter provides flexibility
- Consistent error caching: Failed lookups are cached as `None` (except the tk path check)
- Simple implementation: Uses a plain dict - no external dependencies
- All 693 existing tests pass with no regressions
- Implementation follows constraints: no network calls, simple in-memory dict only

## Summary Statistics
- Critical: 1
- Major: 1
- Minor: 3
- Warnings: 1
- Suggestions: 3
