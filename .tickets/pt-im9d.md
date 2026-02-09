---
id: pt-im9d
status: closed
deps: [pt-tpwl]
links: [pt-tpwl]
created: 2026-02-08T23:04:18Z
type: task
priority: 2
assignee: legout
external-ref: seed-fix-ralph-agents-md
tags: [tf, backlog, component:cli, component:config, component:docs, component:tests, component:workflow]
---
# Add tests for Ralph lessons learned persistence to AGENTS.md

## Task
Add/extend unit tests verifying `.tf/ralph/AGENTS.md` is created and appended-to when lessons are present.

## Context
The current bug is a chicken-egg condition: lessons are only written if the file exists. Tests should prevent regressions by exercising the `update_state()` path with a temp `.tf/` directory and a simulated ticket artifact directory containing `close-summary.md` with a "Lessons Learned" section.

## Acceptance Criteria
- [ ] Test: first lesson creates `.tf/ralph/AGENTS.md` with template + appended lesson
- [ ] Test: second lesson appends (does not overwrite)
- [ ] Test: when no Lessons Learned section exists, AGENTS.md is unchanged/not created

## Constraints
- Use existing pytest patterns and temp directories
- Avoid requiring real `pi` execution; call `update_state()` directly

## References
- Seed: seed-fix-ralph-agents-md
- File: `tf_cli/ralph.py`
- Tests: `tests/` (start with `tests/test_agentsmd.py` if relevant)



## Notes

**2026-02-09T07:22:09Z**

Implementation complete. Added 11 comprehensive tests for Ralph lessons learned persistence to AGENTS.md in tests/test_ralph_state.py. Tests cover: first lesson creation, second lesson appending, no-lessons handling, progress updates, and issue count extraction. Minor cleanup: removed unused imports, fixed docstring. Commit: 949d67f
