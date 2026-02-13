# Fixes: pt-6zp2

## Summary
Fixed test integration issues identified during second-opinion review: corrected escalation test simulation (off-by-one attempt numbers), integrated escalation tests with `sync.resolve_meta_model` for end-to-end coverage, and added explicit backward-compatibility test for `agents.fixer="general"` with missing `metaModels.fixer`.

## Fixes by Severity

### Critical (must fix)
- No critical issues within ticket scope.

### Major (should fix)
- **tests/test_sync.py:218-271** – Revised `test_escalation_overrides_fixer_model` and `test_escalation_fallback_to_base_when_no_override` to:
  - Use explicit `next_attempt_number=2` instead of starting attempt 2 before calling `resolve_escalation`, eliminating off-by-one error.
  - Derive base model via `sync.resolve_meta_model` from a full config, ensuring the tests cover the actual resolution pipeline.
- **tests/test_sync.py:157** – Added `test_fixer_uses_general_when_meta_model_missing` to directly test the exact backward-compat configuration (`agents.fixer="general"`, `metaModels.fixer` missing).

### Minor (nice to fix)
- No minor issues addressed in this fix step.

### Warnings (follow-up)
- Pre-existing worker escalation bug (`tf/retry_state.py:247`) is not fixed here; will be tracked in a separate follow-up ticket.

## Summary Statistics
- **Critical**: 0
- **Major**: 2 (both fixed)
- **Minor**: 0
- **Warnings**: 0
- **Suggestions**: 0

## Verification
- All 26 tests in `tests/test_sync.py` pass, including the 7 in `TestFixerMetaModelSelection`.
- The revised tests now correctly verify the escalation curve boundary and the full integration chain.
- No regressions introduced.
