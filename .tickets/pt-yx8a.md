---
id: pt-yx8a
status: closed
deps: []
links: [pt-d68t]
created: 2026-02-09T00:26:44Z
type: task
priority: 2
assignee: legout
external-ref: seed-add-timestamps-to-the-progressbar-when-r
tags: [tf, backlog, component:config, component:docs, component:workflow]
---
# Define timestamp format and placement for Ralph --progress output

## Task
Decide and document the timestamp format and when/where it appears in `tf ralph --progress` output.

## Context
We want progress lines to include a timestamp so users can correlate progress updates with real time during long Ralph runs.

## Acceptance Criteria
- [ ] Decide timestamp format (MVP recommendation: local `HH:MM:SS`).
- [ ] Decide placement (prefix before `[i/total]`) and whether it applies to start + completion lines.
- [ ] Confirm behavior in TTY (in-place) vs non-TTY (newline) output.

## Constraints
- Minimal config surface for MVP (hardcode a sensible format).

## References
- Seed: seed-add-timestamps-to-the-progressbar-when-r



## Notes

**2026-02-09T07:57:40Z**

Decision complete: Timestamp format defined as HH:MM:SS (local time), placed before [i/total] counter, applied to both start and completion lines. Specification documented in .tf/knowledge/tickets/pt-yx8a/implementation.md - unblocks pt-d68t for implementation.
