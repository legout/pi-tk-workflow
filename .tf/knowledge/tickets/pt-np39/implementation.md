# Implementation: pt-np39

## Summary
Renamed all transitional `*_new.py` modules to stable names and updated all references in imports, tests, and CLI dispatch.

## Files Changed

### Source Files (13 renamed in `tf_cli/`)
- `agentsmd_new.py` → `agentsmd.py`
- `backlog_ls_new.py` → `backlog_ls.py`
- `doctor_new.py` → `doctor.py`
- `init_new.py` → `init.py`
- `login_new.py` → `login.py`
- `next_new.py` → `next.py`
- `priority_reclassify_new.py` → `priority_reclassify.py`
- `ralph_new.py` → `ralph.py`
- `setup_new.py` → `setup.py`
- `sync_new.py` → `sync.py`
- `tags_suggest_new.py` → `tags_suggest.py`
- `track_new.py` → `track.py`
- `update_new.py` → `update.py`

### Test Files (5 renamed in `tests/`)
- `test_init_new.py` → `test_init.py`
- `test_next_new.py` → `test_next.py`
- `test_sync_new.py` → `test_sync.py`
- `test_track_new.py` → `test_track.py`
- `test_update_new.py` → `test_update.py`

### Updated References
- `tf_cli/cli.py` - Updated 16 import statements to use stable module names
- `tests/test_*.py` - Updated all import references and docstrings

## Key Decisions
- Used `sed` for bulk replacement of imports in test files to ensure consistency
- Preserved runtime behavior - all CLI commands remain functional
- Module docstrings updated to reflect new names

## Tests Run
```bash
python -m pytest tests/test_track.py tests/test_update.py tests/test_init.py tests/test_next.py tests/test_sync.py -v
```
Result: **72 passed**

## Verification
- CLI loads without import errors: `python -m tf_cli.cli --version` → `0.1.0`
- No remaining `*_new.py` files in repository (excluding worktrees)
- No remaining `_new` import references in codebase
