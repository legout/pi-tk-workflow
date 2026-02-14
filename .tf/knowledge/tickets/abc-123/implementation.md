# Implementation: abc-123

## Summary
Demo hello-world utility module with comprehensive Unicode handling and CLI support.

## Retry Context
- Attempt: 1
- Escalated Models: fixer=base, reviewer-second=base, worker=base

## Files Changed
- `demo/hello.py` - Core greeting function with Unicode zero-width char handling
- `demo/__main__.py` - CLI entry point with BrokenPipeError handling
- `tests/test_demo_hello.py` - Comprehensive test suite

## Key Decisions
- Used pre-compiled regex for performance (module-level)
- Handles Unicode zero-width characters (U+200B-U+200D, U+FEFF)
- Collapses internal whitespace runs to single space
- Returns proper exit code (0) from CLI
- Type validation raises descriptive TypeError

## Tests Run
- All 14 tests passing
- pytest tests/test_demo_hello.py -v

## Verification
- Import: `from demo.hello import hello`
- CLI: `python -m demo Alice`
- Tests: `python -m pytest tests/test_demo_hello.py`
