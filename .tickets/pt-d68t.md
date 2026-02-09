---
id: pt-d68t
status: closed
deps: [pt-yx8a]
links: [pt-yx8a, pt-qmor]
created: 2026-02-09T00:26:44Z
type: task
priority: 2
assignee: legout
external-ref: seed-add-timestamps-to-the-progressbar-when-r
tags: [tf, backlog, component:cli, component:workflow]
---
# Implement timestamp prefix in ProgressDisplay for tf ralph --progress

## Task
Add a timestamp prefix to the progress display output used by the serial Ralph loop when `--progress` is enabled.

## Context
`ProgressDisplay` in `tf_cli/ralph.py` draws lines like `[i/total] Processing ...`. We want to include a timestamp without breaking TTY rendering or non-TTY logs.

## Acceptance Criteria
- [ ] Progress lines are prefixed with a timestamp (per spec ticket).
- [ ] Works in TTY mode (carriage return updates still correct).
- [ ] Works in non-TTY mode (no control characters; readable logs).
- [ ] No output change when `--progress` is not used.

## Constraints
- Keep overhead minimal (cheap time formatting only).

## References
- Seed: seed-add-timestamps-to-the-progressbar-when-r



## Notes

**2026-02-09T08:03:16Z**

Implemented timestamp prefix in ProgressDisplay._draw() method.

Changes:
- tf_cli/ralph.py: Added HH:MM:SS timestamp prefix to all progress lines
- tests/test_progress_display.py: Updated 22 tests for timestamp assertions

Acceptance criteria met:
✓ Progress lines prefixed with timestamp
✓ Works in TTY mode (carriage return updates correct)
✓ Works in non-TTY mode (readable logs)
✓ No output change when --progress not used

Commit: 75161ab
Review: 0 issues (Critical/Major/Minor)
