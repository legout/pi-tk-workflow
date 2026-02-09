---
id: pt-tpz9
status: closed
deps: [pt-pdha]
links: [pt-c4lo]
created: 2026-02-09T09:31:35Z
type: task
priority: 2
assignee: legout
external-ref: seed-tf-ui-web-app
tags: [tf, backlog, component:cli, component:docs, component:workflow]
---
# Implement ticket detail view in web UI

## Task
Implement ticket detail view showing full ticket information.

## Status
**CLOSED as duplicate** - Consolidated into pt-c4lo. See pt-sd01 for stack decision (Sanic+Datastar).

## Context
When a user clicks on a ticket (from kanban or topic view), they should see detailed ticket information including full description, status, priority, and related metadata.

## Acceptance Criteria
- [ ] Display ticket ID, title, status, priority
- [ ] Render ticket description as formatted markdown
- [ ] Show ticket tags and external references
- [ ] Display created/updated timestamps
- [ ] Add button/link to open ticket in external system (tk web)
- [ ] Add back button to return to previous view

## Constraints
- Description must be rendered as markdown
- Layout should be readable and scrollable
- Work with existing ticket data structure from TicketLoader

## References
- Seed: seed-tf-ui-web-app
- **Consolidated into**: pt-c4lo (Sanic+Datastar implementation)
- **Stack decision**: pt-sd01
- tf_cli/ticket_loader.py - Ticket dataclass
