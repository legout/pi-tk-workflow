# Fixes: ptw-5pax

## Summary
Fixed 1 Major issue identified in code review.

## Issues Fixed

### Major
1. **tf_cli/new_cli.py:25** - Updated help text to document `--fix` flag
   - Changed: `tf new doctor [--project <path>]`
   - To: `tf new doctor [--project <path>] [--fix]`

### Minor (addressed)
2. **tf_cli/doctor_new.py:173** - Enhanced error message in `sync_version_file()`
   - Added full path to VERSION file in error message for better debugging
   - Changed: `Failed to write VERSION file: {exc}`
   - To: `Failed to write VERSION file at {version_file}: {exc}`

## Files Changed
- `tf_cli/new_cli.py` - Updated help text
- `tf_cli/doctor_new.py` - Enhanced error message

## Verification
- `ruff check` passes on both files
- `ruff format` applied to both files
