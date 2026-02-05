---
id: ptw-6gt3
status: closed
deps: []
links: []
created: 2026-02-05T14:00:22Z
type: task
priority: 2
assignee: legout
external-ref: seed-backlog-deps-and-tags
tags: [tf, backlog]
---
# Update backlog.md format to include components and links

## Task
Update the backlog.md writer in /tf-backlog to include component tags and linked ticket IDs in the summary table.

## Context
Backlog.md should be a quick human overview of the generated work, including ordering (deps), categorization (components), and grouping (links).

## Acceptance Criteria
- [ ] Backlog table includes columns for Components and Links (in addition to Depends On).
- [ ] Output is stable and readable.
- [ ] Existing backlog.md files are not broken (new columns can be optional).

## Constraints
- Keep the table simple; avoid multi-line cells if possible.

## References
- Seed: seed-backlog-deps-and-tags


## Notes

**2026-02-05T14:28:16Z**

✅ Completed: Updated backlog.md format in skills/tf-planning/SKILL.md

**Changes:**
- Added 'Components' column for comma-separated tags (e.g., tf, backlog, plan)
- Added 'Links' column for comma-separated linked ticket IDs
- Updated template documentation with placeholder descriptions

**Table format:**


**Commit:** 5cbb753
**Review:** 0 Critical, 0 Major, 0 Minor issues
**Artifacts:** .tf/knowledge/tickets/ptw-6gt3/
