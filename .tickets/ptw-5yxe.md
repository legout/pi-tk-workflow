---
id: ptw-5yxe
status: closed
deps: []
links: []
created: 2026-02-05T14:00:22Z
type: task
priority: 2
assignee: legout
external-ref: seed-backlog-deps-and-tags
tags: [tf, backlog]
---
# Document fallback workflow using tf-deps-sync and tf-tags-suggest

## Task
Update docs to clearly describe the fallback workflow when /tf-backlog inference is incomplete.

## Context
We already have /tf-deps-sync and /tf-tags-suggest as manual correction tools. Users should know when to run them and what to expect.

## Acceptance Criteria
- [ ] Docs describe typical sequence: /tf-backlog -> (optional) /tf-tags-suggest --apply -> (optional) /tf-deps-sync --apply.
- [ ] Mention manual linking via `tk link`.
- [ ] Guidance is short and actionable.

## Constraints
- Documentation should match actual behavior.

## References
- Seed: seed-backlog-deps-and-tags


## Notes

**2026-02-05T14:20:34Z**

## Implementation Complete

Updated documentation to describe the fallback workflow when /tf-backlog inference is incomplete.

### Changes
- **docs/workflows.md**: Added Step 6 to Greenfield Development workflow documenting the fallback sequence
- **docs/commands.md**: Added fallback note to /tf-backlog, plus full documentation for /tf-tags-suggest and /tf-deps-sync

### Acceptance Criteria
- ✅ Typical sequence documented: /tf-backlog → /tf-tags-suggest --apply → /tf-deps-sync --apply
- ✅ Manual linking via tk link mentioned
- ✅ Short and actionable guidance
- ✅ Documentation matches actual behavior

### Review
- Critical: 0, Major: 0, Minor: 0
- No fixes required

### Commit
8ef419f538b3bf92a218a068021ce824d6755068
