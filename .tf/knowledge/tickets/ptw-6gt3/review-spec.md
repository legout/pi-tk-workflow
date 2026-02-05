# Review (Spec Audit): ptw-6gt3

## Overall Assessment
The implementation updates the SKILL.md documentation with the new backlog.md format including Components and Links columns. However, the `backlog_ls_new.py` display code was not updated to show the new columns when rendering a single topic's backlog.

## Critical (must fix)
No critical issues found.

## Major (should fix)
- `tf_cli/backlog_ls_new.py:77-82` - The single-topic display output does not include Components and Links columns in the table header or data rows. The current output shows only `| ID | Title | Est. Hours |` but should show `| ID | Title | Est. Hours | Depends On | Components | Links |` to match the SKILL.md template and provide complete information when viewing a backlog.

## Minor (nice to fix)
- `tf_cli/backlog_ls_new.py` - When displaying a single topic's backlog, the Depends On column values are parsed but not displayed (rows contain this data at index 3, but only indices 0, 1, 2 are used). The new Components and Links columns would be at indices 4+ if present.

## Warnings (follow-up ticket)
- Existing backlog.md files (e.g., `.tf/knowledge/topics/seed-backlog-deps-and-tags/backlog.md`, `.tf/knowledge/topics/seed-add-versioning/backlog.md`) use the old format without Components/Links columns. These will need to be regenerated or migrated to use the new format when those topics are processed again.

## Suggestions (follow-up ticket)
- Consider adding a `--format` or `--columns` option to `backlog-ls` to control which columns are displayed
- Consider a migration command to update existing backlog.md files to the new format

## Positive Notes
- The SKILL.md template was correctly updated with Components and Links columns (lines 472-480)
- The column ordering (ID | Title | Est. Hours | Depends On | Components | Links) is logical and keeps related metadata together
- Using `-` as placeholder for empty values maintains consistency with existing conventions
- The parse_backlog() function correctly handles variable column counts, so it will parse both old and new format files without errors

## Summary Statistics
- Critical: 0
- Major: 1
- Minor: 1
- Warnings: 1
- Suggestions: 2

## Spec Coverage
- Spec/plan sources consulted:
  - Ticket ptw-6gt3 (acceptance criteria and constraints)
  - skills/tf-planning/SKILL.md (Backlog Generation procedure, step 10)
  - prompts/tf-backlog.md (execution instructions)
  - tf_cli/backlog_ls_new.py (display implementation)
- Missing specs: none
