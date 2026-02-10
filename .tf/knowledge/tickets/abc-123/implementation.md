# Implementation: abc-123

## Summary
Demo hello-world utility for IRF workflow testing. The implementation provides a simple greeting function with CLI support.

## Files Changed
- `demo/__init__.py` - Package marker
- `demo/hello.py` - Main greeting function with docstring, type hints, and edge case handling
- `demo/__main__.py` - CLI entry point using argparse
- `tests/test_demo_hello.py` - 6 unit tests covering default, custom names, whitespace handling, and CLI

## Key Decisions
- Used `argparse` for CLI (project convention)
- Added whitespace/empty string handling to fall back to "World"
- Comprehensive docstrings with examples
- Type hints throughout for consistency

## Tests Run
```bash
python -m pytest tests/test_demo_hello.py -v
# 6 passed
```

## Verification
```bash
python -m demo              # Hello, World!
python -m demo "Test User"  # Hello, Test User!
```
