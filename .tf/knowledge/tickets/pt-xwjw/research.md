# Research: pt-xwjw

## Status
Research completed. Existing codebase analyzed for timeout configuration patterns.

## Context Reviewed

### Current Timeout Configuration
From `tf/ralph.py`, the `DEFAULTS` dictionary contains:
- `attemptTimeoutMs`: 600000 (10 minutes default, 0 = no timeout)
- This is used for per-ticket attempt timeouts in serial mode

### Configuration Loading
- Config loaded from `.tf/ralph/config.json` via `load_config()`
- Environment variables take precedence for timeout settings
- `resolve_attempt_timeout_ms()` handles resolution from env var → config → default

### Retry State Management
- `tf/retry_state.py` manages attempt counters via `RetryState` class
- `get_attempt_number()` returns 1-indexed attempt count
- `get_retry_count()` returns number of BLOCKED attempts

### Related Tickets
- **pt-bcu8** [open]: Implement timeout backoff calculation helper (blocking dependency)
- This ticket (pt-xwjw) defines the semantics that pt-bcu8 will implement

## Key Findings

1. **Target Timeout**: The `attemptTimeoutMs` in Ralph's DEFAULTS is the primary timeout to enhance
2. **Iteration Counter**: `RetryState.get_attempt_number()` provides 1-indexed attempt numbers
3. **Config Surface**: `.tf/ralph/config.json` is the appropriate location for new timeout backoff settings

## Sources
- `tf/ralph.py` - DEFAULTS dict, timeout resolution functions
- `tf/retry_state.py` - Retry state management, attempt counting
- `.tf/knowledge/topics/plan-increase-timeout-on-each-iteration-defau/plan.md` - Plan context
- `.tf/knowledge/topics/seed-increase-timeout-on-each-iteration-defau/seed.md` - Seed context
