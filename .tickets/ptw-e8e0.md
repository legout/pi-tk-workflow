---
id: ptw-e8e0
status: closed
deps: [ptw-4c5a]
links: []
created: 2026-01-29T09:15:56Z
type: feature
priority: 2
assignee: legout
tags: [irf, workflow]
---
# Add --plan/--dry-run for IRF chain

Add --plan/--dry-run flag to /implement-review-fix-close to print resolved chain and exit without running agents.

## Acceptance Criteria

- --plan prints resolved chain steps, reviewers, and config overrides
- No agents are invoked

