# Timeout Backoff Specification

**Ticket**: pt-xwjw  
**Status**: Draft → Ready for Implementation  
**Related**: pt-bcu8 (implementation ticket)

---

## 1. Iteration Index Semantics

### 1.1 Definition
The **iteration index** is a zero-based integer representing the current attempt number.

| Attempt | Iteration Index (`i`) |
|---------|----------------------|
| First   | 0                    |
| Second  | 1                    |
| Third   | 2                    |
| ...     | ...                  |

### 1.2 Rationale
- Zero-based indexing aligns with Python's standard conventions
- The first attempt uses the base timeout without increment
- Maps naturally to `attempt_number - 1` from RetryState

### 1.3 Mapping from RetryState
```python
# RetryState.get_attempt_number() returns 1-indexed value
iteration_index = retry_state.get_attempt_number() - 1  # Convert to 0-indexed
```

---

## 2. Effective Timeout Formula

### 2.1 Core Formula
```
effective_timeout_ms = base_timeout_ms + (iteration_index * increment_ms)
```

### 2.2 With Maximum Cap
When `max_timeout_ms` is configured and > 0:
```
effective_timeout_ms = min(
    base_timeout_ms + (iteration_index * increment_ms),
    max_timeout_ms
)
```

### 2.3 Formula Components

| Component | Type | Description |
|-----------|------|-------------|
| `base_timeout_ms` | int | Starting timeout for the first attempt (iteration_index=0) |
| `increment_ms` | int | Additional time added per iteration |
| `iteration_index` | int | Zero-based iteration counter |
| `max_timeout_ms` | int \| None | Optional upper bound on effective timeout |
| `effective_timeout_ms` | int | Final computed timeout for the current iteration |

---

## 3. Configuration Keys and Defaults

### 3.1 Configuration Location
Timeout backoff settings are defined in **`.tf/ralph/config.json`** alongside existing Ralph configuration.

### 3.2 Configuration Schema
```json
{
  "timeoutBackoff": {
    "enabled": false,
    "baseTimeoutMs": 600000,
    "incrementMs": 150000,
    "maxTimeoutMs": null
  }
}
```

### 3.3 Configuration Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `timeoutBackoff.enabled` | bool | `false` | Whether timeout backoff is active |
| `timeoutBackoff.baseTimeoutMs` | int | `600000` | Base timeout in milliseconds (10 minutes) |
| `timeoutBackoff.incrementMs` | int | `150000` | Increment per iteration in milliseconds (2.5 minutes) |
| `timeoutBackoff.maxTimeoutMs` | int \| null | `null` | Maximum timeout cap (null = no cap) |

### 3.3.1 Validation Constraints

All configuration values **MUST** be validated on load. Invalid values **MUST** log an error and fall back to defaults.

| Constraint | Validation Rule | Error Behavior |
|------------|-----------------|----------------|
| `baseTimeoutMs` | Must be ≥ 0 | Log error, use default (600000) |
| `incrementMs` | Must be ≥ 0 | Log error, use default (150000) |
| `maxTimeoutMs` | Must be null or ≥ `baseTimeoutMs` | Log error, treat as null (no cap) |
| `enabled` | Must be boolean | Log error, use default (false) |

**Rationale**: Negative timeouts are nonsensical. Negative increment would decrease timeout over iterations (opposite of intent). A max less than base would always cap to an invalid value.

### 3.4 Default Values Rationale

- **`baseTimeoutMs: 600000`**: Matches existing Ralph default (`attemptTimeoutMs`)
- **`incrementMs: 150000`**: As specified in plan - 2.5 minutes per iteration provides meaningful additional time without excessive growth
- **`maxTimeoutMs: null`**: No cap by default to maintain backward compatibility; users must explicitly set a cap
- **`enabled: false`**: Opt-in feature to preserve existing behavior

### 3.5 Backward Compatibility

When `timeoutBackoff.enabled` is `false` (default):
- The existing `attemptTimeoutMs` configuration is used unchanged
- No backoff calculation is performed
- Behavior is identical to pre-backoff implementation

### 3.6 Configuration Loading and Error Handling

**Error Logging Requirement**: All configuration parsing errors **MUST** be logged at WARNING level or higher. Silently falling back to defaults without logging is **NOT** acceptable.

Example error log format:
```
[ralph] Invalid timeoutBackoff.baseTimeoutMs: -10000 (must be >= 0). Using default: 600000
[ralph] Invalid timeoutBackoff.maxTimeoutMs: 300000 (must be >= baseTimeoutMs: 600000). Disabling cap.
```

**Migration Path**: When loading config, if `timeoutBackoff` section is missing, treat as `enabled: false` and do not log an error (this is expected for existing configs).

---

## 4. Example Calculations

### 4.1 Default Configuration (enabled=true)
```python
base_timeout_ms = 600000      # 10 minutes
increment_ms = 150000         # 2.5 minutes
max_timeout_ms = null         # No cap

Attempt 1 (i=0): 600000 + (0 * 150000) = 600000 ms  (10 min)
Attempt 2 (i=1): 600000 + (1 * 150000) = 750000 ms  (12.5 min)
Attempt 3 (i=2): 600000 + (2 * 150000) = 900000 ms  (15 min)
Attempt 4 (i=3): 600000 + (3 * 150000) = 1050000 ms (17.5 min)
```

### 4.2 With Maximum Cap
```python
base_timeout_ms = 600000
increment_ms = 150000
max_timeout_ms = 1200000      # 20 minutes

Attempt 1 (i=0): min(600000,  1200000) = 600000 ms   (10 min)
Attempt 2 (i=1): min(750000,  1200000) = 750000 ms   (12.5 min)
Attempt 3 (i=2): min(900000,  1200000) = 900000 ms   (15 min)
Attempt 4 (i=3): min(1050000, 1200000) = 1050000 ms  (17.5 min)
Attempt 5 (i=4): min(1200000, 1200000) = 1200000 ms  (20 min, capped)
Attempt 6 (i=5): min(1350000, 1200000) = 1200000 ms  (20 min, capped)
```

### 4.3 Custom Configuration
```python
base_timeout_ms = 300000      # 5 minutes
increment_ms = 60000          # 1 minute
max_timeout_ms = 600000       # 10 minutes

Attempt 1 (i=0): 300000 ms  (5 min)
Attempt 2 (i=1): 360000 ms  (6 min)
Attempt 3 (i=2): 420000 ms  (7 min)
Attempt 4 (i=3): 480000 ms  (8 min)
Attempt 5 (i=4): 540000 ms  (9 min)
Attempt 6 (i=5): 600000 ms  (10 min, at cap)
Attempt 7 (i=6): 600000 ms  (10 min, capped)
```

---

## 5. Observability Requirements

### 5.1 Log Format
When timeout backoff is enabled, each attempt must log:
```
[ralph] Timeout backoff: base={base}ms increment={inc}ms iteration={i} effective={eff}ms capped={true|false}
```

### 5.2 Example Log Output
```
[ralph] Timeout backoff: base=600000ms increment=150000ms iteration=0 effective=600000ms capped=false
[ralph] Timeout backoff: base=600000ms increment=150000ms iteration=1 effective=750000ms capped=false
[ralph] Timeout backoff: base=600000ms increment=150000ms iteration=2 effective=900000ms capped=false
[ralph] Timeout backoff: base=600000ms increment=150000ms iteration=3 effective=1050000ms capped=false
```

### 5.3 Structured Logging Fields
For machine parsing, include these fields:
- `timeout_backoff_base_ms`
- `timeout_backoff_increment_ms`
- `timeout_backoff_iteration_index`
- `timeout_backoff_effective_ms`
- `timeout_backoff_capped`

---

## 6. Implementation Notes for pt-bcu8

### 6.1 Suggested Function Signature

```python
def calculate_effective_timeout(
    attempt_number: int,  # 1-indexed from RetryState
    base_timeout_ms: int = 600000,
    increment_ms: int = 150000,
    max_timeout_ms: int | None = None,
) -> int:
    """Calculate effective timeout with linear backoff.
    
    Args:
        attempt_number: 1-indexed attempt number (from RetryState).
                       Must be >= 1. Values < 1 raise ValueError.
        base_timeout_ms: Base timeout for first attempt. Must be >= 0.
        increment_ms: Additional time per iteration. Must be >= 0.
        max_timeout_ms: Optional maximum timeout cap. If set, must be >= base_timeout_ms.
    
    Returns:
        Effective timeout in milliseconds for this attempt
    
    Raises:
        ValueError: If attempt_number < 1, or if any timeout value is negative,
                   or if max_timeout_ms < base_timeout_ms.
    
    Example:
        >>> # RetryState returns 1-indexed attempt number
        >>> attempt = retry_state.get_attempt_number()  # Returns 1, 2, 3...
        >>> effective = calculate_effective_timeout(attempt, 600000, 150000, 1200000)
        >>> # Attempt 1: 600000ms, Attempt 2: 750000ms, etc.
    """
    # Input validation
    if attempt_number < 1:
        raise ValueError(f"attempt_number must be >= 1, got {attempt_number}")
    if base_timeout_ms < 0:
        raise ValueError(f"base_timeout_ms must be >= 0, got {base_timeout_ms}")
    if increment_ms < 0:
        raise ValueError(f"increment_ms must be >= 0, got {increment_ms}")
    if max_timeout_ms is not None and max_timeout_ms < base_timeout_ms:
        raise ValueError(
            f"max_timeout_ms ({max_timeout_ms}) must be >= base_timeout_ms ({base_timeout_ms})"
        )
    
    iteration_index = attempt_number - 1  # Convert to 0-indexed
    effective = base_timeout_ms + (iteration_index * increment_ms)
    
    if max_timeout_ms is not None and max_timeout_ms > 0:
        effective = min(effective, max_timeout_ms)
    
    return effective
```

### 6.1.1 Integer Overflow Considerations

Python integers have arbitrary precision, so overflow is not a concern in the traditional sense. However, extremely large iteration counts could produce effectively infinite timeouts.

**Recommended Safeguards**:
1. **Practical upper bound**: Document that iteration counts beyond 1000 produce diminishing returns and may indicate a systemic issue
2. **maxTimeoutMs as circuit breaker**: Even without an explicit cap, consider a hard internal limit of 1 hour (3600000 ms) unless user specifies otherwise
3. **Warning log**: Log a warning when effective timeout exceeds 1 hour:
   ```
   [ralph] Warning: Effective timeout {effective}ms exceeds 1 hour. Consider reviewing max iterations.
   ```

### 6.2 Integration Points
1. **Config loading**: Extend `load_config()` in `tf/ralph.py` to read `timeoutBackoff` section
2. **Timeout resolution**: Update `resolve_attempt_timeout_ms()` to apply backoff when enabled
3. **Logging**: Add backoff details to attempt start logging

### 6.3 Environment Variable Override
Support these environment variables for CI/CD flexibility:
- `RALPH_TIMEOUT_BACKOFF_ENABLED`
- `RALPH_TIMEOUT_BACKOFF_BASE_MS`
- `RALPH_TIMEOUT_BACKOFF_INCREMENT_MS`
- `RALPH_TIMEOUT_BACKOFF_MAX_MS`

#### 6.3.1 Environment Variable Validation

Environment variables follow the same priority as existing Ralph settings (env var > config > default). **Invalid env values must log a WARNING and fall back to the next priority level** (config value or default).

**Validation Rules** (same as config):
- `RALPH_TIMEOUT_BACKOFF_ENABLED`: Must be "true", "false", "1", or "0" (case-insensitive). Invalid values log warning and use config/default.
- `RALPH_TIMEOUT_BACKOFF_BASE_MS`: Must be a non-negative integer. Invalid values log warning and use config/default.
- `RALPH_TIMEOUT_BACKOFF_INCREMENT_MS`: Must be a non-negative integer. Invalid values log warning and use config/default.
- `RALPH_TIMEOUT_BACKOFF_MAX_MS`: Must be a positive integer or empty/unset. Invalid values log warning and use config/default.

**Example Error Log**:
```
[ralph] Warning: Invalid RALPH_TIMEOUT_BACKOFF_BASE_MS='ten_minutes'. Using config value: 600000
```

---

## 7. Test Requirements

### 7.1 Unit Tests
1. Base timeout returned for iteration_index=0
2. Correct increment applied for iterations 1-5
3. Cap enforced when effective exceeds max
4. No cap applied when max is null
5. No cap applied when max is 0
6. Correct conversion from 1-indexed attempt_number

#### 7.1.1 Edge Case Tests (Required)
7. **Negative attempt_number**: Verify ValueError raised for attempt_number=0 and negative values
8. **Negative base_timeout_ms**: Verify ValueError raised
9. **Negative increment_ms**: Verify ValueError raised
10. **max_timeout_ms < base_timeout_ms**: Verify ValueError raised
11. **max_timeout_ms == base_timeout_ms**: Verify cap applied immediately from attempt 2
12. **Very large iteration numbers**: Verify no overflow (Python arbitrary precision) but warning logged
13. **Zero increment_ms**: Verify constant timeout across all iterations
14. **Zero base_timeout_ms**: Verify timeout starts at 0 and grows by increment

### 7.2 Integration Tests
1. Config loading with backoff enabled
2. Config loading with backoff disabled (backward compat)
3. Environment variable overrides
4. Log output verification
5. **Invalid config values log errors**: Verify WARNING logs when config contains negative values
6. **Missing timeoutBackoff section**: No error logged (backward compat for existing configs)

---

## 8. Spec Coverage Checklist

| Plan Requirement | Spec Section | Status |
|-----------------|--------------|--------|
| Iteration index semantics | Section 1 | ✓ Defined (0-indexed) |
| Effective timeout formula | Section 2 | ✓ Defined with cap support |
| Config keys and defaults | Section 3 | ✓ Defined with rationale |
| Observability | Section 5 | ✓ Log format specified |
| Backward compatibility | Section 3.5 | ✓ Documented |
| Test guidance | Section 7 | ✓ Requirements listed |

---

## Decision

**Acceptance Criteria Status**:
- [x] Iteration index semantics are explicit (starts at 0)
- [x] Effective timeout formula is documented (including optional max cap)
- [x] Config keys and defaults are defined (base, increment=150000, max cap)

This specification is ready for implementation in **pt-bcu8**.
