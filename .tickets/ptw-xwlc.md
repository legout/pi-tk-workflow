---
id: ptw-xwlc
status: open
deps: []
links: []
created: 2026-02-05T14:00:22Z
type: task
priority: 2
assignee: legout
external-ref: seed-backlog-deps-and-tags
tags: [tf, backlog]
---
# Update tf-backlog to apply component tags by default

## Task
Update the /tf-backlog workflow to automatically assign `component:*` tags to newly created tickets.

## Context
Ralph parallel processing and backlog filtering rely on consistent component tags. Today tags are added only via manual follow-ups (e.g., /tf-tags-suggest).

## Acceptance Criteria
- [ ] /tf-backlog assigns at least one `component:*` tag to each created ticket when it can infer one.
- [ ] Tickets without a confident component are left untagged (no random tagging).
- [ ] Behavior is documented, including how to re-run tagging via /tf-tags-suggest.

## Constraints
- Must not break existing /tf-backlog behavior.

## References
- Seed: seed-backlog-deps-and-tags

