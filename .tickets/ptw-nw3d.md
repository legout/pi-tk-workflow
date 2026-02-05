---
id: ptw-nw3d
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
# Add version retrieval helper for CLI

## Task
Add a small helper (e.g., `tf_cli/version.py`) that returns the current Ticketflow version reliably.

## Context
`tf --version` should work across install modes (running from repo, pip/uvx install, etc.). Centralizing version lookup prevents duplicated logic.

## Acceptance Criteria
- [ ] A single function (e.g., `get_version() -> str`) exists and is used by CLI entry points.
- [ ] Works when running from a git checkout and when installed as a Python package.
- [ ] Behavior is documented (fallback order, what happens if version can’t be determined).

## Constraints
- Avoid new dependencies unless clearly justified.

## References
- Seed: seed-add-versioning

