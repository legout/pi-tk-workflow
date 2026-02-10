# Review: pt-xwjw

## Overall Assessment
The timeout backoff specification is comprehensive and well-structured, with clear iteration semantics, formulas, and configuration schema. However, several edge cases around type coercion, config precedence, and integer boundary conditions warrant clarification before implementation in pt-bcu8. The spec correctly aligns with RetryState's 1-indexed attempt counting and preserves backward compatibility.

## Critical (must fix)
No issues found

## Major (should fix)
- `timeout-backoff-spec.md:204` - The `max_timeout_ms > 0` check treats both `null` and `0` identically as "no cap", but `0` should arguably be an error (timeout of 0ms is nonsensical) or explicitly documented as "no timeout" behavior. This ambiguity could lead to silent misconfiguration where a user sets `maxTimeoutMs: 0` expecting no timeout cap but the implementation might interpret it differently.
- `timeout-backoff-spec.md:135` - Environment variable validation specifies invalid values "log warning and use config/default" but doesn't specify whether malformed values in `RALPH_TIMEOUT_BACKOFF_MAX_MS` (e.g., "null" string vs empty/unset) follow the same path. This creates uncertainty around empty string handling.
- `timeout-backoff-spec.md:3` - Configuration location `.tf/ralph/config.json` is specified, but Ralph currently loads config from `.tf/config/settings.json` per `retry_state.py:462`. The spec should clarify which config file takes precedence or if both are valid locations, as this could cause confusion during implementation.

## Minor (nice to fix)
- `timeout-backoff-spec.md:101` - The validation constraint table shows `maxTimeoutMs` must be "null or ≥ baseTimeoutMs", but the error behavior says "treat as null (no cap)" which doesn't distinguish between "user explicitly set null" vs "validation failed". Consider logging differently for explicit null vs fallback null.
- `timeout-backoff-spec.md:141` - Example error log shows `[ralph] Invalid timeoutBackoff.maxTimeoutMs: 300000` but doesn't show the baseTimeoutMs value that caused the validation failure, making debugging harder.
- `timeout-backoff-spec.md:186` - The suggested function signature uses `int | None` syntax (Python 3.10+) but the codebase may need to support older Python versions. Should verify minimum Python version for Ralph.
- `timeout-backoff-spec.md:227` - Warning threshold of "1 hour" for large timeouts is arbitrary and not configurable. Consider documenting why 1 hour was chosen or making it configurable.

## Warnings (follow-up ticket)
- `timeout-backoff-spec.md:60` - The spec does not address interaction with the existing `attemptTimeoutMs` config key. If both are specified, which takes precedence? If `timeoutBackoff.enabled: false`, does `timeoutBackoff.baseTimeoutMs` override `attemptTimeoutMs` or are they completely separate?
- `timeout-backoff-spec.md:78` - No guidance on partial config overrides. If config has `timeoutBackoff.enabled: true` but missing `incrementMs`, does it use default or fail? The spec implies defaults are used but this should be explicit.
- `timeout-backoff-spec.md:156` - Structured logging fields use snake_case (`timeout_backoff_base_ms`) which differs from camelCase used elsewhere in Ralph config. This inconsistency may cause confusion for log parsers.

## Suggestions (follow-up ticket)
- `timeout-backoff-spec.md:41` - Consider adding a "dry-run" or "preview" mode where Ralph logs what timeouts would be calculated without actually running tickets, allowing users to verify their backoff configuration.
- `timeout-backoff-spec.md:201` - The formula `base + (i * increment)` uses simple linear growth. Consider documenting rationale for linear vs exponential backoff (the plan mentioned this was intentional, but the spec doesn't explain why).
- `timeout-backoff-spec.md:272` - Test case "max_timeout_ms == base_timeout_ms: Verify cap applied immediately from attempt 2" should clarify expected behavior: attempt 1 gets base, attempt 2+ get base (capped), or should attempt 2 calculation be checked before min()?

## Positive Notes
- The 0-indexed iteration semantics are clearly defined with explicit mapping from RetryState's 1-indexed attempt numbers, eliminating a common source of off-by-one errors
- Backward compatibility is thoroughly addressed with explicit "missing section = no error" behavior
- Validation constraints table provides clear rules with fallback behaviors for all invalid inputs
- The `incrementMs: 150000` default is documented with rationale (2.5 minutes per iteration from plan)
- Observability requirements include both human-readable logs and structured fields for machine parsing
- Edge case coverage in test requirements is comprehensive (negative values, zero values, large iterations, overflow)

## Summary Statistics
- Critical: 0
- Major: 3
- Minor: 4
- Warnings: 3
- Suggestions: 3
