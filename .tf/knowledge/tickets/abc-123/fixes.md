# Fixes: abc-123

## Issues Fixed

### Minor Issues (2)

1. **Import order violation** (`tests/test_demo_hello.py:13`)
   - **Problem**: `from demo.hello import hello` appeared after `pytestmark = pytest.mark.unit`
   - **Fix**: Moved import to correct position (after `import pytest`, before `pytestmark`)
   - **Rationale**: Follows PEP 8 convention where imports come after module docstring but before other module-level code

2. **CLI docstring clarity** (`demo/hello.py:35`)
   - **Problem**: Multi-word name handling in CLI not explicitly documented
   - **Fix**: No code change required - existing behavior is correct. The docstring examples show direct function calls which is appropriate.
   - **Rationale**: The docstring focuses on API usage; CLI behavior is documented in the module-level docstring under "CLI Usage"

## Verification
- All tests pass (3/3)
- No Critical or Major issues remain
- 1 Minor issue intentionally not fixed (CLI docstring is acceptable as-is)
