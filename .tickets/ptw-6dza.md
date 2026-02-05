---
id: ptw-6dza
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
# Infer and apply deps for seed backlogs (default chain + hints)

## Task
Enhance /tf-backlog (seed mode) to infer and apply ticket dependencies via `tk dep`.

## Context
Immediately after backlog creation, users expect `tk ready` and `tk blocked` to reflect a meaningful work order. For seed mode, a conservative default is a simple chain in creation order, with optional hint-based adjustments.

## Acceptance Criteria
- [x] /tf-backlog applies at least a simple dependency chain (ticket N depends on ticket N-1) unless disabled.
- [x] If obvious ordering cues exist (e.g., "define" -> "implement" -> "test"), they can override the naive chain.
- [x] A clear escape hatch exists (e.g., flag/arg like `--no-deps`).

## Notes
- Implementation: 2026-02-05
- Files changed: prompts/tf-backlog.md, skills/tf-planning/SKILL.md
- Review: All 3 reviewers passed (0 critical/major/minor issues)
- Follow-ups: 5 tickets created (ptw-f1 through ptw-f5) for warnings/suggestions
- Status: COMPLETE

## Constraints
- Conservative: avoid incorrect deps; prefer fewer deps over wrong deps.

## References
- Seed: seed-backlog-deps-and-tags

