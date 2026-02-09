---
id: pt-7t1n
status: closed
deps: []
links: []
created: 2026-02-09T09:32:03Z
type: task
priority: 2
assignee: legout
external-ref: seed-tf-ui-web-app
tags: [tf, backlog, component:api, component:cli, component:docs, component:workflow]
---
# Spike: Evaluate textual-web vs FastAPI+HTMX for tf ui web

## Task
Evaluate and compare two approaches for serving tf ui as a web application: textual-web vs FastAPI+HTMX.

## Context
We need to serve the Ticketflow TUI as a web application. Two main options exist:
1. **textual-web**: Minimal changes, serves existing Textual TUI in browser
2. **FastAPI+HTMX**: Full web-native implementation with server-rendered updates

This spike will build proof-of-concepts for both approaches and document the decision.

## Acceptance Criteria
- [ ] Build working proof-of-concept using textual-web serving existing ui.py
- [ ] Build working proof-of-concept using FastAPI+HTMX with basic kanban view
- [ ] Document comparison: complexity, maintenance, features, performance
- [ ] Document pros/cons of each approach
- [ ] Make clear recommendation on which approach to pursue for MVP
- [ ] Present findings to team for decision

## Constraints
- POCs should be minimal but functional (kanban board display minimum)
- Must work with existing ticket data sources (tk CLI, knowledge base)
- Consider single-user local development as primary use case

## References
- Seed: seed-tf-ui-web-app
- Textual Web: https://textual.textualize.io/blog/2023/09/06/textual-web/
- FastAPI: https://fastapi.tiangolo.com/
- HTMX: https://htmx.org/


## Notes

**2026-02-09T09:39:45Z**

## Spike Complete: Web UI Approach Selected

### POCs Built
1. **textual-web POC** (`examples/web-ui-poc/textual-web/`)
   - Configuration to serve existing TUI in browser
   - Zero code changes, immediate results

2. **FastAPI+HTMX POC** (`examples/web-ui-poc/fastapi-htmx/`)
   - Full web-native kanban board
   - Responsive design, bookmarkable URLs
   - Run: `python web_app.py` → http://127.0.0.1:8080

### Recommendation: FastAPI+HTMX

**Decision**: Proceed with FastAPI+HTMX for MVP implementation.

**Rationale**:
- Native web UX with mobile support
- Bookmarkable URLs for sharing specific tickets
- Better accessibility (semantic HTML)
- Foundation for future multi-user features
- MVP scope (localhost-only, manual refresh) keeps initial work manageable

**Full Analysis**: See `.tf/knowledge/tickets/pt-7t1n/comparison.md`

### Committed
- POCs moved to `examples/web-ui-poc/` for team access
- Commit: `pt-7t1n: Add web UI POCs - textual-web and FastAPI+HTMX`

### Next Steps
Create implementation ticket for FastAPI+HTMX web UI MVP.
