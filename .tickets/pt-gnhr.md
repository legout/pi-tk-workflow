---
id: pt-gnhr
status: open
deps: [pt-33o0]
links: [pt-33o0]
created: 2026-02-09T13:42:03Z
type: task
priority: 2
assignee: legout
external-ref: spike-modern-simple-css-dashboard-kanban
tags: [tf, backlog, component:config]
---
# Improve Kanban board layout CSS (grid minmax/auto-fit, better responsiveness)

## Task
Refine the board grid/columns CSS to behave well across desktop/tablet/mobile using modern Grid patterns.

## Context
Kanban boards need predictable columns, readable cards, and graceful stacking. Modern Grid patterns like `minmax()` and responsive breakpoints help.

## Acceptance Criteria
- [ ] Board uses a robust grid definition (e.g. `repeat(4, minmax(240px, 1fr))` or `auto-fit`).
- [ ] Tablet: 2 columns; Mobile: 1 column (or equivalent responsive strategy).
- [ ] Columns have consistent header + scroll behavior is acceptable.

## Constraints
- Avoid JS-based layout; CSS-only.

## References
- Spike: spike-modern-simple-css-dashboard-kanban


