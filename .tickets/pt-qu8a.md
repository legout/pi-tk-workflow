---
id: pt-qu8a
status: closed
deps: [pt-bska]
links: [pt-u3vz, pt-bska]
created: 2026-02-08T23:59:25Z
type: task
priority: 2
assignee: legout
external-ref: plan-fix-ralph-progressbar-counter
tags: [tf, backlog, plan, component:workflow]
---
# Compute correct progress total for tf ralph --progress (ready tickets snapshot)

## Task
Change the serial `tf ralph start --progress` counter total to reflect the number of ready tickets, not `maxIterations` (default 50).

## Context
Currently progress display receives `max_iterations` as `total`, which makes counters like `[1/50]` misleading on small backlogs.

## Acceptance Criteria
- [ ] Progress display total is derived from `len(list_ready_tickets(...))` computed once at loop start.
- [ ] If ticket listing fails, progress shows an unknown/placeholder total (avoid showing 50).
- [ ] No behavior change when `--progress` is not used.

## Constraints
- Keep work lightweight (no expensive per-iteration listing).

## References
- Plan: plan-fix-ralph-progressbar-counter



## Notes

**2026-02-09T07:44:57Z**

Implemented: Changed progress display to show actual ready tickets count instead of max_iterations (50).\n\nChanges:\n- Compute len(list_ready_tickets()) once at loop start\n- Show '?' placeholder if listing fails (avoid showing 50)\n- Updated ProgressDisplay to accept Union[int, str] for total\n\nCommit: 7c5cd14\nTests: 104 passed (22 progress + 82 ralph tests)
