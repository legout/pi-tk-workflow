---
id: pt-ls9y
status: open
deps: [pt-sf9w]
links: [pt-sf9w, pt-uo1b]
created: 2026-02-09T11:48:25Z
type: task
priority: 2
assignee: legout
external-ref: plan-allow-to-serve-the-textual-app-as-a-web
tags: [tf, backlog, plan, component:cli, component:docs, component:workflow]
---
# Document web mode: `textual serve` for `tf ui`

## Task
Add a “Web mode” section to user-facing docs describing how to run the TUI in a browser via `textual serve`.

## Context
We want a safe-by-default, copy/paste workflow for local browser access, with clear warnings for non-local binding.

## Acceptance Criteria
- [ ] Docs include prerequisites (`textual-dev` provides the `textual` CLI)
- [ ] Docs include both commands: `textual serve "tf ui"` and dev fallback `textual serve "python -m tf_cli.ui"`
- [ ] Docs mention `textual serve --help` for host/port flags and warn against public binding
- [ ] Docs state lifecycle behavior (what happens when the browser tab closes)

## Constraints
- Keep `textual-web` explicitly out-of-scope unless marked experimental

## References
- Plan: plan-allow-to-serve-the-textual-app-as-a-web

