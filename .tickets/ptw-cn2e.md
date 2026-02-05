---
id: ptw-cn2e
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
# Add ticket linking in tf-backlog using tk link

## Task
Add support in /tf-backlog to link tightly-related tickets using `tk link`.

## Context
Links are symmetric and help discovery/grouping for related work that is not strictly dependent. This is complementary to `component:*` tags.

## Acceptance Criteria
- [ ] /tf-backlog links a small number of obvious related pairs (conservative).
- [ ] Linking criteria are documented (e.g., same component + adjacent in creation order, or title similarity).
- [ ] Provide an opt-out (e.g., `--no-links`).

## Constraints
- Under-linking is preferable to over-linking.

## References
- Seed: seed-backlog-deps-and-tags


## Notes

**2026-02-05T15:01:37Z**

Implemented ticket linking support in /tf-backlog.

Changes:
- Added --no-links flag for opting out of automatic linking
- Linking criteria: same component + adjacent creation order, or title similarity
- Max 2-3 links per ticket (conservative approach)
- Uses tk link for symmetric relationships

Commit: d3aa925
Follow-ups: ptw-8f4r (docs example), ptw-uv0x (links-only flag)
