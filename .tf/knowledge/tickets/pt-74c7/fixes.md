# Fixes: pt-74c7

## Issues Fixed

### Major: Fixed unconventional datetime usage (kb_cli.py:240)
**Before:**
```python
timestamp = __import__('datetime').datetime.now().isoformat()
```

**After:**
```python
timestamp = datetime.datetime.now().isoformat()
```

**Rationale:** The `datetime` module was already imported at the top of the file. Using `__import__()` is unconventional and unnecessary when the module is already available.

### Minor: Fixed archive_md variable reference
**Before:**
The `archive_md` variable was removed during the datetime fix, causing a NameError.

**After:**
Re-added `archive_md = archive_dir / "archive.md"` before using it.

## Tests Re-run
- All 33 existing `test_kb_helpers.py` tests pass
- Manual verification of archive/restore commands successful
