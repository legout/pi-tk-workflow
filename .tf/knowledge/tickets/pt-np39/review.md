# Review: pt-np39

## Critical (must fix)

- `tf_cli/new_cli.py:9-22` - Imports 13 `_new` modules (`agentsmd_new`, `backlog_ls_new`, `doctor_new`, `init_new`, `login_new`, `next_new`, `priority_reclassify_new`, `ralph_new`, `setup_new`, `sync_new`, `tags_suggest_new`, `track_new`, `update_new`) that no longer exist. This completely breaks the `tf new <command>` backward-compatibility namespace.

- `tf_cli/new_cli.py:85-115` - All dispatch calls reference `_new` modules (e.g., `agentsmd_new.main(rest)`). Must use renamed modules.

- `tf_cli/setup.py:71` - Imports and calls `login_new.main([])` which no longer exists. Causes ImportError when running `tf setup` and selecting "Configure API keys".

- `tests/test_priority_reclassify.py:8` - Imports `priority_reclassify_new` which no longer exists. Must be `from tf_cli import priority_reclassify as pr`.

- `tests/test_priority_reclassify.py:24-117` - All `@patch` decorators reference `tf_cli.priority_reclassify_new` in patch paths. Must be updated to `tf_cli.priority_reclassify`.

- `tests/test_doctor_version.py:17` - Imports from `doctor_new` which no longer exists. Must use `doctor` module.

- `tests/test_doctor_version_integration.py:1` - Imports from `doctor_new` which no longer exists. Must use `doctor` module.

- `tests/test_json_capture.py:12` - Imports from `ralph_new` which no longer exists. Must use `ralph` module.

## Major (should fix)

- Implementation verification was incomplete. The "72 passed" tests excluded broken test files (`test_priority_reclassify.py`, `test_doctor_version.py`, `test_doctor_version_integration.py`, `test_json_capture.py`).

## Minor (nice to fix)

- `tf_cli/component_classifier.py:29` - Docstring references `tf_cli.tags_suggest_new`. Should be `tf_cli.tags_suggest`.

## Warnings (follow-up ticket)

- Consider deprecating the `tf new` namespace entirely in a follow-up ticket since stable CLI commands are now primary.

## Suggestions (follow-up ticket)

- Add CI check or pre-commit hook to prevent `*_new.py` references in imports or patch decorators.

## Summary Statistics
- Critical: 8
- Major: 1
- Minor: 1
- Warnings: 1
- Suggestions: 1
