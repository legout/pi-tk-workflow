# Implementation: abc-123

## Summary
Applied Minor fix to hello-world utility test suite. Removed global sys.argv patching in CLI tests and now pass argv directly to main() function.

## Files Changed
- `tests/test_demo_hello.py` - Removed unittest.mock import and sys.argv patching. CLI tests now pass argv directly to main() function.

## Key Decisions
- Applied fix from reviewer-general feedback: CLI tests now pass argv directly to main([]) and main(["Alice"]) instead of patching sys.argv globally
- This avoids global state mutation in tests and follows the function signature more directly
- All 6 tests continue to pass

## Tests Run
```bash
pytest tests/test_demo_hello.py -v
```
Results: 6 passed
- test_hello_default
- test_hello_custom_name
- test_hello_empty_string
- test_hello_whitespace_only
- test_cli_default
- test_cli_with_name

## Quality Checks
```bash
ruff check tests/test_demo_hello.py --fix
ruff format tests/test_demo_hello.py
```
Result: All checks passed

## Verification
```bash
python -m demo           # Hello, World!
python -m demo Alice     # Hello, Alice!
```
