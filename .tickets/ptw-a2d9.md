---
id: ptw-a2d9
status: closed
deps: [ptw-14ff]
links: []
created: 2026-01-29T09:15:56Z
type: feature
priority: 2
assignee: legout
tags: [irf, workflow]
---
# Add quality gate step + quality.md artifact

Add optional quality gate step that runs checkers/tests and writes quality.md at an absolute path (e.g., {chain_dir}/quality.md).

## Acceptance Criteria

- When enabled, quality.md is written with commands + results
- Runs after fixer (if invoked) or after review merge when fixer is skipped
- When disabled, no quality.md is produced and no quality commands run

