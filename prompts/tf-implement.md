---
description: Implementation phase for TF workflow [tf-implement]
model: minimax/MiniMax-M2.5
thinking: high
skill: tf-implement
---

# /tf-implement

Execute the Implementation phase for TF workflow ticket implementation.

## Input
- Ticket ID: `$1`
- Args: `$@`

## Execution

Follow the **tf-implement** skill procedure to:

1. Load context (research.md, ticket details, retry state)
2. Explore codebase
3. Implement changes
4. Run quality checks (lint, format, typecheck)
5. Run tests
6. Write `{artifactDir}/implementation.md`
7. Track changed files

## Usage

```
/tf-implement <ticket-id>
```

## Output

- `{artifactDir}/implementation.md` - Implementation summary
- `{artifactDir}/files_changed.txt` - Tracked changed files
