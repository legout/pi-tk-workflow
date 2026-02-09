---
id: pt-ce2e
status: closed
deps: [pt-mu0s, pt-k2rk]
links: [pt-k2rk, pt-7li0]
created: 2026-02-09T16:25:09Z
type: task
priority: 2
assignee: legout
external-ref: plan-refactor-tf-cli-to-tf
tags: [tf, backlog, plan, component:cli, component:config, component:workflow]
---
# Introduce tf package skeleton + module entrypoint (python -m tf)

## Task
Add a new top-level `tf/` package and make `python -m tf --help` invoke the same CLI as `tf --help`.

## Context
Aligning the import namespace with the user-facing command reduces confusion and improves embed-ability.

## Acceptance Criteria
- [ ] `tf/__init__.py` exists (minimal)
- [ ] `tf/__main__.py` exists and dispatches to the CLI
- [ ] `python -m tf --help` works locally

## Constraints
- Preserve Python >= 3.9

## References
- Plan: plan-refactor-tf-cli-to-tf


## Notes

**2026-02-09T16:39:11Z**

Implemented tf/__main__.py to enable 'python -m tf' module execution.

Changes:
- Created tf/__main__.py with proper PEP 338 module entrypoint
- Uses sys.exit(main()) for correct exit code propagation
- Verified: python -m tf --help and --version work identically to tf command

Review: 0 Critical, 0 Major, 0 Minor issues. 2 suggestions for follow-up tests/docs.

Commit: c34e189
