# Implementation: pt-xwjw

## Summary
Defined timeout backoff semantics and configuration keys for Ralph's per-iteration timeout increase feature. This is a specification ticket that documents the complete semantics for the implementation ticket pt-bcu8.

## Retry Context
- Attempt: 1
- Escalated Models: fixer=base, reviewer-second=base, worker=base

## Files Changed
- `.tf/knowledge/tickets/pt-xwjw/timeout-backoff-spec.md` - Complete specification document (already existed, verified accurate)
- `.tf/knowledge/tickets/pt-xwjw/research.md` - Research findings (already existed)

## Work Completed

### 1. Verified Spec Alignment with Codebase
Examined `tf/ralph.py` and `tf/retry_state.py` to confirm the specification aligns with existing implementation:

- **Timeout default**: `DEFAULTS["attemptTimeoutMs"] = 600000` (10 minutes) - matches spec baseTimeoutMs default
- **RetryState API**: `get_attempt_number()` returns 1-indexed values - spec correctly defines `iteration_index = attempt_number - 1`
- **Config location**: `.tf/ralph/config.json` is the appropriate location for timeoutBackoff settings

### 2. Acceptance Criteria Verification

| Criteria | Status | Spec Section |
|----------|--------|--------------|
| Iteration index semantics explicit (starts at 0 vs 1) | ✓ PASS | Section 1 - Defines 0-indexed iteration index |
| Effective timeout formula documented (with max cap) | ✓ PASS | Section 2 - `effective = base + (i * increment)` with `min(effective, max)` |
| Config keys and defaults defined | ✓ PASS | Section 3 - `timeoutBackoff.enabled`, `baseTimeoutMs`, `incrementMs=150000`, `maxTimeoutMs` |

### 3. Key Definitions Finalized

**Iteration Index Semantics**:
- Zero-based indexing (`i=0` for first attempt)
- Maps from 1-indexed `RetryState.get_attempt_number()` via: `iteration_index = attempt_number - 1`

**Effective Timeout Formula**:
```
effective_timeout_ms = base_timeout_ms + (iteration_index * increment_ms)
# With optional cap:
effective_timeout_ms = min(effective, max_timeout_ms)
```

**Configuration Keys**:
```json
{
  "timeoutBackoff": {
    "enabled": false,
    "baseTimeoutMs": 600000,
    "incrementMs": 150000,
    "maxTimeoutMs": null
  }
}
```

### 4. Validation Constraints Documented
- `baseTimeoutMs` ≥ 0
- `incrementMs` ≥ 0  
- `maxTimeoutMs` null or ≥ `baseTimeoutMs`
- All invalid values log error and fall back to defaults

### 5. Observability Requirements Documented
Log format specified:
```
[ralph] Timeout backoff: base={base}ms increment={inc}ms iteration={i} effective={eff}ms capped={true|false}
```

## Tests Run
- N/A (specification ticket - no code changes)

## Verification
- [x] Spec reviewed against actual codebase
- [x] All acceptance criteria met
- [x] Configuration defaults align with existing `attemptTimeoutMs` default
- [x] RetryState API semantics correctly documented
- [x] Blocking dependency pt-bcu8 has clear implementation guidance

## Review Fixes Applied

After code review, the specification was enhanced with:

### Critical Fixes
- **Integer overflow considerations** (Section 6.1.1): Documented safeguards and warning thresholds
- **Error logging requirements** (Section 3.6): Explicitly prohibited silent failures, mandated WARNING logs

### Major Fixes  
- **Validation constraints** (Section 3.3.1): Added comprehensive validation table for all config values
- **Environment variable validation** (Section 6.3.1): Specified validation rules and error logging
- **Function input validation** (Section 6.1): Added ValueError raises and docstring examples
- **Edge case tests** (Section 7.1.1): Added 8 additional test requirements

## Notes
- This ticket only defines semantics; implementation is in pt-bcu8
- The spec file `timeout-backoff-spec.md` serves as the reference for pt-bcu8
- All review feedback (2 Critical, 4 Major issues) has been addressed
