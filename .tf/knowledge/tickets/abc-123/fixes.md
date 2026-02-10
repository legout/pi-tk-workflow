# Fixes: abc-123

## Summary
Fixed 3 Major issues identified in review regarding type safety and None handling.

## Fixes Applied

### Major Issue 1: None handling
- **File**: `demo/hello.py`
- **Fix**: Added explicit None check with descriptive TypeError
- **Code**: `if name is None: raise TypeError("name must be a string, not None")`

### Major Issue 2: Non-string type handling
- **File**: `demo/hello.py`
- **Fix**: Added isinstance check with descriptive TypeError showing actual type
- **Code**: `if not isinstance(name, str): raise TypeError(f"name must be a string, got {type(name).__name__}")`

### Major Issue 3: Missing test coverage
- **File**: `tests/test_demo_hello.py`
- **Fix**: Added 2 new tests:
  - `test_hello_none_raises()` - Verifies TypeError for None input
  - `test_hello_non_string_raises()` - Verifies TypeError for int and list inputs

### Additional Improvements
- **File**: `demo/hello.py`
- **Fix**: Added `__all__ = ["hello"]` to explicitly control public API (Suggestion from reviewer-general)
- **Docstring**: Updated function docstring to document the new `Raises` section

## Test Results
```
python -m pytest tests/test_demo_hello.py -v
==============================
10 passed in 0.08s
```

## Files Changed
- `demo/hello.py` - Added type validation and __all__ export
- `tests/test_demo_hello.py` - Added 2 type validation tests
