---
id: pt-7mvl
status: closed
deps: []
links: [pt-buwk]
created: 2026-02-08T23:56:07Z
type: task
priority: 2
assignee: legout
external-ref: seed-remove-session-param-from-ralph
tags: [tf, backlog, component:cli, component:docs, component:workflow]
---
# Define Ralph session behavior without forwarding pi --session

## Task
Document and decide the intended behavior of `tf ralph start/run` after removing the forwarded `--session` argument to `pi`.

## Context
Today `tf ralph start` and `tf ralph run` pass `--session <...>` through to `pi`. We want to remove that parameter while preserving resumability and isolation.

## Acceptance Criteria
- [ ] Identify where `--session` is currently coming from and what it affects (artifacts, resume behavior, isolation).
- [ ] Define the new behavior when no `--session` is forwarded (what becomes the source of truth for session selection).
- [ ] Capture any backward-compat constraints (e.g., whether `tf ralph ... --session` is still accepted but not forwarded).

## Constraints
- Keep behavior change minimal besides removing the forwarded parameter.

## References
- Seed: seed-remove-session-param-from-ralph



## Notes

**2026-02-09T00:14:57Z**

## Completed: Define Ralph session behavior without forwarding pi --session

### Decision
Remove --session forwarding entirely. Pi's internal session management becomes the source of truth.

### Key Points
1. **Current state**: --session is constructed in run_ticket() (line ~417) and parallel mode (line ~1758)
2. **New behavior**: Ralph delegates session management entirely to Pi
3. **Backward compat**: sessionDir and sessionPerTicket config options become no-ops (deprecated)

### Implementation Guidance for Dependent Tickets
- **pt-buwk**: Test that pi is invoked without --session argument
- **pt-ihfv**: Remove args += ["--session", str(session_path)] from both locations; add deprecation warnings
- **pt-oebr**: Remove session-related documentation

### Artifacts
- .tf/knowledge/tickets/pt-7mvl/implementation.md (decision document)
- .tf/knowledge/tickets/pt-7mvl/research.md (analysis)
- .tf/knowledge/tickets/pt-7mvl/review.md (consolidated review)

Commit: 7e99250
