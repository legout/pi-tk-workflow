---
id: pt-znph
status: closed
deps: [pt-1x64]
links: [pt-1d6c]
created: 2026-02-09T09:31:34Z
type: task
priority: 2
assignee: legout
external-ref: seed-tf-ui-web-app
tags: [tf, backlog, component:cli, component:docs, component:workflow]
---
# Implement kanban board view in web UI

## Task
Implement the kanban board view displaying tickets in Ready/Blocked/In Progress/Closed columns.

## Status
**CLOSED as duplicate** - Consolidated into pt-1d6c. See pt-sd01 for stack decision (Sanic+Datastar).

## Context
The kanban board is the primary view of the tf ui. In web mode, this should display tickets in their respective columns with basic ticket information.

## Acceptance Criteria
- [ ] Display four columns: Ready, Blocked, In Progress, Closed
- [ ] Load tickets using existing TicketLoader and BoardClassifier
- [ ] Display ticket cards with ID, title, and priority
- [ ] Color-code or label tickets by priority (P0-P4)
- [ ] Click ticket card to open detail view
- [ ] Manual refresh button to reload ticket data
- [ ] Handle empty states (no tickets in a column)

## Constraints
- Reuse existing ticket loading and classification logic
- Page load time < 2 seconds for < 100 tickets
- Works in modern browsers (Chrome, Firefox, Safari, Edge)
- Responsive layout (columns side by side, scrollable)

## References
- Seed: seed-tf-ui-web-app
- **Consolidated into**: pt-1d6c (Sanic+Datastar implementation)
- **Stack decision**: pt-sd01
- tf_cli/ticket_loader.py - TicketLoader class
- tf_cli/board_classifier.py - BoardClassifier class
