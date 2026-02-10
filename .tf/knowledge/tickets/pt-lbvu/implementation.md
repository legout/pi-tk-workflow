# Implementation: pt-lbvu

## Summary
Added `workflow.escalation` configuration to the repo settings schema with explicit defaults (enabled=false, maxRetries=3, models nullable) and documented how model overrides map to roles.

## Retry Context
- Attempt: 1
- Escalated Models: fixer=base, reviewer-second=base, worker=base

## Files Changed

### 1. config/settings.json
Added the `escalation` configuration block under `workflow`:

```json
"escalation": {
  "enabled": false,
  "maxRetries": 3,
  "models": {
    "fixer": null,
    "reviewerSecondOpinion": null,
    "worker": null
  }
}
```

This ensures the repo settings template includes the escalation config with:
- `enabled: false` - Escalation is disabled by default (backwards compatible)
- `maxRetries: 3` - Maximum 3 retry attempts before skipping
- `models.*: null` - All model overrides default to null (use base models)

### 2. tf/retry_state.py
Fixed a bug in `resolve_escalation()` method where calling the method after `start_attempt()` (while an attempt is in progress) would incorrectly calculate the attempt number and trigger escalation prematurely.

The fix checks if the last attempt has status "in_progress" and uses the current attempt number instead of incrementing:

```python
# Check if there's an in-progress attempt (called after start_attempt)
current_attempts = self._data["attempts"]
if current_attempts and current_attempts[-1].get("status") == "in_progress":
    # We're in the middle of an attempt - use current attempt number
    attempt = len(current_attempts)
else:
    # Starting a new attempt - use next attempt number
    attempt = len(current_attempts) + 1
```

## Key Decisions

1. **Backwards Compatibility**: The escalation config defaults to `enabled: false`, ensuring existing projects continue to work without changes. When disabled, the workflow uses base models for all attempts.

2. **Model Override Mapping**: The escalation config uses camelCase keys that map to workflow roles:
   - `fixer` → The fixer agent (runs after review to fix issues)
   - `reviewerSecondOpinion` → The reviewer-second-opinion agent (parallel reviewer)
   - `worker` → The main implementation worker (optional, for attempt 3+)

3. **Escalation Curve**: As documented in `docs/retries-and-escalation.md`:
   - Attempt 1: Base models for all roles
   - Attempt 2: Escalated fixer only
   - Attempt 3+: Escalated fixer + reviewer-second-opinion (+ worker if configured)

## Tests Run

All 60 tests in `tests/test_retry_state.py` pass:
- Retry state persistence (load/save)
- Retry counter behavior
- Blocked status detection
- Max retries skip logic
- Escalation model resolution
- Reset functionality
- Close summary detection
- Review detection
- Unified detection
- Schema validation
- Edge cases
- Integration tests

```bash
cd /home/volker/coding/pi-ticketflow && python -m pytest tests/test_retry_state.py -v
# 60 passed
```

## Verification

1. The escalation config is now present in `config/settings.json` with correct defaults
2. The `docs/configuration.md` already documents the escalation config and model mapping
3. The `docs/retries-and-escalation.md` has comprehensive documentation on retry behavior
4. All retry state tests pass, including the escalation resolution tests

## Documentation References

- `docs/configuration.md` - Workflow configuration including escalation settings
- `docs/retries-and-escalation.md` - Full retry and escalation behavior documentation
- `tf/retry_state.py` - Implementation of retry state management and escalation resolution
