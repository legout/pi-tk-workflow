---
id: ptw-120f
status: closed
deps: [ptw-4c5a]
links: []
created: 2026-01-29T09:15:56Z
type: feature
priority: 2
assignee: legout
tags: [irf, workflow]
---
# Add workflow.failOn severity gate

Support workflow.failOn in config to stop the chain before closer when specified severities exist.

## Acceptance Criteria

- workflow.failOn accepts list of severities
- If matching issues exist, chain stops before closer and exits non-zero
- Clear blocking message is shown

