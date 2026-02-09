# Review: pt-igly

## Critical (must fix)
- `tf_cli/workflow_status.py:14` - Frontmatter regex is duplicated from `ticket_loader.py`. If `ticket_loader.FRONTMATTER_PATTERN` changes, this will silently break. Should import from ticket_loader or use a shared constant.

## Major (should fix)
- `tf_cli/workflow_status.py:26` - Field name `recent_closed` is misleading. It counts ALL closed tickets, not just recent ones. Rename to `total_closed`.
- `tf_cli/workflow_status.py:44-71` - `_parse_frontmatter_status()` reimplements parsing logic that exists in `ticket_loader.py`. The ticket_loader has more robust parsing with YAML fallback.
- `tf_cli/workflow_status.py` - No unit tests for this new module. All other CLI modules have corresponding `test_*.py` files.

## Minor (nice to fix)
- `tf_cli/workflow_status.py:60-86` - The 2KB file read limit is efficient but doesn't validate frontmatter length. Consider logging a warning when frontmatter appears incomplete.
- `tf_cli/workflow_status.py:79` - The "in_progress" status check won't match any tickets. Actual ticket statuses are "open" and "closed" only.
- `tf_cli/workflow_status.py:62-63` - The deps parsing logic only handles single-line YAML lists. Multi-line YAML list syntax would fail.
- `tf_cli/workflow_status.py:178` - Implementation.md claims 152 lines but actual file is 178 lines. Keep documentation accurate.

## Warnings (follow-up ticket)
- `tf_cli/workflow_status.py` - Module is standalone but not integrated into the main CLI (`cli.py`). Consider adding as `tf status` command.
- `tf_cli/workflow_status.py:111` - Tickets directory is hardcoded as `.tickets/`. Should be configurable via settings.json.
- `tf_cli/workflow_status.py:98` - `get_knowledge_entries()` counts directories, not actual knowledge documents.

## Suggestions (follow-up ticket)
- `tf_cli/workflow_status.py` - Add `--json` flag for machine-readable output.
- `tf_cli/workflow_status.py` - Add filtering options like `--status open` or `--component cli`.
- `tf_cli/workflow_status.py` - Consider caching computed stats to a file for faster repeated queries.
- `tf_cli/workflow_status.py` - Consider refactoring to use the existing `TicketLoader` class.

## Summary Statistics
- Critical: 1
- Major: 3
- Minor: 4
- Warnings: 3
- Suggestions: 4
