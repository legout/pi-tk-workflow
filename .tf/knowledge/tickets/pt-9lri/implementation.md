# Implementation: pt-9lri

## Summary
Added comprehensive unit tests for the `calculate_timeout_backoff()` function in `tests/test_utils.py`. The tests cover iteration index semantics, cap behavior, and custom increment overrides.

## Retry Context
- Attempt: 1

## Files Changed
- `tests/test_utils.py` - Added `TestCalculateTimeoutBackoff` class with 17 test methods

## Test Coverage

### Iteration Index Semantics (3 tests)
- `test_iteration_index_zero_returns_base` - iteration_index=0 returns base only
- `test_iteration_index_one_adds_single_increment` - iteration_index=1 adds one increment
- `test_iteration_index_two_adds_two_increments` - verifies linear progression

### Cap Behavior (5 tests)
- `test_cap_applied_when_effective_exceeds_max` - cap applied when effective > max
- `test_cap_not_applied_when_effective_below_max` - no cap when effective < max
- `test_cap_exactly_at_max` - edge case when effective equals max
- `test_cap_with_max_equal_to_base` - full cap scenario
- `test_no_cap_when_max_ms_is_none` - unbounded growth when no cap

### Non-Default Increment Override (2 tests)
- `test_non_default_increment_override` - custom increment value
- `test_zero_increment_constant_timeout` - zero increment = constant timeout

### Additional Edge Cases (7 tests)
- `test_large_iteration_index` - high iteration numbers
- `test_zero_base_timeout_is_valid` - zero base timeout
- `test_negative_base_ms_raises` - input validation
- `test_negative_increment_ms_raises` - input validation
- `test_negative_iteration_index_raises` - input validation
- `test_max_ms_less_than_base_raises` - input validation
- `test_default_increment_constant_value` - verifies DEFAULT_TIMEOUT_INCREMENT_MS = 150000

## Tests Run
- `python -m pytest tests/test_utils.py::TestCalculateTimeoutBackoff -v` - 17 PASSED

## Verification
```python
# Import test
from tf.utils import calculate_timeout_backoff, DEFAULT_TIMEOUT_INCREMENT_MS

# Basic functionality tests
assert calculate_timeout_backoff(60000, 150000, 0) == 60000
assert calculate_timeout_backoff(60000, 150000, 1) == 210000
assert calculate_timeout_backoff(60000, 150000, 2, max_ms=300000) == 300000
```

## Acceptance Criteria Status
- [x] Tests cover iteration_index=0 and iteration_index=1 semantics
- [x] Tests cover cap behavior (max_timeout_ms)
- [x] Tests cover non-default increment override
- [x] Tests are fast and hermetic (no I/O, no external dependencies)
