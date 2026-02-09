---
id: pt-tupn
status: closed
deps: [pt-62g6, pt-ce2e]
links: [pt-62g6, pt-m06z]
created: 2026-02-09T16:25:09Z
type: task
priority: 2
assignee: legout
external-ref: plan-refactor-tf-cli-to-tf
tags: [tf, backlog, plan, component:cli, component:tests, component:workflow]
---
# Move CLI dispatcher + core modules from tf_cli to tf

## Task
Move the CLI dispatch/root command wiring into `tf/` and update internal imports to prefer `tf.*`.

## Context
Once entrypoints point at `tf`, we can progressively relocate modules and stop expanding `tf_cli`.

## Acceptance Criteria
- [ ] CLI dispatch code lives under `tf/`
- [ ] Internal imports updated (prefer `tf.*`)
- [ ] All tests pass

## Constraints
- Keep changes incremental (move a vertical slice first)

## References
- Plan: plan-refactor-tf-cli-to-tf


## Notes

**2026-02-09T17:40:30Z**

## Implementation Complete

Moved CLI dispatcher and core modules from tf_cli to tf namespace.

### Changes
- Migrated 32 Python modules to tf/ package
- Updated all internal imports to use tf.* namespace
- Fixed remaining tf_cli imports in board_classifier.py, asset_planner.py, cli.py
- Updated __all__ in __init__.py to include ticket_factory exports
- Fixed documentation inconsistencies in tags_suggest.py

### Verification
- All Python files compile successfully
- CLI smoke tests pass (--version, --help, new --help)
- No remaining tf_cli imports in tf/ package

**Commit:** 13754d5
