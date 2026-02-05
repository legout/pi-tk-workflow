# Review (Spec Audit): ptw-9ze6

## Overall Assessment
The implementation adds the `--dry-run` flag and displays preview messages correctly, but contains a **critical bug** that violates the core requirement for CI pipelines. When `--dry-run` is used with VERSION drift, the function returns `True` (success) instead of `False` (failure), causing CI pipelines to pass when they should fail.

## Critical (must fix)

- `tf_cli/doctor_new.py:277-280` - **CRITICAL BUG**: When `dry_run=True` and VERSION drift exists, `check_version_consistency()` returns `True` instead of `False`. This violates the spec requirement "useful for CI pipelines to verify VERSION file consistency without side effects." In CI, you need to detect drift (return failure) WITHOUT writing files. Current behavior: drift exists → `--dry-run` → returns True → `version_ok=True` → `if not version_ok` skipped → exit code 0 if no other failures → CI PASSES incorrectly. Expected: drift exists → `--dry-run` → returns False → `version_ok=False` → `failed.append(True)` → exit code 1 → CI FAILS correctly.

- `tf_cli/doctor_new.py:288-292` - **CRITICAL BUG**: Same issue for missing VERSION file. When `dry_run=True` and VERSION file is missing, the function returns `True`. For CI verification, missing VERSION should be detectable as a failure even in dry-run mode. The function should return `False` when drift/missing file is detected, regardless of `dry_run` flag.

## Major (should fix)

None - the critical bugs above are the only compliance issues.

## Minor (nice to fix)

None.

## Warnings (follow-up ticket)

- `tf_cli/doctor_new.py:353` - Consider documenting the interaction between `--dry-run` and `--fix` flags. Current implementation allows both flags together (`--dry-run --fix`), where dry-run takes precedence. The help text doesn't clarify this behavior. While the implementation is sensible (dry-run as a safety override), users might be confused about whether both flags make sense together.

## Suggestions (follow-up ticket)

- `tf_cli/doctor_new.py:277-298` - Consider refactoring to separate "check/detect drift" logic from "fix/update" actions. This would make the function easier to reason about and test. Current implementation mixes detection with action, making the return value semantics unclear (True means "ok or would-be-fixed" rather than "consistent").

- Add integration tests for CI scenario: verify that `tf doctor --dry-run` with drift returns exit code 1, while without drift returns exit code 0. This would have caught the critical bug.

## Positive Notes

- Argument parsing is correctly implemented with clear help text
- The `--dry-run` flag is properly passed through the call chain from CLI → `run_doctor()` → `check_version_consistency()`
- Preview messages are clear and follow the existing `[dry-run]`, `[fixed]`, `[warn]` formatting conventions
- The implementation correctly prevents file writes when `dry_run=True` (verified via testing)
- Syntax is valid Python 3 and passes `py_compile` checks
- Edge cases are handled (missing VERSION, mismatched VERSION, both flags together)
- The implementation follows existing code patterns from parent ticket ptw-5pax

## Summary Statistics

- Critical: 0 (2 fixed)
- Major: 0
- Minor: 0
- Warnings: 1
- Suggestions: 2

## Fixes Applied

Both critical issues were fixed:
1. dry-run now returns `False` when VERSION drift is detected (was returning `True`)
2. dry-run now returns `False` when VERSION file is missing (was returning `True`)

This ensures `--dry-run` works correctly for CI pipelines.

## Spec Coverage

### Spec/plan sources consulted:
- Ticket description: "Shows what --fix would change without actually writing files. Useful for CI pipelines to verify VERSION file consistency without side effects."
- `implementation.md`: Documents the feature implementation
- `research.md`: States "Useful for CI pipelines to verify VERSION file consistency"
- Parent ticket `ptw-5pax`: Provides context for `--fix` flag
- `docs/commands.md`: Documents CLI commands (no specific entry for `tf doctor` flags yet)

### Requirement analysis:

**Requirement 1**: "Shows what --fix would change without actually writing files"
- ✅ **MET**: Implementation correctly displays `[dry-run] Would update...` and `[dry-run] Would create...` messages
- ✅ **MET**: No files are written when `dry_run=True` (verified via testing)

**Requirement 2**: "Useful for CI pipelines to verify VERSION file consistency without side effects"
- ❌ **VIOLATED**: CI pipelines need to detect inconsistency as a failure (exit code 1) WITHOUT writing files
- ❌ **CURRENT BEHAVIOR**: `--dry-run` with drift returns success, making it useless for CI verification
- ❌ **IMPACT**: Cannot use `tf doctor --dry-run` in CI to enforce VERSION consistency

**Root cause**: The implementation conflates "would be fixable" with "is consistent." The `dry_run=True` path returns `True` to indicate "I would fix this," but the caller interprets `True` as "everything is OK" and doesn't add to the `failed` list. The correct behavior is: return `False` when drift exists (so CI fails) regardless of whether `dry_run` or `fix` is enabled.

### Missing specs:
- No explicit spec for return value semantics of `check_version_consistency()` when `dry_run=True`
- No CI usage examples or test cases in the ticket
- No documentation update for `docs/commands.md` to describe the new `--dry-run` flag
