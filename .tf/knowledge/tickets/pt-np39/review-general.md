# Review: pt-np39

## Overall Assessment
The module renaming from `*_new.py` to stable names was mostly completed successfully for the main CLI modules and 5 test files. However, **critical issues remain** - the `new_cli.py` backward-compatibility module and `test_priority_reclassify.py` still reference the old `_new` module names, causing import errors. The implementation claim of "No remaining `_new` import references" is incorrect.

## Critical (must fix)

- `tf_cli/new_cli.py:6-20` - Imports `*_new` modules (`agentsmd_new`, `backlog_ls_new`, `doctor_new`, `init_new`, `login_new`, `next_new`, `priority_reclassify_new`, `ralph_new`, `setup_new`, `sync_new`, `tags_suggest_new`, `track_new`, `update_new`) that no longer exist. This breaks the `tf new <command>` backward-compatibility namespace completely. The imports must be updated to use the stable module names (e.g., `from . import init` instead of `from . import init_new`).

- `tests/test_priority_reclassify.py:8` - Imports `priority_reclassify_new` which no longer exists: `from tf_cli import priority_reclassify_new as pr`. This causes the entire test file to fail collection with `ImportError`. Must be changed to `from tf_cli import priority_reclassify as pr`.

- `tests/test_priority_reclassify.py` - Multiple `@patch` decorators reference `tf_cli.priority_reclassify_new` (lines with `@patch("tf_cli.priority_reclassify_new...`) which will fail when the module is fixed. All patch paths must be updated to `tf_cli.priority_reclassify`.

## Major (should fix)

- `implementation.md` claims "No remaining `_new` import references in codebase" but the grep results clearly show 20+ references. The verification step was incomplete - it should have run `grep -r "_new"` across the entire codebase, not just checked for file existence.

- `implementation.md` reports "72 passed" tests but only ran 5 test files. The `test_priority_reclassify.py` tests were not included in the test run, which would have immediately revealed the import error.

## Minor (nice to fix)

- `tf_cli/new_cli.py` - Consider deprecating this entire backward-compatibility module since the stable modules are now the default. The `cli.py` already dispatches directly to stable modules, making `new_cli.py` redundant.

## Warnings (follow-up ticket)

- None - all issues should be fixed in this ticket.

## Suggestions (follow-up ticket)

- Add a CI check or pre-commit hook to prevent `*_new.py` module naming patterns from being reintroduced.

- Consider removing `new_cli.py` entirely in a future cleanup ticket once users have migrated away from the `tf new` namespace.

## Positive Notes

- The main CLI (`cli.py`) correctly imports all modules using stable names - the primary code path works correctly.
- The 5 renamed test files (`test_init.py`, `test_next.py`, `test_sync.py`, `test_track.py`, `test_update.py`) pass all 72 tests and use correct imports.
- No `*_new.py` files remain in the repository (excluding Ralph worktrees).
- The `cli.py --version` command works correctly, confirming the primary import chain is functional.

## Summary Statistics
- Critical: 3
- Major: 2
- Minor: 1
- Warnings: 0
- Suggestions: 2
