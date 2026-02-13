---
description: Fix phase for TF workflow [tf-fix]
model: zai/glm-5
thinking: high
skill: tf-fix
---

# /tf-fix

Execute the Fix phase for TF workflow ticket implementation.

## Input
- Ticket ID: `$1`
- Args: `$@`

## Execution

Follow the **tf-fix** skill procedure to:

1. Load context (review.md, implementation.md)
2. Check if fixer enabled
3. Analyze issues by severity (Critical/Major/Minor/Warnings/Suggestions)
4. Apply fixes (Critical required, Major recommended, Minor if low effort)
5. Re-run tests
6. Write `{artifactDir}/fixes.md`

## Usage

```
/tf-fix <ticket-id>
```

## Output

- `{artifactDir}/fixes.md` - Fixes applied with statistics
