# Research: pt-mu0s - tf_cli Deprecation Strategy

## Status
Research enabled. Analysis of existing patterns and requirements completed.

## Context Reviewed

### Current State
- **Version**: 0.3.0 (per VERSION file)
- **Current Package**: `tf_cli` - Python package with CLI entrypoint `tf`
- **Target Package**: `tf` - New canonical namespace (not yet created)
- **Console Script**: `tf = "tf_cli.cli:main"` (in pyproject.toml)

### Existing Deprecation Patterns in Codebase

#### 1. _version.py Module
```python
"""Version information for tf_cli (deprecated, use tf_cli.version instead).

This module is kept for backward compatibility.
Prefer importing from tf_cli.version or tf_cli directly.
"""
from tf_cli.version import get_version, __version__
```
- Silent re-export (no runtime warning)
- Docstring indicates deprecation
- No env-gated warning mechanism

#### 2. cli.py Deprecation Warning
```python
"WARNING: --project is deprecated. Installing tf globally; "
```
- Simple print-based warning (not DeprecationWarning)
- User-facing message

### Existing Deprecation Policy (docs/deprecation-policy.md)

Covers:
- `scripts/tf_legacy.sh` - REMOVED
- `*_new.py` module suffix - Deprecated, removal 2026-03-15
- `tf new` command prefix - Deprecated, removal 2026-03-01

Timeline pattern observed:
- Notice period: 3 weeks
- Soft deprecation: 4 weeks (warnings active)
- Hard deprecation: removal

### Requirements from Ticket

**Acceptance Criteria:**
1. Decide how long `tf_cli` stays supported (at least one release cycle)
2. Decide warning behavior (default off vs env-gated) to avoid CI noise
3. Capture the policy in docs and link it

**Constraints:**
- Avoid emitting DeprecationWarning by default in tests

### Related Tickets
- pt-hpme: Implement tf_cli compatibility shims (depends on this ticket)
- pt-62g6: Wire packaging/entrypoints so tf console script uses tf namespace
- pt-ce2e: Introduce tf package skeleton + module entrypoint

## Analysis

### Timeline Considerations

Current version 0.3.0 suggests semantic versioning. Options:
1. **One release cycle**: Support tf_cli through 0.4.x, remove in 0.5.0
2. **Two release cycles**: Support through 0.5.x, remove in 0.6.0
3. **Time-based**: Support for N months regardless of version

Given this is a package namespace change (breaking for importers), the "at least one release cycle" suggests:
- **Recommendation**: Support through 0.4.x, removal targeted for 0.5.0

### Warning Strategy Options

| Approach | Pros | Cons |
|----------|------|------|
| Always warn | Maximum visibility | CI noise, test breakage |
| Env-gated (TF_CLI_DEPRECATION_WARN=1) | No CI noise, opt-in | Less visibility |
| Import-time check (only warn on direct tf_cli import) | Targets actual users | Implementation complexity |
| Python warnings filter compatible | Standard Python pattern | May still affect test suites |

**Recommendation**: Env-gated with sensible default (off)
- `TF_CLI_DEPRECATION_WARN=1` to enable warnings
- Silent by default to avoid CI/test disruption
- Document clearly in migration guide

### What Needs Shimming

The tf_cli package exports:
- CLI entrypoint (tf_cli.cli:main)
- Public API modules: ticket_factory, version, etc.
- Submodules: doctor, sync, init, login, ralph, etc.

Shim strategy:
- Keep tf_cli/ directory as thin re-exports
- All implementations move to tf/
- tf_cli modules do `from tf.x import *`

### Sources
- `pyproject.toml` - Package configuration
- `tf_cli/__init__.py` - Current exports
- `docs/deprecation-policy.md` - Existing policy patterns
- Plan: plan-refactor-tf-cli-to-tf
