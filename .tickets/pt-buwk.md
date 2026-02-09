---
id: pt-buwk
status: closed
deps: [pt-7mvl]
links: [pt-7mvl, pt-ihfv]
created: 2026-02-08T23:56:07Z
type: task
priority: 2
assignee: legout
external-ref: seed-remove-session-param-from-ralph
tags: [tf, backlog, component:cli, component:tests, component:workflow]
---
# Add regression test/smoke coverage for ralph pi invocation args

## Task
Add a regression test (or CLI smoke test) that asserts the generated `pi` invocation for `tf ralph start/run` does not include `--session`.

## Context
This change is easy to regress because it’s a small flag in a subprocess call. A test should lock in the desired command construction.

## Acceptance Criteria
- [ ] Test fails if `--session` appears in the constructed `pi` argv for start/run.
- [ ] Test is stable and does not require actually running Pi (mock subprocess/command builder).
- [ ] `pytest` (or existing test runner) passes locally.

## Constraints
- Prefer unit-level test (mocking) over integration (slow/flaky).

## References
- Seed: seed-remove-session-param-from-ralph



## Notes

**2026-02-09T00:24:38Z**

Implementation complete.

Added tests/test_ralph_pi_invocation.py with regression tests ensuring pi invocation for ralph start/run does not include --session.

Commit: e05c07e

Note: Tests currently fail as expected until pt-ihfv (Remove pi --session forwarding) is implemented.
