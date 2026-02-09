---
id: pt-pbpm
status: open
deps: [pt-6hpl]
links: [pt-za25]
created: 2026-02-09T13:26:39Z
type: task
priority: 2
assignee: legout
external-ref: spike-datastar-py-sanic-datastar-tf-web-ui
tags: [tf, backlog, component:api, component:config, component:tests, component:workflow]
---
# Add board stats DOM target for Datastar patching

## Task
Update the Kanban templates so the ticket counts/stats are patchable independently (e.g. wrap counts in an element with a stable id).

## Context
Currently `/api/refresh` only refreshes `#board`. The counts shown in the header are rendered server-side on initial load and become stale after refresh.

## Acceptance Criteria
- [ ] The counts section is wrapped in an element with a stable id (e.g. `id="board-stats"`).
- [ ] Refreshing the board can update counts without full page reload (hook is in place; can be wired later).
- [ ] No visual regression in the existing board page.

## Constraints
- Avoid large template refactors; keep changes localized to templates.

## References
- Spike: spike-datastar-py-sanic-datastar-tf-web-ui


