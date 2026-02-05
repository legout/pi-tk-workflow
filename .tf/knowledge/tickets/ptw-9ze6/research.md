# Research: ptw-9ze6

## Status
Research skipped - straightforward feature implementation based on existing code patterns.

## Context
- Parent ticket ptw-5pax implemented `tf doctor --fix` to auto-sync VERSION file
- This ticket adds `--dry-run` flag to preview changes without writing files
- Useful for CI pipelines to verify VERSION file consistency

## Implementation Plan
1. Add `--dry-run` argument to argument parser in `doctor_new.py`
2. Modify `check_version_consistency()` to accept `dry_run` parameter
3. When `dry_run=True`, print `[dry-run]` messages showing what would change
4. Ensure `--dry-run` and `--fix` can work together (dry-run takes precedence or they conflict)
5. Update `run_doctor()` to pass the dry_run flag

## Files to Modify
- `tf_cli/doctor_new.py` - Add --dry-run flag and logic

## Sources
- `tf_cli/doctor_new.py` - existing doctor implementation
- `.tickets/ptw-5pax.md` - parent ticket context
