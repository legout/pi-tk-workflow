I've completed the spec audit review for ticket `ptw-6gt3`. Here's a summary:

## Review Summary

**Overall**: The implementation correctly updates the SKILL.md documentation with the new backlog.md format, but the `backlog_ls_new.py` display code was not updated to show the new columns.

### Key Findings

| Severity | Issue |
|----------|-------|
| **Major** | `tf_cli/backlog_ls_new.py` doesn't display Components/Links columns when showing a single topic's backlog - only shows `| ID | Title | Est. Hours |` |
| **Minor** | The Depends On column values are parsed but not displayed in single-topic view |
| **Warning** | Existing backlog.md files use the old format and would need regeneration |

### What Was Done Correctly
- ✅ SKILL.md template updated with new columns (Components, Links)
- ✅ Column ordering is logical: ID | Title | Est. Hours | Depends On | Components | Links
- ✅ Using `-` placeholder maintains consistency
- ✅ Backward compatible: `parse_backlog()` handles variable column counts

### Output Location
`.tf/knowledge/tickets/ptw-6gt3/review-spec.md`