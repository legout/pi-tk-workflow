# Review: pt-lbvu

## Overall Assessment
The escalation config implementation is solid with good defaults and backwards compatibility. However, there are several edge cases around model resolution, config merging, and type safety that could cause subtle failures in production retry scenarios. The documentation correctly describes the escalation curve but doesn't warn about the asymmetric worker escalation behavior.

## Critical (must fix)
- No issues found

## Major (should fix)
- `tf/retry_state.py:603-633` - `load_escalation_config()` silently swallows all `IOError` exceptions including permission errors, potentially masking configuration issues where the file exists but isn't readable (wrong permissions, locked file).

## Minor (nice to fix)
- `tf/retry_state.py:388-401` - `resolve_escalation()` accepts negative or zero `next_attempt_number` without validation, which could produce unexpected escalation behavior if called with erroneous parameters.
- `tf/retry_state.py:398-401` - The worker escalation logic is asymmetric: worker only escalates on attempt 3+ if explicitly configured (non-null), while fixer and reviewer fall back to base models. This subtle difference isn't highlighted in docs.
- `docs/configuration.md:254-270` - The escalation curve table shows "Escalation model (if configured)" for worker at attempt 3+, but this phrasing understates the behavioral difference - worker escalation is opt-in while others are fallback-based.
- `.tf/config/settings.json:126-134` - All escalation models are `null` by default, which is correct for backwards compatibility, but means escalation is effectively a no-op until explicitly configured - this could confuse users who enable `enabled: true` without setting models.

## Warnings (follow-up ticket)
- `tf/retry_state.py:25-34` - `DEFAULT_ESCALATION_CONFIG` uses `dict[str, Any]` typing which bypasses type checking. Consider using `TypedDict` for stricter validation, especially since nested `models` dict merging relies on structure.
- `tf/retry_state.py:234-247` - The schema validation in `_validate_schema()` only checks field existence, not types or values (e.g., `version` could be a string, `retryCount` could be negative).

## Suggestions (follow-up ticket)
- Add a config validation warning when `escalation.enabled: true` but all models are null - help users discover they need to configure models.
- Consider adding `attempt 4+` behavior documentation - current docs imply the curve plateaus at attempt 3 but don't explicitly state what happens beyond.
- Add test case for `next_attempt_number=0` in `resolve_escalation()` to document/verify expected behavior.

## Positive Notes
- The atomic save mechanism (`save()` using temp file + `os.replace()`) correctly prevents state corruption during crashes.
- The nested models dict merging in `load_escalation_config()` correctly preserves defaults for unspecified roles while allowing partial overrides.
- The `start_attempt()` resume logic (lines 268-277) elegantly handles process crashes without duplicate attempt entries.
- Documentation table clearly maps role names to their config keys and describes the escalation progression.

## Summary Statistics
- Critical: 0
- Major: 1
- Minor: 4
- Warnings: 2
- Suggestions: 3
