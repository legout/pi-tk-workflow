# Review: ptw-5pax

## Critical (must fix)
No issues found

## Major (should fix)
- `tf_cli/new_cli.py:25` - The help text for `tf new doctor` doesn't document the `--fix` flag. The usage string shows `tf new doctor [--project <path>]` but should show `tf new doctor [--project <path>] [--fix]` to match the actual functionality.

## Minor (nice to fix)
- `tf_cli/doctor_new.py:191-192` - `sync_version_file()` prints error message but returns False, causing the caller to treat it as a "check failed" rather than a "fix failed". Consider differentiating these cases in the UI message.
- `tf_cli/doctor_new.py:242-245` - When `package_version is None` (invalid/missing version field), the function returns `True` indicating success. While safe, it could be misleading.
- `tf_cli/doctor_new.py:337` - The `resolve_target_base` function returns a tuple with a hardcoded `False` middle value that is immediately discarded. Could be cleaned up to return a 2-tuple.
- `tf_cli/doctor_new.py:173` - The `sync_version_file` function could include the project root path in the error message for better debugging.

## Warnings (follow-up ticket)
- `tf_cli/doctor_new.py:183-187` - `get_version_file_version()` silently returns `None` on any exception. File permission errors or encoding issues would go unnoticed.
- `scripts/tf_legacy.sh:doctor()` - The legacy bash doctor implementation doesn't include version checking, creating a feature gap between `tf doctor` (legacy) and `tf new doctor` (Python).

## Suggestions (follow-up ticket)
- Add a `--dry-run` flag that shows what `--fix` would change without actually writing the file
- Consider adding version check against git tags as a third version source
- Extend version check to verify other sources (pyproject.toml, Cargo.toml) for multi-language projects
- Consider adding pre-commit hook integration for automatic VERSION syncing

## Summary Statistics
- Critical: 0
- Major: 1
- Minor: 4
- Warnings: 2
- Suggestions: 4
