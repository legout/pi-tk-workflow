---
id: pt-mu0s
status: closed
deps: []
links: [pt-hpme]
created: 2026-02-09T16:25:09Z
type: task
priority: 2
assignee: legout
external-ref: plan-refactor-tf-cli-to-tf
tags: [tf, backlog, plan, component:cli, component:config, component:docs, component:tests, component:workflow]
---
# Define tf_cli shim + deprecation strategy (timeline + warning policy)

## Task
Define how `tf_cli` remains usable during the transition (re-exports, warnings, and removal timeline).

## Context
A compatibility layer avoids breaking downstream imports while we migrate internal code to `tf.*`.

## Acceptance Criteria
- [ ] Decide how long `tf_cli` stays supported (at least one release cycle)
- [ ] Decide warning behavior (default off vs env-gated) to avoid CI noise
- [ ] Capture the policy in docs (or deprecation-policy.md) and link it

## Constraints
- Avoid emitting DeprecationWarning by default in tests

## References
- Plan: plan-refactor-tf-cli-to-tf


## Notes

**2026-02-09T16:34:31Z**

Completed: Defined tf_cli → tf deprecation strategy

**Decisions:**
- Timeline: Support tf_cli through 0.4.x, removal in 0.5.0
- Warnings: Opt-in via TF_CLI_DEPRECATION_WARN=1 (default off to avoid CI noise)
- Documentation: Updated docs/deprecation-policy.md with Section 3.4

**Commit:** ff2aee3
