---
id: pt-uo1b
status: open
deps: [pt-ls9y]
links: [pt-ls9y, pt-et1v]
created: 2026-02-09T11:48:25Z
type: task
priority: 2
assignee: legout
external-ref: plan-allow-to-serve-the-textual-app-as-a-web
tags: [tf, backlog, plan, component:cli, component:config, component:tests, component:workflow]
---
# Add CI smoke test: headless import of `tf_cli.ui`

## Task
Add a minimal automated smoke test that verifies `tf_cli.ui` can be imported in CI/headless contexts.

## Context
Web serving runs in a non-TTY environment; we need confidence the module doesn’t crash on import.

## Acceptance Criteria
- [ ] Add a test that imports `tf_cli.ui` without raising
- [ ] Test runs in existing CI test suite
- [ ] No additional heavy dependencies added

## Constraints
- Avoid launching the full interactive app in CI

## References
- Plan: plan-allow-to-serve-the-textual-app-as-a-web

