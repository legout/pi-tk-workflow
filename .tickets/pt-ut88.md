---
id: pt-ut88
status: closed
deps: [pt-4dji]
links: [pt-2s2s, pt-cj59]
created: 2026-02-08T18:41:27Z
type: task
priority: 2
assignee: legout
external-ref: seed-move-ralph-session-away-from-tf-ralph-us
tags: [tf, backlog, component:api, component:cli, component:config, component:tests, component:workflow]
---
# Add tests for tf ralph sessionDir resolution + legacy warning

## Task
Add unit tests covering sessionDir resolution (new default, config override, legacy dir detection/warning).

## Context
There are existing tests for `tf_cli/ralph` flag parsing and JSON capture. Extend test coverage to ensure this change is safe.

## Acceptance Criteria
- [ ] Tests cover new default path selection
- [ ] Tests cover config override semantics (relative vs absolute)
- [ ] Tests cover legacy `.tf/ralph/sessions` detection and warn-once behavior

## Constraints
- Prefer tmp_path fixtures and mocking; no real Pi invocation

## References
- Seed: seed-move-ralph-session-away-from-tf-ralph-us



## Notes

**2026-02-09T07:54:56Z**

--message Implementation complete. Added 21 unit tests covering sessionDir resolution and legacy warning behavior.

Commit: f4d06fa8b8a6ace70cfae62b81967e643ef8a8b2

Test Results: All 21 tests pass
- TestDefaultSessionDir: 3 tests
- TestConfigOverrideSemantics: 6 tests  
- TestLegacyWarningBehavior: 5 tests
- TestForceLegacyEnvironmentVariable: 4 tests
- TestSessionDirEdgeCases: 3 tests

Files Changed:
- tests/test_ralph_session_dir.py (435 lines, new file)
