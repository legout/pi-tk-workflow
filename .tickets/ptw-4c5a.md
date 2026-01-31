---
id: ptw-4c5a
status: closed
deps: []
links: []
created: 2026-01-29T09:15:56Z
type: feature
priority: 2
assignee: legout
tags: [irf, workflow]
---
# Dynamic reviewer outputs from workflow.enableReviewers

Derive review output filenames and review-merge reads dynamically from workflow.enableReviewers without manual prompt edits.

## Acceptance Criteria

- Changing workflow.enableReviewers updates review outputs automatically
- review-merge reads match generated outputs
