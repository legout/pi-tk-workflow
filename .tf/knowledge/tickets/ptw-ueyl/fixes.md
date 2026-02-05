# Fixes: ptw-ueyl

## Issues Fixed

### Minor Fix 1: Trailing Newline in Shell Script Output
**Issue**: The `get_tf_version()` function strips newlines with `tr -d '\n\r'`, causing version output to lack a trailing newline, differing from standard CLI convention and the Python implementation.

**Fix**: Modified the version flag handling in `scripts/tf_legacy.sh` to use `echo "$(get_tf_version)"` instead of just `get_tf_version`, ensuring a trailing newline is added.

**Before**:
```bash
--version|-v|-V)
  get_tf_version
  exit 0
```

**After**:
```bash
--version|-v|-V)
  echo "$(get_tf_version)"
  exit 0
```

**Verification**:
```bash
$ bash scripts/tf_legacy.sh --version | xxd
00000000: 302e 312e 300a                           0.1.0.
# Trailing newline (0a) now present
```

### Minor Fix 2: Added Comment for Early Version Flag Parsing
**Issue**: Early version flag parsing happens before environment validation, which could be confusing without explanation.

**Fix**: Added comment explaining this is intentional behavior:
```bash
# This early exit is intentional: version flags should work even if repo is misconfigured
```

## Issues Not Fixed (by design)

### Minor: get_tf_version() relies on $ROOT_DIR
**Rationale**: This is a known limitation of the shell script approach. The script is designed to be run from the repo or installed via the proper install mechanism. A more robust fix would require significant refactoring and is out of scope for this ticket.

## Verification
- All 9 tests in `tests/test_cli_version.py` pass
- Manual testing confirms all three flags (`--version`, `-v`, `-V`) work in both Python CLI and shell script
- Shell script output now includes trailing newline
