# Fixes: abc-123

## Fixes Applied

### 1. CLI Argument Handling (Minor)
**File:** `demo/hello.py:40`
**Change:** Modified to join all remaining arguments instead of just taking `sys.argv[1]`
- Before: `name = sys.argv[1] if len(sys.argv) > 1 else "World"`
- After: `name = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "World"`

This allows multi-word names like `python -m demo.hello Alice Smith` to work correctly.

### 2. Missing pytestmark (Minor)
**File:** `tests/test_demo_hello.py:8`
**Change:** Added `pytestmark = pytest.mark.unit` to follow project testing conventions
- Added import `import pytest`
- Added marker `pytestmark = pytest.mark.unit`

## Fixes NOT Applied (by design)

### Empty String Test (Minor)
- **Rationale:** The test documents current behavior. Empty string handling is a design decision - returning `"Hello, !"` is valid behavior for this simple utility.

### Warning: CLI Argument Parsing
- **Rationale:** Using `argparse` would be overkill for this demo utility. The current implementation is sufficient for the scope.

### Suggestions (follow-up tickets)
- Input validation (strip whitespace, reject None)
- CLI entry point test using subprocess/capsys
- Additional edge case tests (None, whitespace, Unicode)
- Module docstring with ticket ID

## Verification
- All 3 tests passing
- Syntax validation passed
- pytest marker recognized
