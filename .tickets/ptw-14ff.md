---
id: ptw-14ff
status: closed
deps: []
links: []
created: 2026-01-29T09:15:56Z
type: feature
priority: 2
assignee: legout
tags: [irf, workflow]
---
# IRF session-scoped files_changed tracking helper

Add ./bin/irf track <path> to append de-duplicated paths to a per-run files_changed.txt at an absolute path (e.g., {chain_dir}/files_changed.txt). Update agents to call this after each edit/write.

## Acceptance Criteria

- files_changed.txt is written per run to {chain_dir}/files_changed.txt
- No git diff is used
- Helper de-duplicates entries
- Parallel runs do not contaminate each other

