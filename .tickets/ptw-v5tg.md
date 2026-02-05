---
id: ptw-v5tg
status: open
deps: []
links: []
created: 2026-02-05T13:38:20Z
type: task
priority: 2
assignee: legout
external-ref: seed-add-versioning
tags: [tf, backlog]
---
# Add minimal smoke test for tf --version

## Task
Add a minimal smoke test to ensure `tf --version` returns a version string and exits successfully.

## Context
Version output should not regress silently; a small test helps catch breakage early.

## Acceptance Criteria
- [ ] A test (or script) runs `tf --version` and asserts exit code 0.
- [ ] Output is non-empty and matches expected format (basic SemVer check).
- [ ] Document how to run the test locally.

## Constraints
- Prefer stdlib-only (no new test framework required for MVP).

## References
- Seed: seed-add-versioning
