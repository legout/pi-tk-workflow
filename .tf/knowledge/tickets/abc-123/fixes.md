# Fixes: abc-123

## Applied Fixes

### Minor Fixes
- `tests/test_demo_hello.py` - **Test pattern improvement**: Removed global `sys.argv` patching and `unittest.mock` import. CLI tests now pass argv directly to `main()` function:
  - `test_cli_default`: Changed from patching `sys.argv` to calling `main([])`
  - `test_cli_with_name`: Changed from patching `sys.argv` to calling `main(["Alice"])`
  - This avoids global state mutation and follows the function signature directly

## Remaining Minor Issues (Intentionally Not Fixed)
None - all Minor issues have been addressed.

## Tests After Fixes
All 6 tests passing:
```
tests/test_demo_hello.py::test_hello_default PASSED
tests/test_demo_hello.py::test_hello_custom_name PASSED
tests/test_demo_hello.py::test_hello_empty_string PASSED
tests/test_demo_hello.py::test_hello_whitespace_only PASSED
tests/test_demo_hello.py::test_cli_default PASSED
tests/test_demo_hello.py::test_cli_with_name PASSED
```
