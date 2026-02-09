---
id: pt-ihfv
status: closed
deps: [pt-buwk]
links: [pt-buwk, pt-oebr]
created: 2026-02-08T23:56:07Z
type: task
priority: 2
assignee: legout
external-ref: seed-remove-session-param-from-ralph
tags: [tf, backlog, component:cli, component:workflow]
---
# Remove pi --session forwarding from tf ralph start/run

## Task
Update the Ralph CLI implementation so the `pi` command invocation used by `tf ralph start` and `tf ralph run` no longer includes `--session ...`.

## Context
We want session handling to be implicit/managed by ticketflow, not manually forwarded to Pi. This should not break existing flows like resuming and artifact placement.

## Acceptance Criteria
- [ ] `tf ralph start` constructed `pi ...` command has no `--session` argument.
- [ ] `tf ralph run` constructed `pi ...` command has no `--session` argument.
- [ ] Ensure any required alternative wiring is in place (e.g., sessionDir / run dir) to preserve isolation.

## Constraints
- Avoid unrelated refactors.

## References
- Seed: seed-remove-session-param-from-ralph



## Notes

**2026-02-09T07:18:26Z**

Implementation complete: Removed --session forwarding from pi command invocation in tf ralph start/run. Session handling is now implicit/managed by ticketflow.\n\nChanges:\n- Removed session_path parameter from run_ticket()\n- Removed --session arg construction in all pi invocations\n- Removed session_dir/session_per_ticket resolution from ralph_run() and ralph_start()\n- Updated dry-run logging to not include session info\n\nAll 82 ralph tests pass, including 3 regression tests for this change.\n\nCommit: 2e75c36
