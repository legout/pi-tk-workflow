# Review (Second Opinion): pt-igly

## Overall Assessment
The workflow status utility is a clean, well-structured implementation using only stdlib. It successfully provides a quick overview of IRF workflow state. However, there are naming inconsistencies and code duplication issues that should be addressed.

## Critical (must fix)
No issues found.

## Major (should fix)
- `tf_cli/workflow_status.py:26` - Field name `recent_closed` is misleading. It counts ALL closed tickets (138 in the project), not just recent ones. Either rename to `total_closed` or implement actual recency filtering (e.g., closed in last 30 days).

- `tf_cli/workflow_status.py:15` - Code duplication: `FRONTMATTER_PATTERN` is duplicated from `ticket_loader.py` (line 25). This creates maintenance burden if the pattern needs updating. Consider importing from ticket_loader or creating a shared constants module.

- `tf_cli/workflow_status.py:44-71` - `_parse_frontmatter_status()` reimplements parsing logic that exists in `ticket_loader.py` (lines 170-227). The ticket_loader has more robust parsing with YAML fallback. This implementation may fail on edge cases that the main loader handles.

## Minor (nice to fix)
- `tf_cli/workflow_status.py:178` - Implementation.md claims 152 lines but actual file is 178 lines. Keep documentation accurate.

- `tf_cli/workflow_status.py:79` - The "in_progress" status check won't match any tickets. Actual ticket statuses in the project are "open" and "closed" only (verified via grep). The counter will always be 0, which could confuse users.

- `tf_cli/workflow_status.py:62-63` - The deps parsing logic only handles single-line YAML lists. Multi-line YAML list syntax (common in tickets with many deps) would fail to parse correctly.

## Warnings (follow-up ticket)
- `tf_cli/workflow_status.py:98` - The `get_knowledge_entries()` function counts directories, not actual knowledge documents. A directory with no content would still be counted as an entry. Consider counting actual `.md` files within each subdirectory.

## Suggestions (follow-up ticket)
- `tf_cli/workflow_status.py:120-145` - Consider refactoring to use the existing `TicketLoader` class from `ticket_loader.py`. This would eliminate the parsing duplication and ensure consistent behavior. TicketLoader already provides `count_by_status` property.

- `tf_cli/workflow_status.py:1` - Consider adding CLI argument support (e.g., `--json` for machine-readable output, `--watch` for continuous monitoring) in a future enhancement.

## Positive Notes
- Clean separation of concerns with `WorkflowStats`, `WorkflowStatus` dataclasses and `NamedTuple`
- Good use of type hints throughout
- Efficient 2KB read limit for frontmatter parsing (line 86)
- Proper error handling with logger warnings for unreadable tickets
- Auto-discovery of project root via `.tf` directory is user-friendly
- Script runs successfully and produces accurate counts for available data

## Summary Statistics
- Critical: 0
- Major: 3
- Minor: 3
- Warnings: 1
- Suggestions: 2
