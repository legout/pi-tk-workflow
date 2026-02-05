# Research: ptw-nw3d

## Status
Research enabled. No additional external research was performed - existing codebase analysis is sufficient.

## Context Reviewed

### Existing Version Handling
1. **`tf_cli/_version.py`** - Has `__version__` that reads from VERSION file at module load time
2. **`tf_cli/cli.py`** - Has its own `get_version()` function (lines 14-27) that reads from VERSION file with fallback logic
3. **`tf_cli/__init__.py`** - Exports `__version__` from `_version.py`

### Current Version Sources
- `VERSION` file in repo root (canonical source, plain text: "0.1.0")
- `pyproject.toml` - Uses dynamic version from VERSION file
- `package.json` - Currently hardcoded (mentioned in VERSIONING.md as needing manual sync)

### Current --version Handling
- `cli.py` lines 427-428 handle `--version` and `-v` flags before other commands
- Prints result of `get_version()` which returns "unknown" if VERSION file not found

### Install Modes to Support
1. **Git checkout** - VERSION file at repo root, `tf_cli` is a subdirectory
2. **pip install** - VERSION file included via package data, located relative to installed module
3. **uvx install** - Same as pip install (pulls from git and installs)

## Key Findings
1. There's duplicated logic between `_version.py` and `cli.py`'s `get_version()`
2. `_version.py` uses static module-level `__version__` loaded at import time
3. `cli.py`'s `get_version()` has more robust fallback logic using `resolve_repo_root()`
4. Need to consolidate to a single `get_version()` in `tf_cli/version.py`

## Implementation Approach
1. Create `tf_cli/version.py` with centralized `get_version()` function
2. Handle both install modes:
   - Look for VERSION relative to package (for pip/uvx installs)
   - Look for VERSION in git repo root via resolve_repo_root() (for git checkouts)
3. Update `__init__.py` to export `get_version`
4. Update `_version.py` to import from new module
5. Update `cli.py` to import from new module
6. Document fallback order and behavior

## References
- Seed topic: `.tf/knowledge/topics/seed-add-versioning/`
- VERSIONING.md - Documents version source of truth
- Ticket: ptw-nw3d
