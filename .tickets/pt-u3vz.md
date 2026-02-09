---
id: pt-u3vz
status: closed
deps: [pt-qu8a]
links: [pt-qu8a]
created: 2026-02-08T23:59:25Z
type: task
priority: 2
assignee: legout
external-ref: plan-fix-ralph-progressbar-counter
tags: [tf, backlog, plan, component:cli, component:tests, component:workflow]
---
# Add unit tests for tf ralph progress total (no default 50)

## Task
Add unit tests to prevent regressions where progress total reverts to `maxIterations` (50) instead of actual ready ticket count.

## Context
The bug is a small argument mismatch and is easy to reintroduce. Tests should assert the generated progress total equals the ready-ticket snapshot.

## Acceptance Criteria
- [ ] Tests fail if `[*/50]` appears when the ready-ticket count is not 50.
- [ ] Tests do not shell out to `pi`; use mocks/fakes for ticket listing and progress display.
- [ ] `pytest` passes locally.

## Constraints
- Prefer unit-level tests with subprocess mocking.

## References
- Plan: plan-fix-ralph-progressbar-counter



## Notes

**2026-02-09T07:50:45Z**

Implemented: Added 7 unit tests for Ralph progress total computation to prevent regressions.

Changes:
- tests/test_ralph_progress_total.py (405 lines, 7 test cases)

Test Coverage:
- Progress total equals actual ready ticket count (not maxIterations/50)
- '?' placeholder shown when ticket listing fails  
- Regression tests ensure [*/50] doesn't appear incorrectly
- No ProgressDisplay created without --progress flag

Commit: 34c5dea
Tests: 7/7 passed (new) + 104/104 passed (existing ralph tests)
