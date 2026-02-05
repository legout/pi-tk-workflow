---
id: ptw-ueyl
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
# Implement tf --version (and -V) across entry points

## Task
Implement `tf --version` (and optionally `-V`) to print the current version string.

## Context
Seed success metric: users can reliably retrieve the installed version via CLI. The repo currently has multiple CLI layers (Python + legacy shell) and should behave consistently.

## Acceptance Criteria
- [ ] `tf --version` prints just the version (e.g., `0.1.0`) and exits 0.
- [ ] `tf -V` works (if implemented) and is documented in usage/help output.
- [ ] No breaking changes to existing command behavior.

## Constraints
- Additive only; keep implementation simple.

## References
- Seed: seed-add-versioning
