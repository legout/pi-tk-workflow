# Fixes: ptw-9ze6

## Critical Issues Fixed

### Issue 1: dry-run returned success on VERSION drift
**Location**: `tf_cli/doctor_new.py:277-280`

**Problem**: When `dry_run=True` and VERSION drift existed, `check_version_consistency()` returned `True` instead of `False`. This caused CI pipelines to pass incorrectly when VERSION was inconsistent.

**Fix**: Changed `return True` to `return False` in the dry-run path when VERSION mismatch is detected.

```python
# Before:
if dry_run:
    print(
        f"[dry-run] Would update VERSION file from {version_file_version} to {package_version}"
    )
    return True  # BUG: Returns success on drift

# After:
if dry_run:
    print(
        f"[dry-run] Would update VERSION file from {version_file_version} to {package_version}"
    )
    return False  # FIXED: Returns failure on drift
```

### Issue 2: dry-run returned success on missing VERSION file
**Location**: `tf_cli/doctor_new.py:288-292`

**Problem**: When `dry_run=True` and VERSION file was missing, the function returned `True` instead of `False`.

**Fix**: Changed `return True` to `return False` in the dry-run path when VERSION file is missing.

```python
# Before:
if dry_run:
    print(
        f"[dry-run] Would create VERSION file with version {package_version}"
    )
    return True  # BUG: Returns success when file missing

# After:
if dry_run:
    print(
        f"[dry-run] Would create VERSION file with version {package_version}"
    )
    return False  # FIXED: Returns failure when file missing
```

## Verification

Tested the fix with all three scenarios:

1. **VERSION matches**: Returns `True` (success)
   ```bash
   $ python3 -c "from tf_cli.doctor_new import check_version_consistency; ..."
   [ok] VERSION file matches package.json: 0.1.0
   check_version_consistency returned: True
   ```

2. **VERSION drift with --dry-run**: Returns `False` (failure)
   ```bash
   $ echo "v0.2.0" > VERSION
   $ python3 -c "from tf_cli.doctor_new import check_version_consistency; ..."
   [dry-run] Would update VERSION file from v0.2.0 to 0.1.0
   check_version_consistency returned: False
   ```

3. **Missing VERSION with --dry-run**: Returns `False` (failure)
   ```bash
   $ rm VERSION
   $ python3 -c "from tf_cli.doctor_new import check_version_consistency; ..."
   [dry-run] Would create VERSION file with version 0.1.0
   check_version_consistency returned: False
   ```

All tests pass. The `--dry-run` flag now correctly detects VERSION inconsistencies and returns failure, making it suitable for CI pipelines.
