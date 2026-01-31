---
id: ptw-40ab
status: closed
deps: [ptw-4c5a]
links: []
created: 2026-01-29T09:15:56Z
type: feature
priority: 2
assignee: legout
tags: [irf, workflow]
---
# Skip fixer when no actionable issues

If review merge yields zero Critical/Major/Minor issues, skip the fixer step and write a fixes.md stub stating no fixes needed.

## Acceptance Criteria

- Fixer is not invoked when Critical/Major/Minor counts are zero
- fixes.md stub is still written with "No fixes needed"

