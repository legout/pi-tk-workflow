# Review (Spec Audit): pt-np39

## Overall Assessment
The implementation partially satisfies the spec requirements. While the source modules were successfully renamed from `*_new.py` to stable names in `tf_cli/`, **critical test files and related imports remain unupdated**, causing import errors. The claim of "No remaining `_new` import references in codebase" is incorrect.

## Critical (must fix)
- `tests/test_priority_reclassify.py:1` - Still imports `priority_reclassify_new` which no longer exists after rename. This causes `ImportError` and test failures. Must update to `from tf_cli import priority_reclassify as pr` and all `@patch("tf_cli.priority_reclassify_new...")` references to use `priority_reclassify`.
- `tests/test_doctor_version.py:1` - Still imports from `tf_cli.doctor_new` which no longer exists. Must update to `tf_cli.doctor`.
- `tests/test_doctor_version_integration.py:1` - Still imports from `tf_cli.doctor_new` which no longer exists. Must update to `tf_cli.doctor`.
- `tests/test_json_capture.py:1` - Still imports from `tf_cli.ralph_new` which no longer exists. Must update to `tf_cli.ralph`.
- `tf_cli/new_cli.py` - This entire file still imports and dispatches to all `*_new` modules (`agentsmd_new`, `backlog_ls_new`, `doctor_new`, `init_new`, etc.). While it may be a backward-compatibility file, it is now broken since the modules no longer exist with those names. Either update to stable names or remove if no longer needed.
- `tf_cli/setup.py:71` - Still imports `login_new` module which no longer exists. Must update to `login`.

## Major (should fix)
- `tests/test_priority_reclassify.py` - File name suggests it's the test file for the priority_reclassify module, but there is no `test_priority_reclassify_new.py` that was claimed to be renamed. Either the test file was never named `test_priority_reclassify_new.py` (in which case the implementation.md is inaccurate) or the test file was missed during rename.

## Minor (nice to fix)
- `tf_cli/component_classifier.py:29` - Docstring references `tf_cli.tags_suggest_new` in backtick code format. Should update to `tf_cli.tags_suggest` for consistency.
- `tests/test_doctor_version.py:1` - Docstring comment references `tf_cli/doctor_new.py` in module path format. Should update to `tf_cli/doctor.py`.

## Warnings (follow-up ticket)
- `tf_cli/new_cli.py` - The existence of a separate `new_cli.py` that dispatches to `new` namespace commands creates maintenance overhead. Consider consolidating into main `cli.py` or formally deprecating the `tf new <command>` namespace once migration is complete.

## Suggestions (follow-up ticket)
- Add a CI check or pre-commit hook to prevent future `*_new.py` transitional naming patterns from persisting past their migration window.

## Positive Notes
- All 13 source modules in `tf_cli/` were correctly renamed to stable names (`agentsmd.py`, `backlog_ls.py`, `doctor.py`, `init.py`, `login.py`, `next.py`, `priority_reclassify.py`, `ralph.py`, `setup.py`, `sync.py`, `tags_suggest.py`, `track.py`, `update.py`).
- `tf_cli/cli.py` was correctly updated to import from stable module names (verified lines 337-405).
- 5 test files were correctly renamed from `test_*_new.py` to `test_*.py` (`test_init.py`, `test_next.py`, `test_sync.py`, `test_track.py`, `test_update.py`).
- The CLI `--version` command works correctly and reports `0.1.0`.

## Summary Statistics
- Critical: 6
- Major: 1
- Minor: 2
- Warnings: 1
- Suggestions: 1

## Spec Coverage
- Spec/plan sources consulted: `.tf/knowledge/topics/plan-critical-cleanup-simplification/plan.md`, `.tf/knowledge/topics/plan-critical-cleanup-simplification/backlog.md`
- Missing specs: none
