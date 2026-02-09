# Review: pt-igly

## Overall Assessment
A well-structured utility module with clean architecture using dataclasses and NamedTuples. Uses stdlib only as intended and handles errors gracefully. However, it duplicates existing frontmatter parsing logic and lacks unit tests, which goes against established project conventions.

## Critical (must fix)
- `tf_cli/workflow_status.py:14` - Frontmatter regex is duplicated from `ticket_loader.py` with comment "Use existing frontmatter pattern from ticket_loader" but it's actually redefined here. If `ticket_loader.FRONTMATTER_PATTERN` changes, this will silently break. Should import from ticket_loader or use a shared constant.

## Major (should fix)
- `tf_cli/workflow_status.py` - No unit tests for this new module. All other CLI modules have corresponding `test_*.py` files in the `tests/` directory. Should create `tests/test_workflow_status.py` with tests for `_parse_frontmatter_status`, `count_tickets_by_status`, `get_knowledge_entries`, `_resolve_project_root`, and `get_workflow_status`.
- `tf_cli/workflow_status.py:35-57` - `_parse_frontmatter_status` manually parses YAML frontmatter with string splitting. This duplicates logic in `ticket_loader.py` which already has robust frontmatter parsing. Should use `TicketLoader` class or extract shared parsing utility to avoid maintenance burden and potential parsing inconsistencies.

## Minor (nice to fix)
- `tf_cli/workflow_status.py:60-86` - The 2KB file read limit is efficient but `_parse_frontmatter_status` doesn't validate frontmatter length. If a ticket has frontmatter >2KB, the parsing will be truncated and fail silently. Consider logging a warning when frontmatter appears incomplete.
- `tf_cli/workflow_status.py:75` - Status mapping uses `"in_progress"` but ticket frontmatter may use kebab-case `"in-progress"` (common convention). Consider normalizing status values.
- `tf_cli/workflow_status.py:102` - Docstring references `TicketLoader._resolve_tickets_dir()` but no such method exists in `ticket_loader.py`. The pattern is similar to `next.find_project_root()` - update docstring to reference the correct function.
- `tf_cli/workflow_status.py:147-148` - The CLI output uses hardcoded emoji and separator width. Consider making these configurable or using a constants section for maintainability.

## Warnings (follow-up ticket)
- `tf_cli/workflow_status.py` - Module is standalone but not integrated into the main CLI (`cli.py`). Users must run `python tf_cli/workflow_status.py` directly. Consider adding as `tf status` command.
- `tf_cli/workflow_status.py:111` - Tickets directory is hardcoded as `.tickets/` at project root. This path should be configurable via settings.json to match other path configurations in the project.

## Suggestions (follow-up ticket)
- `tf_cli/workflow_status.py` - Add `--json` flag for machine-readable output to enable scripting and CI/CD integration.
- `tf_cli/workflow_status.py` - Add filtering options like `--status open` or `--component cli` to show subset of workflow state.
- `tf_cli/workflow_status.py` - Consider caching computed stats to a file for faster repeated queries on large ticket bases.

## Positive Notes
- Clean separation of concerns with `WorkflowStats` NamedTuple and `WorkflowStatus` dataclass
- Good use of type hints throughout the module (Python 3.9+ style with `|` union)
- Proper error handling with try/except for file I/O operations and appropriate logging
- Efficient memory usage with 2KB read limit for frontmatter-only parsing
- Self-documenting code with clear function names and docstrings
- Follows project naming conventions (snake_case, module structure)
- Successfully runs and produces accurate output as verified by test execution

## Summary Statistics
- Critical: 1
- Major: 2
- Minor: 4
- Warnings: 2
- Suggestions: 3
