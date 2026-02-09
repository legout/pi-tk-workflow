---
id: pt-7li0
status: closed
deps: [pt-hpme, pt-tupn]
links: [pt-ce2e]
created: 2026-02-09T16:25:09Z
type: task
priority: 2
assignee: legout
external-ref: plan-refactor-tf-cli-to-tf
tags: [tf, backlog, plan, component:cli, component:docs, component:workflow]
---
# Update docs: canonical namespace is tf (migration notes + deprecation timeline)

## Task
Update README/docs to describe `tf` as the canonical Python namespace and document migration steps from `tf_cli`.

## Context
Users need clear guidance: what changed, how to update imports, and when `tf_cli` will be removed.

## Acceptance Criteria
- [ ] README/docs reference `tf` for module usage
- [ ] Document `tf_cli` shim and deprecation timeline
- [ ] Add changelog/release note entry if applicable

## Constraints
- Keep docs concise and actionable

## References
- Plan: plan-refactor-tf-cli-to-tf


## Notes

**2026-02-09T17:57:25Z**

Documentation updated for tf namespace migration.

Changes:
- Added migration notice banner to README.md
- Added dedicated 'Migrating from tf_cli to tf' section with:
  - Timeline table (Current 0.4.x → Deprecation → Removal 0.5.0)
  - Before/after import examples
  - Deprecation warning instructions
  - Module execution examples
- Updated Project Structure to show tf/ as canonical, tf_cli/ as deprecated shim
- Fixed Web Mode example to use python -m tf.ui
- Added CHANGELOG entry under [Unreleased] > Deprecated

All acceptance criteria met:
✅ README/docs reference tf for module usage
✅ tf_cli shim and deprecation timeline documented
✅ Changelog/release note entry added

Commit: 3749706caf7de76766ddcde649c034eee9a659fa
Review: 0 Critical, 0 Major, 1 Minor, 3 Warnings, 5 Suggestions
