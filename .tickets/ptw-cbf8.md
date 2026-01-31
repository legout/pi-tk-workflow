---
id: ptw-cbf8
status: closed
deps: [ptw-4c5a]
links: []
created: 2026-01-29T09:15:56Z
type: feature
priority: 2
assignee: legout
tags: [irf, workflow]
---
# Add /irf-followups + --create-followups flag

Introduce a /irf-followups command that parses review.md, creates follow-up tickets via tk create, tags them as followup, and writes followups.md as a run artifact. Wire --create-followups flag to invoke it after review merge.

## Acceptance Criteria

- With --create-followups, /irf-followups runs and creates tickets for Warnings/Suggestions
- Follow-up tickets include a followup tag
- followups.md is written to {chain_dir}/followups.md
- Without the flag, no follow-up tickets are created

