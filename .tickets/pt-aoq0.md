---
id: pt-aoq0
status: closed
deps: []
links: [pt-sd01, pt-7t1n]
created: 2026-02-09T09:31:35Z
type: task
priority: 2
assignee: legout
external-ref: seed-tf-ui-web-app
tags: [tf, backlog, component:api, component:cli, component:docs, component:workflow]
---
# Spike: Evaluate textual-web vs FastAPI+HTMX for tf ui web

## Task
Evaluate and compare two approaches for serving tf ui as a web application: textual-web vs FastAPI+HTMX.

## Status
**CLOSED as superseded** - Decision overridden by pt-sd01 which selected **Sanic+Datastar** instead.

## Context
We need to serve the Ticketflow TUI as a web application. Two main options exist:
1. **textual-web**: Minimal changes, serves existing Textual TUI in browser
2. **FastAPI+HTMX**: Full web-native implementation with server-rendered updates

This spike was completed and FastAPI+HTMX was initially selected. However, a subsequent spike (pt-sd01) re-evaluated and selected **Sanic+Datastar** as the final stack.

## Original Acceptance Criteria
- [x] Build working proof-of-concept using textual-web serving existing ui.py
- [x] Build working proof-of-concept using FastAPI+HTMX with basic kanban view
- [x] Document comparison: complexity, maintenance, features, performance
- [x] Document pros/cons of each approach
- [x] Make clear recommendation on which approach to pursue for MVP
- [x] Present findings to team for decision

## Final Decision
**Sanic+Datastar** selected via pt-sd01. See:
- pt-sd01 for decision record
- `.tf/knowledge/topics/spike-sanic-datastar-vs-fastapi-htmx/` for research

## Constraints
- POCs should be minimal but functional (kanban board display minimum)
- Must work with existing ticket data sources (tk CLI, knowledge base)
- Consider single-user local development as primary use case

## References
- Seed: seed-tf-ui-web-app
- Textual Web: https://textual.textualize.io/blog/2023/09/06/textual-web/
- FastAPI: https://fastapi.tiangolo.com/
- HTMX: https://htmx.org/
- **Superseded by**: pt-sd01 (Sanic+Datastar decision)
- **Related**: pt-7t1n (original spike completion)
