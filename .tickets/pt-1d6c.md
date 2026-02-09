---
id: pt-1d6c
status: closed
deps: [pt-fo58]
links: [pt-sd01]
created: 2026-02-09T09:32:03Z
type: task
priority: 2
assignee: legout
external-ref: seed-tf-ui-web-app
tags: [tf, backlog, component:cli, component:docs, component:workflow]
---
# Implement kanban board view in web UI (Datastar)

## Task
Implement the kanban board view displaying tickets in Ready/Blocked/In Progress/Closed columns using **Datastar**.

## Context
The kanban board is the primary view of the tf ui. In web mode, this should display tickets in their respective columns with basic ticket information. Uses **Datastar** for reactivity and server interactions.

## Acceptance Criteria
- [ ] Display four columns: Ready, Blocked, In Progress, Closed
- [ ] Load tickets using existing TicketLoader and BoardClassifier
- [ ] Display ticket cards with ID, title, and priority
- [ ] Color-code or label tickets by priority (P0-P4)
- [ ] Click ticket card to open detail view (using `data-on:click="@get('/ticket/{id}')"`)
- [ ] Manual refresh button using `data-on:click="@get('/api/refresh')"`
- [ ] Handle empty states (no tickets in a column)
- [ ] Use Datastar's `data-signals` for any client-side state if needed

## Datastar-Specific Implementation Notes
- Include Datastar CDN in base template: `https://cdn.jsdelivr.net/gh/starfederation/datastar@v1.0.0-RC.7/bundles/datastar.js`
- Use colon-delimited attributes: `data-on:click` (not `data-on-click`)
- Backend endpoints return HTML fragments; Datastar morphs them into DOM
- For partial board refresh, return only the board HTML fragment

## Example Template Pattern
```html
<div id="board">
  <div class="column" id="col-ready">
    {%- for ticket in columns.ready %}
    <div class="ticket-card" id="ticket-{{ ticket.id }}"
         data-on:click="@get('/ticket/{{ ticket.id }}')">
      <span class="priority p{{ ticket.priority }}">P{{ ticket.priority }}</span>
      <span class="ticket-id">{{ ticket.id }}</span>
      <span class="title">{{ ticket.title }}</span>
    </div>
    {%- endfor %}
  </div>
  <!-- similar for blocked, in_progress, closed -->
</div>
<button data-on:click="@get('/api/refresh')">Refresh</button>
```

## Constraints
- Reuse existing ticket loading and classification logic
- Page load time < 2 seconds for < 100 tickets
- Works in modern browsers (Chrome, Firefox, Safari, Edge)
- Responsive layout (columns side by side, scrollable)
- Pin Datastar CDN version to avoid breaking changes

## References
- Seed: seed-tf-ui-web-app
- Decision: pt-sd01 (Sanic+Datastar)
- Datastar docs: https://data-star.dev
- Datastar actions: https://data-star.dev/reference/actions
- tf_cli/ticket_loader.py - TicketLoader class
- tf_cli/board_classifier.py - BoardClassifier class

## Notes

**2026-02-09T13:27:00Z**

Implementation completed and critical issues fixed.

**Fixed Issues:**
1. Empty board misclassified as error - now checks for None explicitly
2. XSS vulnerability - enabled Jinja2 autoescape
3. Datastar morphing - added id=board to fragment root
4. Stale stats - header with counts now included in refresh fragment
5. Code duplication - extracted _build_columns_data() helper
6. Priority None guard - displays '—' instead of 'PNone'

**Commit:** 336d7b3
**Files changed:**
- tf_cli/web_ui.py
- tf_cli/templates/_board.html
- tf_cli/templates/index.html
- tf_cli/templates/ticket.html
- tf_cli/templates/base.html
