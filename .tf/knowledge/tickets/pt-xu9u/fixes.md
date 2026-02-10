# Fixes: pt-xu9u

## Summary
Addressed all Critical and Major issues identified in the review.

## Critical Fixes Applied

### 1. Attempt Numbering Consistency (FIXED)
**Issue**: Off-by-one error in attempt numbering causing second attempts to be labeled as 3.

**Fix**: 
- Standardized on `attemptNumber` (1-indexed) throughout
- Fresh attempt: `attemptNumber = 1`, `retryCount = 0`
- Retry attempt: `attemptNumber = len(attempts) + 1`, `retryCount = previous_retryCount + 1`
- Escalation curve based on `attemptNumber` directly:
  - Attempt 1: Base models
  - Attempt 2: Escalated fixer
  - Attempt 3+: Escalated fixer + reviewer-second-opinion + worker (if configured)

### 2. Config Schema Example (FIXED)
**Issue**: Example showed `{ "escalation": { ... } }` at root instead of under `workflow`.

**Fix**: Updated all config examples to show proper nested structure:
```json
{
  "workflow": {
    "escalation": {
      "enabled": false,
      "maxRetries": 3,
      "models": { ... }
    }
  }
}
```

### 3. Detection Algorithm - Missing has_items Fallback (FIXED)
**Issue**: review.md detection only extracted summary statistics, missing fallback when stats absent.

**Fix**: Added complete detection logic:
```python
# Find section boundaries
section_start = section_match.end()
next_header = re.search(r'\n^##\s', content[section_start:], re.MULTILINE)
section_end = section_start + next_header.start() if next_header else len(content)
section = content[section_start:section_end]

# Check if section has bullet items (fallback indicator)
has_items = bool(re.search(r'\n-\s', section))

# Extract count from summary stats (fallback to 1 if items exist but no count)
if stat_match:
    count = int(stat_match.group(1))
else:
    count = 1 if has_items else 0
```

### 4. Ralph Skip Logic for maxRetries (FIXED)
**Issue**: No mechanism to skip tickets that exceeded max retries.

**Fix**: Added to Ralph Integration section:
- Check `{artifactDir}/retry-state.json` for `status: blocked` and `retryCount >= maxRetries`
- If exceeded: Skip ticket with log message
- Also skip if `parallelWorkers > 1` without locking

### 5. Parallel Worker Safety (FIXED)
**Issue**: Only documented assumption without enforcement.

**Fix**: Added explicit skip logic:
```
Also skip if `parallelWorkers > 1` and no locking mechanism is implemented (log warning)
```

### 6. qualityGate.counts Population in BLOCKED Case (FIXED)
**Issue**: Attempt entry didn't show extraction of counts for BLOCKED case.

**Fix**: 
- Parse severity counts from review.md using detection algorithm
- Store in `blocked_counts` when BLOCKED, `severity_counts` when CLOSED
- Populated in attempt entry: `"counts": {blocked_counts if closeStatus == BLOCKED else severity_counts}`

## Major Fixes Applied

### 7. Base Model Resolution Ambiguity (FIXED)
**Issue**: Agent keys (kebab-case) vs escalation fields (camelCase) mapping unclear.

**Fix**: 
- Added explicit mapping note: `reviewer-second-opinion` (agent) → `reviewerSecondOpinion` (escalation field)
- Clarified resolution order in escalation table

### 8. maxRetries Semantics (FIXED)
**Issue**: Unclear if maxRetries means "max total attempts" or "max BLOCKED attempts".

**Fix**: 
- Defined as "max BLOCKED attempts before giving up"
- Comparison: `if retryCount >= maxRetries: Log warning`

### 9. Successful Close Detection (FIXED)
**Issue**: Described in prose without algorithmic clarity.

**Fix**: Detection algorithm is now fully specified with regex patterns and status normalization.

### 10. Schema Validation (FIXED)
**Issue**: Only validated schema version, not required fields.

**Fix**: 
- Added validation for required fields: version, ticketId, attempts, lastAttemptAt, status
- Added corrupted state handling: backup + reset

### 11. Atomic Write for retry-state.json (FIXED)
**Issue**: Direct write without atomic replace.

**Fix**: 
```python
temp_path = f"{retry_state_path}.tmp"
with open(temp_path, 'w') as f:
    json.dump(state, f, indent=2)
os.replace(temp_path, retry_state_path)  # Atomic rename
```

## Files Modified
- `skills/tf-workflow/SKILL.md` - All fixes applied
- `.pi/skills/tf-workflow/SKILL.md` - Synced
