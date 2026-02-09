---
id: pt-fpz7
status: open
deps: [pt-et1v]
links: [pt-et1v]
created: 2026-02-09T11:48:25Z
type: task
priority: 2
assignee: legout
external-ref: plan-allow-to-serve-the-textual-app-as-a-web
tags: [tf, backlog, plan, component:cli, component:config, component:workflow]
---
# Optional: add `tf ui --web` helper (prints serve command)

## Task
Add a minimal helper flag/subcommand that prints the recommended `textual serve …` invocation for the UI.

## Context
This is a convenience feature; it should not re-implement serving.

## Acceptance Criteria
- [ ] `tf ui --web` prints a copy/paste `textual serve "tf ui"` command (or equivalent)
- [ ] Includes warning text about localhost default and public binding risks
- [ ] No config parsing, auth, or process management added

## Constraints
- Keep implementation tiny and easy to remove if it doesn’t pull its weight

## References
- Plan: plan-allow-to-serve-the-textual-app-as-a-web

