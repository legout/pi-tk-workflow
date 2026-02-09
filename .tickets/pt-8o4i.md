---
id: pt-8o4i
status: closed
deps: []
links: [pt-cvj1]
created: 2026-02-09T12:46:53Z
type: task
priority: 2
assignee: legout
external-ref: plan-update-zai-vision-mcp
tags: [tf, backlog, plan, component:agents, component:api, component:cli, component:config, component:workflow]
---
# Update tf login/setup to write command-based `zai-vision` MCP server

## Task
Update MCP config generation so `zai-vision` uses the new command-based server (`npx -y @z_ai/mcp-server`) instead of the legacy URL endpoint.

## Context
Current `~/.pi/agent/mcp.json` uses a command-based `zai-vision` entry, but `tf login`/`tf setup` currently writes a URL-based entry from `tf_cli/login.py`.

## Acceptance Criteria
- [ ] `tf_cli.login.configure_mcp()` writes `zai-vision` with: `command: npx`, `args: ["-y","@z_ai/mcp-server"]`, and `env: {Z_AI_API_KEY, Z_AI_MODE="ZAI"}`
- [ ] `zai-web-search` and `zai-web-reader` remain URL-based with bearer `Authorization` header
- [ ] Generated `mcp.json` remains valid JSON and permissions are still best-effort `0o600`

## Constraints
- Only change `zai-vision`; do not change other servers

## References
- Plan: plan-update-zai-vision-mcp


## Notes

**2026-02-09T13:35:23Z**

Implemented command-based zai-vision MCP server configuration.

Changes:
- Modified configure_mcp() in tf_cli/login.py
- zai-vision now uses: command='npx', args=['-y', '@z_ai/mcp-server'], env={Z_AI_API_KEY, Z_AI_MODE='ZAI'}
- zai-web-search and zai-web-reader remain URL-based as required
- All 17 tests pass
- Commit: fdb43f2
