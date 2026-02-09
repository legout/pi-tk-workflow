---
id: pt-et1v
status: open
deps: [pt-uo1b]
links: [pt-uo1b, pt-fpz7]
created: 2026-02-09T11:48:25Z
type: task
priority: 2
assignee: legout
external-ref: plan-allow-to-serve-the-textual-app-as-a-web
tags: [tf, backlog, plan, component:workflow]
---
# Audit web-served UI styling/assets (CSS/themes)

## Task
Check that the UI renders with correct styling when served via `textual serve` and fix any missing asset / path issues.

## Context
Plan calls out risk that relative paths may not resolve correctly under web serving.

## Acceptance Criteria
- [ ] Web mode loads without missing CSS/theme regressions
- [ ] If issues found, adjust asset loading to use robust paths (package resources / absolute paths)

## Constraints
- Keep changes minimal; no redesign

## References
- Plan: plan-allow-to-serve-the-textual-app-as-a-web

