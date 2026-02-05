# Fixes: ptw-nw3d

## Summary
Fixed all Critical and Major issues identified in the review.

## Fixes Applied

### 1. Critical: Test File Import Paths (tests/test_cli_version.py)
**Issue**: Tests imported `get_version` from `tf_cli.cli` but the function was moved to `tf_cli.version`. Mocks targeted wrong module paths.

**Fix**: Updated test file to:
- Import `get_version` from `tf_cli.version` instead of `tf_cli.cli`
- Updated mock paths from `tf_cli.cli.resolve_repo_root` to `tf_cli.version._resolve_repo_root`
- Kept `main` import from `tf_cli.cli` (correct location)

### 2. Major: Docstring Fallback Order Mismatch (tf_cli/version.py)
**Issue**: Module docstring documented 3 fallbacks but code had 4 (missing cwd fallback).

**Fix**: Updated docstring to document all 4 fallbacks:
```
Fallback order:
1. VERSION file in git repo root (for development/git checkouts)
2. VERSION file relative to this module (for pip/uvx installs)
3. VERSION file in current working directory (edge case)
4. "unknown" (if VERSION cannot be found)
```

### 3. Major: _resolve_repo_root() Search From CWD (tf_cli/version.py)
**Issue**: `_resolve_repo_root()` searched from `Path.cwd()` which could incorrectly find a different project's version if run from within another ticketflow-based project.

**Fix**: Changed search to start from module location:
- Changed `cwd = Path.cwd()` to `module_dir = Path(__file__).resolve().parent`
- Updated docstring to explain this behavior
- This ensures we always find the correct project's version regardless of where the CLI is executed from

### 4. Minor: Exception Handling Simplification (tf_cli/version.py)
**Issue**: `except (OSError, IOError)` is redundant since IOError is an alias for OSError in Python 3.3+.

**Fix**: Simplified to just `except OSError:`.

## Verification

All import paths verified to work:
```python
from tf_cli.version import get_version    # ✓
from tf_cli import get_version            # ✓
from tf_cli._version import get_version   # ✓ (backward compat)
from tf_cli.cli import get_version        # ✓
```

Version correctly returned from different directories:
```bash
# From repo root: 0.1.0 ✓
# From /tmp: 0.1.0 ✓
# new_cli.py --version: 0.1.0 ✓
```

## Files Modified
- `tests/test_cli_version.py` - Fixed imports and mock paths
- `tf_cli/version.py` - Fixed docstring, search logic, and exception handling

## Notes
Minor issues not fixed (low priority):
- Deprecation warning in `_version.py` (comment-based deprecation is acceptable for now)
- `-V` flag inconsistency between cli.py and new_cli.py (both support `--version` and `-v`)
- Comment accuracy for cwd fallback (updated in docstring, inline comment is acceptable)
