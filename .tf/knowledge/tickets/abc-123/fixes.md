# Fixes: abc-123

## Summary
Applied 3 Major fixes identified in review to improve whitespace handling consistency.

## Fixes Applied

### Major Fix 1: Whitespace Stripping in hello() (demo/hello.py:39)
**Issue**: The `hello` function used the raw name without stripping leading/trailing whitespace, causing inconsistent output like `"Hello,   Alice  !"`.

**Fix**: Modified the function to strip whitespace before formatting:
```python
cleaned_name = name.strip()
if not cleaned_name:
    return "Hello, World!"
return f"Hello, {cleaned_name}!"
```

**Verification**: `hello("  Alice  ")` now returns `"Hello, Alice!"` as expected.

### Major Fix 2: Missing Whitespace Test (tests/test_demo_hello.py)
**Issue**: No test coverage for names with leading/trailing whitespace.

**Fix**: Added `test_hello_whitespace_stripped()` test:
```python
def test_hello_whitespace_stripped() -> None:
    """Test hello strips leading/trailing whitespace from names."""
    result = hello("  Alice  ")
    assert result == "Hello, Alice!"
    result = hello("\tBob\n")
    assert result == "Hello, Bob!"
```

### Major Fix 3: Missing CLI Empty String Test (tests/test_demo_hello.py)
**Issue**: CLI path with empty string argument was not tested.

**Fix**: Added `test_cli_empty_string()` test:
```python
def test_cli_empty_string(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI entry point with empty string argument."""
    result = main([""])
    assert result == 0
    captured = capsys.readouterr()
    assert "Hello, World!" in captured.out
```

## Documentation Update
Updated the docstring in `demo/hello.py` to document that leading/trailing whitespace is stripped.

## Test Results
All 8 tests passing:
- test_hello_default ✓
- test_hello_custom_name ✓
- test_hello_empty_string ✓
- test_hello_whitespace_only ✓
- test_hello_whitespace_stripped ✓ (new)
- test_cli_default ✓
- test_cli_with_name ✓
- test_cli_empty_string ✓ (new)

## Files Changed
- demo/hello.py
- tests/test_demo_hello.py
