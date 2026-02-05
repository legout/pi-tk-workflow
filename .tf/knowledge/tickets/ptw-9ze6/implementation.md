# Implementation: ptw-9ze6

## Summary
Added `--dry-run` flag to `tf doctor` command that shows what `--fix` would change without actually writing files. This is useful for CI pipelines to verify VERSION file consistency without side effects.

## Files Changed
- `tf_cli/doctor_new.py` - Added --dry-run argument and logic

## Key Changes

### 1. Added `--dry-run` argument to build_parser()
```python
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Show what --fix would change without writing files",
)
```

### 2. Updated check_version_consistency() signature
- Added `dry_run: bool = False` parameter
- Updated docstring to document the new parameter

### 3. Added dry-run handling for mismatched VERSION file
When VERSION file exists but doesn't match package.json:
- If `dry_run=True`: prints `[dry-run] Would update VERSION file from X to Y`
- If `fix=True` (and not dry_run): actually updates the file

### 4. Added dry-run handling for missing VERSION file
When VERSION file doesn't exist:
- If `dry_run=True`: prints `[dry-run] Would create VERSION file with version X`
- If `fix=True` (and not dry_run): actually creates the file

### 5. Updated run_doctor() to pass dry_run flag
```python
version_ok = check_version_consistency(
    project_root, fix=args.fix, dry_run=args.dry_run
)
```

## Test Results
- Syntax check passed: `python3 -m py_compile tf_cli/doctor_new.py`
- Help shows new flag: `--dry-run  Show what --fix would change without writing files`
- Tested with mismatched VERSION file:
  - `--dry-run`: Shows `[dry-run] Would update VERSION file from v0.2.0 to 0.1.0`
  - `--fix`: Actually updates the file with `[fixed] VERSION file updated...`
- Tested with missing VERSION file:
  - `--dry-run`: Shows `[dry-run] Would create VERSION file with version 0.1.0`

## Verification
```bash
# Test help
tf new doctor --help

# Test dry-run with mismatched VERSION
echo "v0.2.0" > VERSION
tf new doctor --dry-run

# Test dry-run with missing VERSION
rm VERSION
tf new doctor --dry-run
```
