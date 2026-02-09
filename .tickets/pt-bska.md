---
id: pt-bska
status: closed
deps: []
links: [pt-qu8a]
created: 2026-02-08T23:59:25Z
type: task
priority: 2
assignee: legout
external-ref: plan-fix-ralph-progressbar-counter
tags: [tf, backlog, plan, component:api, component:cli, component:workflow]
---
# Refactor progress display API to accept total_tickets separate from max_iterations

## Task
Refactor the progress display plumbing so the displayed `total` is not coupled to `max_iterations`.

## Context
Today `ProgressDisplay.start_ticket(..., total)` is called with `max_iterations`. We need a distinct `total_tickets` input for UX correctness.

## Acceptance Criteria
- [ ] `tf_cli/ralph.py` passes a ticket-derived `total` to `ProgressDisplay.start_ticket()`.
- [ ] `max_iterations` remains purely a loop limit (not UI total).
- [ ] Any existing logging that reports max_iterations remains intact.

## Constraints
- Avoid large refactors; keep changes localized.

## References
- Plan: plan-fix-ralph-progressbar-counter



## Notes

**2026-02-09T00:20:42Z**

Implemented progress display refactor:
- ProgressDisplay.start_ticket() now accepts total_tickets parameter (renamed from total)
- Caller computes total from ready tickets, capped by remaining iterations
- max_iterations remains purely a loop limit, not used for UI display
- All 33 tests pass

Commit: 69bacb4
