# Research: pt-7li0

## Status
Research completed. No external research needed - this is a documentation task based on existing codebase state.

## Context Reviewed

### Current State
- `tf/` package exists with canonical implementation (created in pt-ce2e, pt-tupn)
- `tf_cli/` package now serves as a compatibility shim (pt-hpme)
- `tf_cli/__init__.py` has deprecation warning (opt-in via TF_CLI_DEPRECATION_WARN=1)
- `tf/__init__.py` documents the migration status

### Key Files
- `README.md` - Main documentation still references `tf_cli` extensively
- `CHANGELOG.md` - No entry for namespace migration yet
- `docs/deprecation-policy.md` - Comprehensive policy exists but not prominently linked

### Migration Progress (from ticket deps)
- pt-ce2e [closed]: Introduced tf package skeleton
- pt-hpme: Version reading logic moved to tf/
- pt-tupn: CLI dispatch code moved to tf/

## What Needs Documentation

1. **README updates**:
   - Installation instructions should reference `tf` package
   - Python import examples should use `tf.` not `tf_cli.`
   - Development section needs import path updates
   - Add prominent migration notice

2. **CHANGELOG entry**:
   - Add "Deprecated" section entry for tf_cli namespace
   - Reference the migration guide

3. **Cross-references**:
   - Link to docs/deprecation-policy.md for full details

## Sources
- `tf/__init__.py` - Current canonical package
- `tf_cli/__init__.py` - Shim implementation
- `docs/deprecation-policy.md` - Section 3.4
- `README.md` - Current state requiring updates
- `CHANGELOG.md` - Needs new entry
