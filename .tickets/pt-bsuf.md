---
id: pt-bsuf
status: closed
deps: []
links: [pt-7p2i, pt-33o0]
created: 2026-02-09T13:42:03Z
type: task
priority: 2
assignee: legout
external-ref: spike-modern-simple-css-dashboard-kanban
tags: [tf, backlog, component:api, component:cli, component:docs, component:workflow]
---
# Integrate Pico.css (classless) into Sanic+Datastar web UI templates

## Task
Add Pico.css classless stylesheet to the web UI base template and verify core pages render correctly.

## Context
The current web UI uses large inline CSS blocks in the Jinja templates. Pico.css provides modern defaults (typography/buttons/forms) with a single `<link>` and minimal markup changes.

## Acceptance Criteria
- [ ] `tf_cli/templates/base.html` includes Pico.css classless via CDN (pinned major version).
- [ ] Board page and ticket detail page still render and remain usable.
- [ ] Any conflicting existing CSS is reduced/adjusted (no broken layout).

## Constraints
- Keep changes incremental; avoid redesigning templates.
- Prefer classless Pico variant to avoid HTML class churn.

## References
- Spike: spike-modern-simple-css-dashboard-kanban
- Pico.css docs/CDN: https://picocss.com



## Notes

**2026-02-09T13:44:34Z**

Implemented Pico.css classless integration:\n- Added Pico CSS CDN link (pinned to v2)\n- Scoped header/nav/main with .app-* classes to avoid conflicts\n- Removed conflicting reset styles\n- Preserved priority badge colors and status indicators\n- Commit: df8db41
