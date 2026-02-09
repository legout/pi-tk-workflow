---
id: pt-epyf
status: closed
deps: [pt-qmor]
links: [pt-qmor]
created: 2026-02-09T00:26:44Z
type: task
priority: 2
assignee: legout
external-ref: seed-add-timestamps-to-the-progressbar-when-r
tags: [tf, backlog, component:docs, component:workflow]
---
# Update docs/help text for timestamped progress output (if documented)

## Task
Update any user-facing docs/help that describe `tf ralph --progress` output to mention timestamps (if applicable).

## Context
If we document progress output, it should reflect the new timestamp prefix so users understand the new format.

## Acceptance Criteria
- [ ] `tf ralph ... --help` (or docs) mention the timestamp prefix if they describe progress output.
- [ ] No stale examples remain showing the old format.

## References
- Seed: seed-add-timestamps-to-the-progressbar-when-r



## Notes

**2026-02-09T08:13:35Z**

Updated help text in tf_cli/ralph.py usage() function to document the HH:MM:SS timestamp prefix for --progress output. Added example output lines showing both Processing and complete states. All tests pass. Commit: ea59234
