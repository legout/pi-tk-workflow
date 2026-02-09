# Implementation: abc-123

## Summary
Hello-world utility module for demonstrating the IRF workflow. The implementation includes a greeting function with CLI support and comprehensive test coverage.

## Files Changed
- `demo/__init__.py` - Package initialization with `hello` export
- `demo/hello.py` - Core greeting function with docstrings and type annotations
- `demo/__main__.py` - CLI entry point using argparse

## Key Decisions
- Used argparse for CLI handling (follows project conventions)
- Added empty/whitespace string handling per review feedback
- Included comprehensive docstrings with examples
- Used `from __future__ import annotations` for forward compatibility

## Tests Run
```
python3 -m pytest tests/test_demo_hello.py -v
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.2 -- /usr/bin/python3
collecting ... collected 4 items

tests/test_demo_hello.py::test_hello_default PASSED                      [ 25%]
tests/test_demo_hello.py::test_hello_custom_name PASSED                  [ 50%]
tests/test_demo_hello.py::test_hello_empty_string PASSED                 [ 75%]
tests/test_demo_hello.py::test_hello_whitespace_only PASSED              [100%]

============================== 4 passed in 0.02s ===============================
```

## Verification
- All 4 tests passing
- CLI works: `python -m demo` outputs "Hello, World!"
- CLI with args: `python -m demo Alice` outputs "Hello, Alice!"
