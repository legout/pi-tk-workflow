---
id: pt-oebr
status: closed
deps: [pt-ihfv]
links: [pt-ihfv]
created: 2026-02-08T23:56:07Z
type: task
priority: 2
assignee: legout
external-ref: seed-remove-session-param-from-ralph
tags: [tf, backlog, component:cli, component:docs, component:workflow]
---
# Update tf ralph docs/help text to remove pi --session mention

## Task
Update CLI help text and docs so users are no longer instructed to use or reason about Pi `--session` when running Ralph.

## Context
After removing `--session` forwarding, documentation and help output should reflect the new, simpler UX and any remaining session semantics.

## Acceptance Criteria
- [ ] `tf ralph start --help` and `tf ralph run --help` do not mention forwarding `--session` to `pi`.
- [ ] Any docs/readmes referencing `--session` forwarding are updated.
- [ ] Provide a short note on how sessions/resume work now (if applicable).

## Constraints
- Keep docs accurate and minimal.

## References
- Seed: seed-remove-session-param-from-ralph



## Notes

**2026-02-09T07:40:14Z**

## Implementation Complete

### Changes Made
- Updated 
docs/ralph.md
: Removed  
sessionPerTicket
 from config table and clarified session behavior
- Updated 
tf_cli/ralph.py
: Removed  
sessionPerTicket
 from DEFAULTS dictionary
- Updated Session Storage section to explain automatic session handling

### Commit
75eb0c9

### Verification
- All 82 tests passed
- No  
--session
 forwarding mentioned in help text
- No  
sessionPerTicket
 references remain in codebase

### Review Summary
- Critical: 0
- Major: 0 (review issues already addressed)
- Minor: 0
