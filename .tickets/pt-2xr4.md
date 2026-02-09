---
id: pt-2xr4
status: open
deps: [pt-q2og]
links: [pt-q2og]
created: 2026-02-09T13:42:03Z
type: task
priority: 2
assignee: legout
external-ref: spike-modern-simple-css-dashboard-kanban
tags: [tf, backlog, component:api, component:cli, component:docs]
---
# Add dark-mode toggle (or auto dark mode) for web UI

## Task
Provide a basic dark-mode experience for the web UI using either Pico’s theme mechanism or a small token override.

## Context
Modern dashboards often need dark mode. Pico supports `prefers-color-scheme` and `data-theme` toggling; a minimal toggle is sufficient.

## Acceptance Criteria
- [ ] Web UI supports dark mode automatically (prefers-color-scheme) OR via `data-theme="dark"`.
- [ ] Board columns/cards remain readable in dark mode.
- [ ] Implementation is documented (short note in template or docs).

## Constraints
- No heavy JS; prefer CSS-only or minimal inline script.

## References
- Spike: spike-modern-simple-css-dashboard-kanban
- Pico theme docs: https://picocss.com


