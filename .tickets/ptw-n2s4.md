---
id: ptw-n2s4
status: open
deps: []
links: []
created: 2026-02-05T13:38:19Z
type: task
priority: 2
assignee: legout
external-ref: seed-add-versioning
tags: [tf, backlog]
---
# Define version source of truth + sync package metadata

## Task
Decide and document the canonical version source for Ticketflow, and make package metadata consistent with it.

## Context
The seed calls for a single source of truth for the project version. Today, the repo has multiple version fields (e.g., `package.json` vs `pyproject.toml`) that can drift.

## Acceptance Criteria
- [ ] Canonical version source is chosen and documented (file/path + update procedure).
- [ ] `package.json` and `pyproject.toml` (and any other relevant metadata) are updated to match.
- [ ] A short note is added on how to bump versions (manual is fine for MVP).

## Constraints
- Keep it lightweight; no CI/release automation required for MVP.

## References
- Seed: seed-add-versioning

