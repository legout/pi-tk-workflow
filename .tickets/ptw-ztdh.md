---
id: ptw-ztdh
status: open
deps: []
links: []
created: 2026-02-05T14:00:22Z
type: task
priority: 2
assignee: legout
external-ref: seed-backlog-deps-and-tags
tags: [tf, backlog]
---
# Update tf-tags-suggest to share classifier logic

## Task
Refactor /tf-tags-suggest (or its underlying implementation) to reuse the same component classifier used by /tf-backlog.

## Context
The seed expects /tf-tags-suggest to remain the fallback when automatic tagging fails. To avoid divergence, both paths should share logic.

## Acceptance Criteria
- [ ] /tf-backlog and /tf-tags-suggest produce consistent `component:*` suggestions.
- [ ] Any shared logic is in a single module/file.
- [ ] Documentation updated to describe the relationship.

## Constraints
- Keep changes small and backwards compatible.

## References
- Seed: seed-backlog-deps-and-tags

