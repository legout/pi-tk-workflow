# Implementation: ptw-v5tg

## Summary
Added a minimal smoke test for `tf --version` that validates the version command works correctly without requiring pytest or any external test framework.

## Files Changed
- `tests/smoke_test_version.py` - New smoke test script (stdlib-only)
- `README.md` - Added "Development" section documenting how to run tests

## Key Decisions
1. **Used stdlib-only approach** - The script uses only Python standard library modules (`subprocess`, `re`, `sys`) as specified in the ticket constraints.

2. **SemVer validation** - The test validates output matches basic SemVer format (MAJOR.MINOR.PATCH with optional prerelease/build metadata) using a simple regex pattern.

3. **Executable script** - Made the script executable so it can be run directly as `./tests/smoke_test_version.py`.

4. **Documentation in README** - Added a "Development" section to the README explaining how to run both pytest tests and the smoke test.

## Tests Run
```bash
$ python tests/smoke_test_version.py
Running smoke test: tf --version
----------------------------------------
✓ Exit code is 0
✓ Output is non-empty: '0.1.0'
✓ Output matches SemVer format
----------------------------------------
All smoke tests passed!
```

## Verification
Run the smoke test locally:
```bash
python tests/smoke_test_version.py
```

Or run all tests:
```bash
pytest
python tests/smoke_test_version.py
```
