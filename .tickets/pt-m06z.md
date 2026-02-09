---
id: pt-m06z
status: closed
deps: [pt-hpme, pt-tupn]
links: [pt-tupn, pt-k2rk]
created: 2026-02-09T16:25:09Z
type: task
priority: 2
assignee: legout
external-ref: plan-refactor-tf-cli-to-tf
tags: [tf, backlog, plan, component:cli, component:tests, component:workflow]
---
# Update tests to use tf namespace + add regression test for tf_cli shim

## Task
Update the test suite to primarily import from `tf.*` and add coverage ensuring the `tf_cli` shim continues to function.

## Context
Tests should validate the new canonical namespace while ensuring the transition remains safe.

## Acceptance Criteria
- [ ] Tests updated to import from `tf.*` where appropriate
- [ ] Add at least one test that imports `tf_cli` (shim) successfully
- [ ] CI passes

## Constraints
- Keep tests stable across Python versions supported (>= 3.9)

## References
- Plan: plan-refactor-tf-cli-to-tf


## Notes

**2026-02-09T18:20:17Z**

## Implementation Complete

Updated test suite to primarily import from tf.* namespace.

### Changes
- Migrated 24 test files to import from tf.* where appropriate
- Fixed 18 critical mock.patch() path mismatches
- Fixed 2 major docstring inconsistencies
- Preserved test_tf_cli_shim.py (regression tests for shim)
- Preserved test_version.py and test_workflow_status.py (unmigrated modules)

### Key Fix: Mock Path Mismatches
When using 'from tf import X', mock.patch must use 'tf.X.function' not 'tf_cli.X.function'.

**Commit:** 24d8327
