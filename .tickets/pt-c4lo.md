---
id: pt-c4lo
status: closed
deps: [pt-ba0n]
links: [pt-sd01]
created: 2026-02-09T09:32:03Z
type: task
priority: 2
assignee: legout
external-ref: seed-tf-ui-web-app
tags: [tf, backlog, component:cli, component:docs, component:workflow]
---
# Implement ticket detail view in web UI (Datastar)

## Task
Implement ticket detail view showing full ticket information using **Datastar**.

## Context
When a user clicks on a ticket (from kanban or topic view), they should see detailed ticket information including full description, status, priority, and related metadata. Uses **Datastar** for navigation and interactions.

## Acceptance Criteria
- [ ] Display ticket ID, title, status, priority
- [ ] Render ticket description as formatted markdown
- [ ] Show ticket tags and external references
- [ ] Display created/updated timestamps
- [ ] Add button/link to open ticket in external system (tk web)
- [ ] Add back button to return to previous view using `data-on:click="@get('/board')"`

## Datastar-Specific Implementation Notes
- Use `data-on:click` for back navigation
- Markdown rendering happens server-side; Datastar displays HTML
- For any interactive elements (edit, close ticket), use `data-on:click="@post(...)"`

## Example Template Pattern
```html
<div id="ticket-detail">
  <button data-on:click="@get('/board')">← Back to Board</button>
  
  <h1><span class="ticket-id">{{ ticket.id }}</span> {{ ticket.title }}</h1>
  
  <div class="ticket-meta">
    <span class="status status-{{ ticket.status }}">{{ ticket.status }}</span>
    <span class="priority p{{ ticket.priority }}">P{{ ticket.priority }}</span>
    <span class="created">{{ ticket.created }}</span>
  </div>
  
  <div class="ticket-tags">
    {%- for tag in ticket.tags %}
    <span class="tag">{{ tag }}</span>
    {%- endfor %}
  </div>
  
  <div class="ticket-body markdown">
    {{ ticket.body_html | safe }}
  </div>
  
  <a href="https://tracker.example.com/{{ ticket.id }}" target="_blank">
    Open in Tracker →
  </a>
</div>
```

## Constraints
- Description must be rendered as markdown (server-side)
- Layout should be readable and scrollable
- Work with existing ticket data structure from TicketLoader
- Pin Datastar CDN version to avoid breaking changes

## References
- Seed: seed-tf-ui-web-app
- Decision: pt-sd01 (Sanic+Datastar)
- Datastar docs: https://data-star.dev
- Datastar actions: https://data-star.dev/reference/actions
- tf_cli/ticket_loader.py - Ticket dataclass

## Notes

**2026-02-09T13:59:17Z**

Implemented ticket detail view with:

- Server-side markdown rendering using Python markdown library
- Datastar navigation (@get('/board') for back button)
- Full ticket metadata display (ID, title, status, priority, tags, timestamps)
- Linked tickets and dependencies sections
- External link placeholder for tk web integration

Files changed:
- examples/web-ui-poc/sanic-datastar/requirements.txt (new)
- examples/web-ui-poc/sanic-datastar/web_app.py
- examples/web-ui-poc/sanic-datastar/templates/ticket.html

Commit: 5855a72
Review: 0 Critical, 0 Major, 0 Minor (all acceptance criteria met)
Artifacts: .tf/knowledge/tickets/pt-c4lo/
