---
id: pt-cvj1
status: closed
deps: [pt-8o4i]
links: [pt-8o4i, pt-cje7]
created: 2026-02-09T12:46:53Z
type: task
priority: 2
assignee: legout
external-ref: plan-update-zai-vision-mcp
tags: [tf, backlog, plan, component:agents, component:cli, component:config, component:tests, component:workflow]
---
# Update tests for command-based `zai-vision` MCP config

## Task
Update unit tests to reflect that `zai-vision` is command-based while other ZAI MCP servers remain URL-based.

## Context
`tests/test_login.py::test_includes_zai_servers_with_key` currently assumes URL-based `zai-vision` and must be updated.

## Acceptance Criteria
- [ ] Test asserts `zai-web-search` and `zai-web-reader` still have `url` and `Authorization: Bearer ...`
- [ ] Test asserts `zai-vision` uses `command/args/env` as specified
- [ ] `pytest` passes

## Constraints
- Keep assertions specific (avoid brittle full-file comparisons)

## References
- Plan: plan-update-zai-vision-mcp


## Notes

**2026-02-09T14:02:28Z**

Implemented test updates for command-based zai-vision MCP config.

Changes:
- Updated test_includes_zai_servers_with_key to assert URL-based config for zai-web-search and zai-web-reader
- Added assertions for command-based zai-vision config (command, args, env vars)
- All 17 tests pass

Commit: b246c90
