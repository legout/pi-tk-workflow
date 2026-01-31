---
id: ptw-ae9c
status: closed
deps: []
links: []
created: 2026-01-29T09:15:56Z
type: feature
priority: 2
assignee: legout
tags: [irf, workflow]
---
# IRF doctor command (preflight checks)

Add ./bin/irf doctor to validate tk, pi, required extensions, and checker tools before running IRF.

## Acceptance Criteria

- Running ./bin/irf doctor prints pass/fail for tk, pi, required extensions, and tools from config checkers
- Exits non-zero if required tools are missing
- No files are modified

