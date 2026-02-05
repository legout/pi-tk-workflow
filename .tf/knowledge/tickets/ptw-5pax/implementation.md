# Implementation: ptw-5pax

## Summary
Added `--fix` flag to `tf doctor` command that auto-syncs the VERSION file to match package.json.

## Files Changed
- `tf_cli/doctor_new.py` - Added `--fix` flag and `sync_version_file()` function

## Key Changes

### 1. Added `--fix` argument
```python
parser.add_argument("--fix", action="store_true", help="Auto-fix VERSION file to match package.json")
```

### 2. Added `sync_version_file()` function
Creates or updates the VERSION file with the package.json version.

### 3. Updated `check_version_consistency()` function
- Added `fix` parameter (default False)
- Returns bool indicating success/failure
- When `fix=True`:
  - Creates VERSION file if missing
  - Updates VERSION file if mismatched
  - Prints `[fixed]` message on success
- When `fix=False`:
  - Shows warning with fix instructions on mismatch
  - Returns False to trigger doctor failure

### 4. Version normalization preserved
- Still handles v-prefix versions correctly (v0.1.0 == 0.1.0)
- Normalization happens before comparison
- VERSION file is written with canonical package.json version (no normalization applied to output)

## Behavior Examples

```bash
# Check only (shows warning on mismatch)
$ tf doctor
[warn] VERSION file (0.0.9) does not match package.json (0.1.0)
       To fix: run 'tf doctor --fix' or update VERSION file manually

# Auto-fix (creates or updates VERSION file)
$ tf doctor --fix
[fixed] VERSION file updated from 0.0.9 to 0.1.0

# No VERSION file exists
$ tf doctor
[info] No VERSION file found (optional)

# With --fix, creates VERSION file
$ tf doctor --fix
[fixed] VERSION file created with version 0.1.0
```

## Tests Run
- Syntax check: `python3 -m py_compile tf_cli/doctor_new.py` ✓
- Help display: `python3 -m tf_cli.doctor_new --help` ✓
- Normal check: `python3 -m tf_cli.doctor_new` ✓
- Fix mode (create): `python3 -m tf_cli.doctor_new --fix` ✓
- Fix mode (update): Tested with mismatched version ✓
- Version normalization: v0.1.0 matches 0.1.0 ✓
- Lint: `ruff check tf_cli/doctor_new.py` ✓
- Format: `ruff format tf_cli/doctor_new.py` ✓

## Verification
1. Run `tf doctor` - should show version check
2. Run `tf doctor --fix` - should create/update VERSION file
3. Check `cat VERSION` - should match package.json version