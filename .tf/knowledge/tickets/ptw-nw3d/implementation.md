# Implementation: ptw-nw3d

## Summary
Created a centralized version retrieval helper (`tf_cli/version.py`) that works across all installation modes (git checkout, pip install, uvx install).

## Files Changed

### 1. `tf_cli/version.py` (NEW)
- Centralized `get_version()` function with comprehensive docstring
- Supports all install modes:
  - Git checkout: Finds VERSION via repo root detection
  - Pip/uvx install: Finds VERSION relative to installed package
- Fallback order clearly documented in module docstring
- Private helper functions: `_resolve_repo_root()`, `_read_version_file()`
- Exports both `get_version()` function and `__version__` constant

### 2. `tf_cli/__init__.py`
- Updated to export `get_version` from new `version` module
- Maintains backward compatibility with `__version__`

### 3. `tf_cli/_version.py`
- Refactored to import from new `version` module
- Maintains backward compatibility for existing imports
- Added deprecation note directing users to `tf_cli.version`

### 4. `tf_cli/cli.py`
- Removed local `get_version()` function (was duplicating logic)
- Added import: `from tf_cli.version import get_version`
- `--version` and `-v` flags continue to work as before

### 5. `tf_cli/new_cli.py`
- Added import: `from .version import get_version`
- Added `--version`, `-v`, `-V` flag handling in `main()`
- Now supports version output consistently with main CLI

## Key Decisions

1. **Centralized in version.py**: Consolidated all version logic to a single module with clear documentation
2. **Function + constant**: Provided both `get_version()` (dynamic) and `__version__` (cached) for flexibility
3. **Fallback order**:
   1. VERSION in git repo root (development mode)
   2. VERSION relative to module (installed package)
   3. VERSION in current directory (edge case)
   4. "unknown" (if all fail)
4. **Backward compatibility**: `_version.py` kept as a thin wrapper to avoid breaking existing imports

## Tests Run

```python
# All scenarios verified:
- get_version() from repo: "0.1.0" ✓
- get_version() from temp dir: "0.1.0" ✓
- __version__ constant: "0.1.0" ✓
- Import from tf_cli: works ✓
- Import from tf_cli.version: works ✓
- Import from tf_cli._version: works (backward compat) ✓
- cli.py get_version: works ✓
- new_cli.py --version: works ✓
```

## Verification

```bash
# Test version retrieval
python -c "from tf_cli.version import get_version; print(get_version())"
# Output: 0.1.0

# Test CLI --version (legacy cli.py)
tf --version
# Output: 0.1.0

# Test new CLI --version
python -m tf_cli new --version
# Output: 0.1.0
```

## Documentation

The `version.py` module includes:
- Comprehensive module docstring explaining supported install modes
- Clear fallback order documentation
- Docstring for `get_version()` with example usage
- Type hints throughout
