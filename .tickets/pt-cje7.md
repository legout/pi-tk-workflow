---
id: pt-cje7
status: open
deps: [pt-cvj1]
links: [pt-cvj1]
created: 2026-02-09T12:46:53Z
type: task
priority: 2
assignee: legout
external-ref: plan-update-zai-vision-mcp
tags: [tf, backlog, plan, component:agents, component:docs, component:workflow]
---
# Add release note / doc note about new `zai-vision` MCP server type

## Task
Add a short note in docs (or changelog) that `zai-vision` is now provided via a local npx MCP server, and what prerequisites are needed (Node+npx).

## Context
Users may need Node.js available for `npx` to work; otherwise vision MCP tooling won't start.

## Acceptance Criteria
- [ ] Docs mention that `zai-vision` uses `npx -y @z_ai/mcp-server`
- [ ] Docs mention that Node.js/npx must be available
- [ ] Docs clarify that web-search/web-reader remain remote URL-based MCP servers

## Constraints
- Keep doc note short; avoid deep installation guides

## References
- Plan: plan-update-zai-vision-mcp

