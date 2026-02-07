# Review (Second Opinion): pt-np39

## Overall Assessment
The module renaming from `*_new.py` to stable names was completed for the main source files, but several critical references were missed. The backward-compatibility `tf new` namespace is completely broken, the `tf setup` command will fail when configuring API keys, and multiple test files reference non-existent modules. The implementation verification was incomplete.

## Critical (must fix)

- `tf_cli/new_cli.py:9-22` - Imports 13 `_new` modules that no longer exist (`agentsmd_new`, `backlog_ls_new`, etc.). This completely breaks the `tf new <command>` backward-compatibility namespace. All imports must be updated to use stable names.

- `tf_cli/new_cli.py:85-115` - All dispatch calls reference `_new` modules (e.g., `agentsmd_new.main(rest)`). These must use the renamed modules.

- `tf_cli/setup.py:57-58` - Imports and calls `login_new.main([])` which no longer exists. This causes an ImportError when running `tf setup` and selecting "Configure API keys". Must use `login` module instead.

- `tests/test_priority_reclassify.py:9` - Imports `priority_reclassify_new` which no longer exists. The entire test file uses this module reference. Must be updated to `priority_reclassify`.

- `tests/test_doctor_version.py:17` - Imports from `doctor_new` which no longer exists. Must use `doctor` module.

- `tests/test_doctor_version_integration.py:1` - Imports from `doctor_new` which no longer exists. Must use `doctor` module.

- `tests/test_json_capture.py:12` - Imports from `ralph_new` which no longer exists. Must use `ralph` module.

## Major (should fix)

- `tests/test_priority_reclassify.py:24-117` - All `@patch` decorators reference `tf_cli.priority_reclassify_new` in their patch paths. These must be updated to `tf_cli.priority_reclassify` or the patches will fail to apply correctly.

- Implementation verification claim is inaccurate: "72 passed" tests were run but excluded the broken test files (`test_priority_reclassify.py`, `test_doctor_version.py`, `test_doctor_version_integration.py`, `test_json_capture.py`). A complete test run would have revealed these issues.

## Minor (nice to fix)

- `tf_cli/component_classifier.py:22` - Docstring references `tf_cli.tags_suggest_new` which is misleading. Should reference `tf_cli.tags_suggest`.

## Warnings (follow-up ticket)

- Consider deprecating the `tf new` namespace entirely in a follow-up ticket since the stable CLI commands are now the primary interface. The `new_cli.py` backward-compatibility layer adds maintenance overhead.

## Suggestions (follow-up ticket)

- Add a CI check or pre-commit hook that fails if any `*_new.py` references exist in imports or patch decorators to prevent this type of incomplete migration in the future.

## Positive Notes

- The main `tf_cli/cli.py` file correctly imports all stable module names and the primary CLI interface works.
- All 13 source modules were successfully renamed from `*_new.py` to stable names.
- The 5 test files mentioned in the implementation were correctly renamed.
- No `*_new.py` files exist in the main codebase (only in Ralph worktrees which are expected).

## Summary Statistics
- Critical: 7
- Major: 2
- Minor: 1
- Warnings: 1
- Suggestions: 1
