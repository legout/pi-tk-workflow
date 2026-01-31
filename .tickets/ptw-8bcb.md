---
id: ptw-8bcb
status: closed
deps: []
links: []
created: 2026-01-29T09:15:56Z
type: feature
priority: 2
assignee: legout
tags: [irf, workflow]
---
# Add summary.json artifact for IRF runs

Emit a machine-readable summary.json at an absolute path (e.g., {chain_dir}/summary.json) with ticket id, flags, review counts, files changed, tests run, and timestamps.

## Acceptance Criteria

- summary.json is created per run in {chain_dir}
- Includes ticket id, flags, review counts, files changed, tests run, and timestamps
