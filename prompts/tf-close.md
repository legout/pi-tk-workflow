---
description: Close phase for TF workflow [tf-close]
model: chutes/zai-org/GLM-4.7-Flash
thinking: medium
skill: tf-close
---

# /tf-close

Execute the Close phase for TF workflow ticket implementation.

## Input
- Ticket ID: `$1`
- Args: `$@`

## Execution

Follow the **tf-close** skill procedure to:

1. Load context (all phase artifacts)
2. Quality gate check (parse severity counts)
3. Handle BLOCKED status (if quality gate fails)
4. Update retry state (if enabled)
5. Commit changes (ticket artifacts + changed files)
6. Add note via `tk add-note`
7. Close ticket via `tk close`
8. Write `{artifactDir}/close-summary.md`

## Usage

```
/tf-close <ticket-id>
```

## Output

- `{artifactDir}/close-summary.md` - Final summary with status
- `{artifactDir}/chain-summary.md` - Artifact index
- `{artifactDir}/retry-state.json` - Retry state (if enabled)
