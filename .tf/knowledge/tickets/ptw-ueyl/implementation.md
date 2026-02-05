# Implementation: ptw-ueyl

## Summary
Implemented `tf --version` (and `-V`) support across all CLI entry points.

## Changes Made

### 1. tf_cli/cli.py
- Extended version flag handling to include `-V` (capital V)
- Changed from `("--version", "-v")` to `("--version", "-v", "-V")`
- Updated comment to reflect all three flag variants

### 2. scripts/tf_legacy.sh
- Added `get_tf_version()` helper function to read VERSION file
- Added early argument parsing to handle `--version`, `-v`, `-V` before main command routing
- Updated usage documentation to include version flags

### 3. tests/test_cli_version.py
- Added `test_V_flag_prints_version()` test case for `-V` flag

## Files Changed
- `tf_cli/cli.py` - Added `-V` flag support
- `scripts/tf_legacy.sh` - Added version flag support and documentation
- `tests/test_cli_version.py` - Added test for `-V` flag

## Verification

All version flags now work correctly:

```bash
$ python3 -m tf_cli.cli --version
0.1.0

$ python3 -m tf_cli.cli -v
0.1.0

$ python3 -m tf_cli.cli -V
0.1.0

$ bash scripts/tf_legacy.sh --version
0.1.0

$ bash scripts/tf_legacy.sh -v
0.1.0

$ bash scripts/tf_legacy.sh -V
0.1.0
```

All 9 tests in `tests/test_cli_version.py` pass.

## Acceptance Criteria
- [x] `tf --version` prints just the version (e.g., `0.1.0`) and exits 0
- [x] `tf -V` works and is documented in usage/help output
- [x] No breaking changes to existing command behavior
