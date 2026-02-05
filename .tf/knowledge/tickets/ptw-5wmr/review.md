# Review: ptw-5wmr

## Critical (must fix)
No issues found.

## Major (should fix)
- `tf_cli/doctor_new.py:170-177` - Inconsistent JSON parsing pattern. The file already has a `read_json()` helper function that handles JSON file reading with proper error handling, but `get_package_version()` reimplements this logic. Should use the existing helper.
- `tf_cli/doctor_new.py:176` - No validation for falsy version values. If package.json has `"version": ""` or `"version": null`, the code prints `[ok] package.json version:` which is confusing.

## Minor (nice to fix)
- `tf_cli/doctor_new.py:174` - Info message "No package.json found" is misleading when file exists but has no version field. Consider distinguishing "file not found" from "version not found".
- `tf_cli/doctor_new.py:182` - VERSION file with empty/whitespace-only content passes `is not None` check but produces confusing output.
- `tf_cli/doctor_new.py:176` - `package_data.get("version")` could return non-string types causing confusing comparison behavior.

## Warnings (follow-up ticket)
- No automated tests exist for the doctor module.

## Suggestions (follow-up ticket)
- Consider validating version string is non-empty before returning
- Consider version normalization (stripping 'v' prefix) to avoid false mismatches
- Consider adding a `--version` CLI flag to expose version to users
- Consider extracting version parsing logic into a shared utility
- Consider adding a `--fix` flag to auto-sync VERSION file to package.json

## Summary Statistics
- Critical: 0
- Major: 2
- Minor: 3
- Warnings: 1
- Suggestions: 5
