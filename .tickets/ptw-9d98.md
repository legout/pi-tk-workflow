---
id: ptw-9d98
status: closed
deps: []
links: []
created: 2026-01-29T09:15:56Z
type: feature
priority: 2
assignee: legout
tags: [irf, workflow]
---
# Config-driven MCP server selection

Add workflow.mcpServers list to config and update bin/irf setup to only write those servers to mcp.json.

## Acceptance Criteria

- workflow.mcpServers controls which MCP servers are written
- Empty list results in no servers configured
- bin/irf setup respects the list

