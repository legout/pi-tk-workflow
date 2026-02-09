---
id: pt-hpme
status: closed
deps: [pt-62g6, pt-ce2e]
links: [pt-mu0s, pt-62g6]
created: 2026-02-09T16:25:09Z
type: task
priority: 2
assignee: legout
external-ref: plan-refactor-tf-cli-to-tf
tags: [tf, backlog, plan, component:cli, component:tests, component:workflow]
---
# Implement tf_cli compatibility shims (re-export) + optional deprecation warnings

## Task
Keep `tf_cli` import paths working by making modules thin re-exports/delegators to `tf`.

## Context
This preserves downstream imports during the migration period.

## Acceptance Criteria
- [ ] `import tf_cli` and key `tf_cli.*` imports still work
- [ ] Shims are thin (no duplicated logic)
- [ ] Deprecation warning policy matches the defined strategy

## Constraints
- Avoid warning spam in default test runs

## References
- Plan: plan-refactor-tf-cli-to-tf


## Notes

**2026-02-09T16:49:18Z**

## Completed: tf_cli Compatibility Shims

### Implementation Summary
Implemented tf_cli compatibility shims with opt-in deprecation warnings. The tf package is now canonical, and tf_cli is a thin compatibility shim.

### Key Changes
- **tf/__init__.py**: Canonical package with full version reading (repo root, git tag, fallback chain)
- **tf/cli.py**: Full CLI dispatcher (already existed, imports handlers from tf_cli during transition)
- **tf_cli/__init__.py**: Shim with opt-in deprecation warning, re-exports from tf_cli modules
- **tf_cli/cli.py**: Shim re-exporting public API only (main, can_import_tf, can_import_tf_cli)
- **tf_cli/__main__.py**: Module execution shim for 'python -m tf_cli'

### Post-Review Fixes
- Fixed version reading to match original tf_cli/version.py implementation
- Changed fallback from '0.0.0-dev' to 'unknown' for consistency
- Updated all deprecation warnings to use GitHub URL instead of local path
- Removed internal function re-exports from tf_cli/cli.py public API
- Improved exception handling specificity

### Acceptance Criteria
✅ import tf_cli and key tf_cli.* imports still work
✅ Shims are thin (no duplicated logic)
✅ Deprecation warning policy matches strategy (opt-in via TF_CLI_DEPRECATION_WARN=1)
✅ No warning spam in default test runs

### Verification
- python -m tf --version → 0.3.0
- python -m tf_cli --version → 0.3.0
- TF_CLI_DEPRECATION_WARN=1 shows warnings
- No warnings without env var (default)

### Commit
Commit: e0b8617

### Artifacts
- .tf/knowledge/tickets/pt-hpme/research.md
- .tf/knowledge/tickets/pt-hpme/implementation.md
- .tf/knowledge/tickets/pt-hpme/review.md
- .tf/knowledge/tickets/pt-hpme/fixes.md
