# Follow-ups: ptw-9ze6

## Status
Skipped - `/tf-followups` command not yet implemented (see ticket ptw-cbf8)

## Potential Follow-up Items (from review)

### Warnings
1. **Document --dry-run and --fix interaction**
   - Location: `tf_cli/doctor_new.py:353`
   - Description: Current implementation allows both flags together (`--dry-run --fix`), where dry-run takes precedence. Consider documenting this behavior in help text.

### Suggestions
1. **Refactor check/detect logic from fix/update actions**
   - Location: `tf_cli/doctor_new.py:277-298`
   - Description: Consider separating "check/detect drift" logic from "fix/update" actions to make the function easier to reason about and test.

2. **Add integration tests for CI scenario**
   - Verify that `tf doctor --dry-run` with drift returns exit code 1
   - Verify that `tf doctor --dry-run` without drift returns exit code 0
   - This would prevent regressions of the critical bug that was fixed

## Notes
These are low-priority suggestions for future improvement. The core functionality is working correctly.
